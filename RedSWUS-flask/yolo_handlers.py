import os
import torch
import cv2
from flask import Flask, request, jsonify
from models import db, YoloResult

# YOLO 핸들러 클래스
class YOLOApp:
    def __init__(self):
        self.custom_weights = './pt/yolo.pt'  # 로컬 YOLOv9 가중치 경로

    def detect_video(self, video_path, output_path, stride=6, img_size=640, conf=0.5):
        try:
            os.system(f"python3 ./yolov9/detect.py --weights {self.custom_weights} --vid-stride {stride} \
                        --img {img_size} --conf {conf} --exist-ok --source {video_path} --save-crop --project {output_path}")
        except Exception as e:
            print(f"비디오 처리 중 오류 발생: {e}")

# YOLOAPP 인스턴스 생성
yolo_app = YOLOApp()

def handle_yolo_predict(video_id):
    torch.cuda.empty_cache()

    if 'file' not in request.files:
        return jsonify({"message": "No file part in the request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "No file selected for uploading"}), 400

    file_path = os.path.join("./uploaded_videos", file.filename)

    if file.filename.endswith(('.mp4', '.avi', '.mkv', '.mov', '.wmv')):
        try:
            # YOLO 탐지 수행
            output_path = "./mp4_to_img"
            yolo_app.detect_video(file_path, output_path)

            # YOLO 결과 디렉토리
            result_image_path = os.path.join(output_path, "exp", "crops", "glasses")
            no_padding_dir = os.path.join(result_image_path, "no_padding")
            os.makedirs(no_padding_dir, exist_ok=True)

            for filename in os.listdir(result_image_path):
                if filename.endswith(('.jpg', '.jpeg', '.png')):
                    image_path = os.path.join(result_image_path, filename)
                    image = cv2.imread(image_path)
                    if image is None:
                        raise FileNotFoundError(f"이미지를 찾을 수 없음: {image_path}")

                    # RGB → BGR 변환 후 저장 (패딩 없이)
                    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    output_image_path = os.path.join(no_padding_dir, filename)
                    cv2.imwrite(output_image_path, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))

            # DB에 결과 저장
            detection_result = YoloResult(
                video_code=video_id,
                yolo_result_path=no_padding_dir
            )
            db.session.add(detection_result)
            db.session.commit()

            return jsonify({
                "message": "Image processed successfully (no padding)",
                "yolo_result_code": detection_result.yolo_result_code,
                "output_image": no_padding_dir
            }), 200
        except Exception as e:
            return jsonify({"message": f"Error during processing: {str(e)}"}), 500
    else:
        return jsonify({"message": "Unsupported file format. Only MP4, AVI, MKV, MOV, WMV are supported."}), 400

def handle_yolo_predict_return_frames(video_id):
    no_padding_dir = os.path.join('./mp4_to_img', 'exp', 'crops', 'glasses', 'no_padding')
    if not os.path.exists(no_padding_dir):
        raise FileNotFoundError(f"YOLO 출력 디렉토리가 존재하지 않음: {no_padding_dir}")

    # 프레임 경로 수집
    frame_paths = sorted([
        os.path.join(no_padding_dir, f)
        for f in os.listdir(no_padding_dir)
        if f.lower().endswith(('.jpg', '.jpeg', '.png'))
    ])

    if not frame_paths:
        raise FileNotFoundError("YOLO 출력 디렉토리 내에 유효한 이미지가 없습니다.")

    return frame_paths
