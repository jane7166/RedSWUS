from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os
import torch
import cv2

# Flask 앱 초기화
app = Flask(__name__)
CORS(app)

# 데이터베이스 설정
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///detections.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 데이터베이스 초기화
db = SQLAlchemy(app)

# 데이터베이스 모델 불러오기
from models import DetectionResult

# 데이터베이스 테이블 생성
with app.app_context():
    db.create_all()

# YOLOv9 모델 경로 설정
yolov9_local_path = os.path.abspath('./yolov9')
custom_weights = './pt/best.pt'

# YOLOv9 모델 로드
try:
    model_yolo = torch.hub.load(yolov9_local_path, 'custom', path=custom_weights, source='local')
    print("YOLOv9 모델이 성공적으로 로드되었습니다.")
except Exception as e:
    print(f"YOLOv9 모델 로드 중 오류 발생: {e}")
    exit(1)

# 파일 업로드 처리
@app.route('/upload_file/yolo', methods=['POST'])
def upload_file_yolo():
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
        # YOLOv9 모델 처리
        img = cv2.imread(file_path)
        if img is None:
            return jsonify({"message": "Error: Could not read image."}), 500

        # YOLOv9 감지 수행
        results = model_yolo(img)
        results.render()

        # 처리된 이미지 저장
        result_image_path = os.path.join('./detect', f"output_{file.filename}")
        cv2.imwrite(result_image_path, img)

        # 데이터베이스에 저장
        detection = DetectionResult(
            file_name=file.filename,
            output_image_path=result_image_path,
            model_name="YOLOv9"
        )
        db.session.add(detection)
        db.session.commit()

        return jsonify({"message": "Image processed successfully", "output_image": result_image_path}), 200

    else:
        return jsonify({"message": "Unsupported file format. Only JPG, PNG are supported."}), 400

# 다른 모델의 API 추가
@app.route('/upload_file/another_model', methods=['POST'])
def upload_file_another_model():
    if 'file' not in request.files:
        return jsonify({"message": "No file part in the request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "No file selected for uploading"}), 400

    # 파일 저장 경로 설정
    file_path = os.path.join("./detect", file.filename)
    file.save(file_path)

    # 다른 모델 처리 예시 (로직은 모델에 따라 변경)
    processed_image_path = os.path.join('./detect', f"processed_{file.filename}")
    # 예를 들어, 여기에서 다른 모델 처리 로직을 추가하세요
    # processed_image = another_model.process(file_path)
    # cv2.imwrite(processed_image_path, processed_image)

    # 처리된 파일을 데이터베이스에 저장
    detection = DetectionResult(
        file_name=file.filename,
        output_image_path=processed_image_path,
        model_name="AnotherModel"
    )
    db.session.add(detection)
    db.session.commit()

    return jsonify({"message": "Image processed successfully by AnotherModel", "output_image": processed_image_path}), 200

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
