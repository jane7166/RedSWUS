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
from yolo_handlers import handle_yolo_predict
from firstPrepro_handlers import handle_firstPrepro
from secondPrepro_handlers import handle_secondPrepro
from str_handlers import handle_str_predict

warnings.filterwarnings("ignore", category=FutureWarning, module="torch")

# app 인스턴스는 최상단에서 정의
app = Flask(__name__)
CORS(app)

# DB 설정 및 초기화
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'video_analysis.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# thread-local 모델 캐시
thread_local = threading.local()

def get_handler():
    if not hasattr(thread_local, "handler"):
        print("[INFO] Thread 최초 모델 로딩 중...")
        thread_local.handler = DetectronHandler()
        print("[INFO] 모델 로딩 완료")
    return thread_local.handler

def worker_std_handler(flask_app, code):
    with flask_app.app_context():
        handler = get_handler()
        return handler.handle_std_predict(code)

@app.route('/full_pipeline', methods=['POST'])
def full_pipeline():
    try:
        upload_response = handle_upload_video()
        if upload_response[1] != 200:
            return jsonify(upload_response[0]), upload_response[1]
        video_id = upload_response[0].get("video_id")

        yolo_response = handle_yolo_predict(video_id=video_id)
        if yolo_response[1] != 200:
            return jsonify(yolo_response[0]), yolo_response[1]
        yolo_result_code = yolo_response[0].get_json().get("yolo_result_code")

        first_prepro_response = handle_firstPrepro(yolo_result_code=yolo_result_code)
        if first_prepro_response[1] != 200:
            return jsonify(first_prepro_response[0]), first_prepro_response[1]
        first_result_list = first_prepro_response[0].get("first_code_list")

        std_result_code = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(worker_std_handler, app, code) for code in first_result_list]
            for future in as_completed(futures):
                response = future.result()
                if response == 0 or response[1] != 200:
                    continue
                result = response[0]
                for path in result["cropped_paths"]:
                    std_result = StdResult(
                        video_code=result["video_code"],
                        first_result_code=result["first_result_code"],
                        std_result_path=path
                    )
                    db.session.add(std_result)
                    db.session.flush()
                    std_result_code.append(std_result.std_result_code)
        db.session.commit()

        if not std_result_code:
            return jsonify({"error": "No valid STD results"}), 400

        second_prepro_response = handle_secondPrepro(std_result_codes=std_result_code)
        if second_prepro_response[1] != 200:
            return jsonify(second_prepro_response[0]), second_prepro_response[1]
        second_result_code = second_prepro_response[0].get("second_result_list")

        str_response = handle_str_predict(second_code_list=second_result_code)
        if str_response[1] != 200:
            return jsonify(str_response[0]), str_response[1]

        return jsonify({
            "status": "success",
            "message": "Full pipeline completed successfully.",
            "str_result": str_response[0].get("result")
        }), 200

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
    app.run(host='0.0.0.0', port=5000)
