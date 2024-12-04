import os
import torch
import cv2
from flask import Flask, request, jsonify
from models import db, DetectionResult

# YOLO 핸들러 클래스
class YOLOApp:
    def __init__(self):
        self.custom_weights = './pt/best.pt'  # 로컬 YOLOv9 가중치 경로

    def detect_video(self, video_path, output_path, stride=5, img_size=640, conf=0.5):
        # 비디오 파일 처리
        try:
            os.system(f"python ./yolov9detect.py --weights {self.custom_weights} --vid-stride {stride} \
                        --img {img_size} --conf {conf} --exist-ok --source {video_path} --save-crop --project {output_path}")
            print(f"비디오 파일 {video_path} 처리가 완료되었습니다.")
        except Exception as e:
            print(f"비디오 처리 중 오류 발생: {e}")

# YOLOAPP 인스턴스 생성
yolo_app = YOLOApp()

@app.route('/predict', methods=['POST'])
def handle_yolo_predict():
    if 'file' not in request.files:
        return jsonify({"message": "No file part in the request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "No file selected for uploading"}), 400

    # 파일 저장 경로 설정
    file_path = os.path.join("./detect", file.filename)
    file.save(file_path)

    # 파일 처리
    if file.filename.endswith(('.jpg', '.jpeg', '.png')):
        return jsonify({"message": "Image processing is currently unsupported."}), 400

    elif file.filename.endswith(('.mp4', '.avi', '.mov', '.mkv')):
        try:
            output_path = os.path.join('./detect', f"output_{os.path.splitext(file.filename)[0]}")
            os.makedirs(output_path, exist_ok=True)

            # YOLOv9 모델을 사용하여 비디오 처리
            yolo_app.detect_video(file_path, output_path)

            return jsonify({"message": "Video processed successfully", "output_folder": output_path}), 200
        except Exception as e:
            return jsonify({"message": f"Error during video processing: {str(e)}"}), 500

    else:
        return jsonify({"message": "Unsupported file format. Only MP4, AVI, MOV, MKV are supported."}), 400
