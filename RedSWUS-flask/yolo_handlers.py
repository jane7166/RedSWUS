import os
import torch
import cv2
from flask import request, jsonify
from models import db, DetectionResult

# YOLO 핸들러 클래스
class YOLOApp:
    def __init__(self):
        self.custom_weights = './pt/best.pt'  # 로컬 YOLOv9 가중치 경로
        self.model = self._load_model()

    def _load_model(self):
        # YOLOv9 모델 로드
        try:
            model_yolo = torch.hub.load(os.path.abspath('./yolov9'), 'custom', path=self.custom_weights, source='local')
            print("YOLOv9 모델이 성공적으로 로드되었습니다.")
            return model_yolo
        except Exception as e:
            print(f"YOLOv9 모델 로드 중 오류 발생: {e}")
            exit(1)

    def detect_objects(self, img_path):
        # 이미지 열기
        img = cv2.imread(img_path)
        if img is None:
            raise ValueError("Error: Could not read image.")

        # YOLOv9 감지 수행
        results = self.model(img)
        results.render()  # 감지된 결과를 이미지에 렌더링

        return results.imgs[0]  # 처리된 이미지 반환

# YOLOAPP 인스턴스 생성
yolo_app = YOLOApp()

# 핸들러 함수
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
