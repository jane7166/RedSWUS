import os
import time
import traceback
import threading
import warnings
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from sqlalchemy import inspect
from concurrent.futures import ThreadPoolExecutor, as_completed
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from models import db, StdResult
from std_handlers import DetectronHandler
from video_handlers import handle_upload_video
from yolo_handlers import handle_yolo_predict, handle_yolo_predict_return_frames
from firstPrepro_handlers import handle_firstPrepro_single
from str_handlers import handle_str_predict

warnings.filterwarnings("ignore", category=FutureWarning, module="torch")

app = Flask(__name__)
CORS(app)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'video_analysis.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# 폴더 감시 핸들러
class NewImageHandler(FileSystemEventHandler):
    def __init__(self, flask_app, video_code, yolo_result_code_getter):
        self.flask_app = flask_app
        self.video_code = video_code
        self.yolo_result_code_getter = yolo_result_code_getter

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(('.jpg', '.jpeg', '.png')):
            try:
                yolo_result_code = self.yolo_result_code_getter()
                full_pipeline_per_frame(self.flask_app, event.src_path, self.video_code, yolo_result_code)
            except Exception as e:
                print(f"[WATCHDOG] full_pipeline_per_frame 실패: {str(e)}")

def start_watch_folder(folder_path, flask_app, video_code, yolo_result_code_getter):
    event_handler = NewImageHandler(flask_app, video_code, yolo_result_code_getter)
    observer = Observer()
    observer.schedule(event_handler, path=folder_path, recursive=False)
    observer.start()
    return observer

thread_local = threading.local()

def get_handler():
    if not hasattr(thread_local, "handler"):
        thread_local.handler = DetectronHandler()
    return thread_local.handler

def full_pipeline_per_frame(flask_app, frame_path, video_code, yolo_result_code):
    with flask_app.app_context():
        try:
            first_code = handle_firstPrepro_single(frame_path, video_code, yolo_result_code)
            if not first_code:
                return None

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

            str_response, status_code = handle_str_predict(std_result_codes=std_codes)

            if status_code != 200:
                return None
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

        frame_folder = './mp4_to_img/exp/crops/glasses/padded'
        
        # (1) 폴더 비우기
        if os.path.exists(frame_folder):
            for f in os.listdir(frame_folder):
                os.remove(os.path.join(frame_folder, f))
        
        # (2) yolo_result_code를 나중에 가져올 수 있게 만들자
        yolo_result_code_holder = {"code": None}
        def get_yolo_result_code():
            return yolo_result_code_holder["code"]

        # (3) 폴더 감시 시작
        observer_executor = ThreadPoolExecutor(max_workers=1)
        observer_executor.submit(start_watch_folder, frame_folder, app, video_id, get_yolo_result_code)

        # (4) YOLO detect 실행
        yolo_response = handle_yolo_predict(video_id=video_id)
        if yolo_response[1] != 200:
            return yolo_response
        yolo_result_code_holder["code"] = yolo_response[0].get_json().get("yolo_result_code")

        # (5) YOLO detect 끝나고 기존 프레임들은 바로 병렬 처리
        frame_paths = handle_yolo_predict_return_frames(video_id=video_id)
        if not frame_paths:
            return jsonify({"error": "YOLO 처리 실패"}), 400

        results = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(full_pipeline_per_frame, app, path, video_id, yolo_result_code_holder["code"])
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
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": f"An error occurred during full pipeline execution: {str(e)}"
        }), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5001)
