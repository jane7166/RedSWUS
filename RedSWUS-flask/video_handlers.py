# video_handlers.py
from flask import request
from models import db, Video
from datetime import datetime
import os

# Video 업로드 관련 클래스
class VideoAPP:
    def __init__(self, upload_folder):
        self.upload_folder = upload_folder
        os.makedirs(self.upload_folder, exist_ok=True)

    def upload_video(self):
        # 프론트에서 업로드된 비디오를 처리하고 데이터베이스에 저장
        file = request.files.get('file')
        if not file:
            return {"status": "error", "message": "No file provided"}, 400

        filename = file.filename
        file_path = os.path.join(self.upload_folder, filename)

        try:
            file.save(file_path)

            # 데이터베이스에 비디오 정보 저장
            video = Video(video_path=file_path, upload_time=datetime.utcnow())
            db.session.add(video)
            db.session.commit()

            return {
                "status": "success",
                "message": "Video uploaded successfully.",
                "video_id": video.video_code,
                "file_path": video.video_path
            }, 200

        except Exception as e:
            return {"status": "error", "message": f"An error occurred: {str(e)}"}, 500

# VideoAPP 인스턴스 생성

video_app = VideoAPP(upload_folder="uploaded_videos")

# 핸들러 함수
def handle_upload_video():
    return video_app.upload_video()