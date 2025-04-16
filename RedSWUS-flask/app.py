import os
import time
import traceback
import threading
import warnings
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from sqlalchemy import inspect
from concurrent.futures import ThreadPoolExecutor, as_completed

from models import db, StdResult
from std_handlers import DetectronHandler
from video_handlers import handle_upload_video
from yolo_handlers import handle_yolo_predict, handle_yolo_predict_return_frames
from firstPrepro_handlers import handle_firstPrepro_single
from secondPrepro_handlers import handle_secondPrepro
from str_handlers import handle_str_predict

warnings.filterwarnings("ignore", category=FutureWarning, module="torch")

app = Flask(__name__)
CORS(app)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'video_analysis.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

thread_local = threading.local()

def get_handler():
    if not hasattr(thread_local, "handler"):
        print("[INFO] Thread 최초 모델 로딩 중...")
        thread_local.handler = DetectronHandler()
        print("[INFO] 모델 로딩 완료")
    return thread_local.handler

def full_pipeline_per_frame(flask_app, frame_path, video_code, yolo_result_code):
    with flask_app.app_context():
        try:
            print(f"[DEBUG] 전달된 yolo_result_code: {yolo_result_code}")
            # 1. First Preprocessing
            first_code = handle_firstPrepro_single(frame_path, video_code, yolo_result_code)
            if not first_code:
                return None

            # 2. STD
            handler = get_handler()
            std_result = handler.handle_std_predict(first_code)
            if std_result == 0 or std_result[1] != 200:
                return None

            std_codes = []
            for path in std_result[0]["cropped_paths"]:
                std = StdResult(
                    video_code=std_result[0]["video_code"],
                    first_result_code=first_code,
                    std_result_path=path
                )
                db.session.add(std)
                db.session.flush()
                std_codes.append(std.std_result_code)
            db.session.commit()

            # 3. Second Preprocessing
            second_response = handle_secondPrepro(std_result_codes=std_codes)
            if second_response[1] != 200:
                return None
            second_codes = second_response[0].get("second_result_list")

            # 4. STR
            str_response = handle_str_predict(second_code_list=second_codes)
            return str_response

        except Exception:
            traceback.print_exc()
            return None

@app.route('/full_pipeline', methods=['POST'])
def full_pipeline():
    try:
        upload_response = handle_upload_video()
        if upload_response[1] != 200:
            return upload_response
        video_id = upload_response[0].get("video_id")

        # YOLO 실행 및 결과 코드 획득
        yolo_response = handle_yolo_predict(video_id=video_id)
        if yolo_response[1] != 200:
            return yolo_response
        yolo_result_code = yolo_response[0].get_json().get("yolo_result_code")
        print(f"[DEBUG] 받은 yolo_result_code: {yolo_result_code}")

        # YOLO 탐지 결과로부터 프레임 경로 획득
        frame_paths = handle_yolo_predict_return_frames(video_id=video_id)
        if not frame_paths:
            return jsonify({"error": "YOLO 처리 실패"}), 400

        results = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(full_pipeline_per_frame, app, path, video_id, yolo_result_code)
                for path in frame_paths
            ]
            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)

        if not results:
            return jsonify({"error": "모든 파이프라인 처리 실패"}), 400

        return jsonify({"status": "success", "results": results}), 200

    except Exception as e:
        print("[ERROR] Full pipeline 예외 발생:")
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": f"An error occurred during full pipeline execution: {str(e)}"
        }), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("테이블 목록:", inspect(db.engine).get_table_names())
    app.run(host='0.0.0.0', port=5001)