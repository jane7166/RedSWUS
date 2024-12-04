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
            os.system(f"python ./yolov9/detect.py --weights {self.custom_weights} --vid-stride {stride} \
                        --img {img_size} --conf {conf} --exist-ok --source {video_path} --save-crop --project {output_path}")
            print(f"비디오 파일 {video_path} 처리가 완료되었습니다.")
        except Exception as e:
            print(f"비디오 처리 중 오류 발생: {e}")

# YOLOAPP 인스턴스 생성
yolo_app = YOLOApp()

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
        try:
            # YOLOv9 모델을 사용하여 이미지 처리
            processed_image = yolo_app.detect_objects(file_path)

            # 처리된 이미지 저장
            result_image_path = os.path.join('./detect', f"output_{file.filename}")
            cv2.imwrite(result_image_path, processed_image)

            # 데이터베이스에 결과 저장
            detection_result = DetectionResult(
                file_name=file.filename,
                output_image_path=result_image_path,
                model_name="YOLOv9"
            )
            db.session.add(detection_result)
            db.session.commit()

            return jsonify({"message": "Image processed successfully", "output_image": result_image_path}), 200
        except Exception as e:
            return jsonify({"message": f"Error during processing: {str(e)}"}), 500
    else:
        return jsonify({"message": "Unsupported file format. Only JPG, PNG are supported."}), 400