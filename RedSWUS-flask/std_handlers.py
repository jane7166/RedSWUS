import os
import torch
import cv2
import numpy as np
import glob
import tempfile
import time
from flask import Flask, request, jsonify, send_file
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from model_detection import setup_cfg, get_parser, VisualizationDemo, save_result_to_txt

# Flask 앱 초기화
app = Flask(__name__)

# Detectron2 설정 및 모델 불러오기
cfg = get_cfg()
cfg.merge_from_file("./config.yaml")  # YAML 파일 경로 설정
cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5  # 예측 점수 임계값 설정
cfg.MODEL.WEIGHTS = "./model_0000599.pth"  # 모델 가중치 파일 경로 설정
cfg.MODEL.DEVICE = "cuda" if torch.cuda.is_available() else "cpu"  # GPU 사용 가능하면 GPU 사용

predictor = DefaultPredictor(cfg)

@app.route('/detect_visual', methods=['POST'])
def detect_objects_visual():
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400

    try:
        # 이미지 읽기
        file = request.files['image']
        np_img = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

        # 이미지가 정상적으로 로드되지 않을 경우 에러 반환
        if img is None:
            return jsonify({"error": "Failed to load image"}), 400

        # Detectron2를 사용한 객체 탐지 수행
        outputs = predictor(img)

        # 탐지된 객체의 정보 가져오기
        instances = outputs["instances"].to("cpu")
        boxes = instances.pred_boxes.tensor.numpy()
        classes = instances.pred_classes.numpy()
        scores = instances.scores.numpy()

        # 탐지된 객체 박스 및 정보 이미지에 표시
        for box, cls, score in zip(boxes, classes, scores):
            x1, y1, x2, y2 = box
            cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            label = f"Class: {cls}, Score: {score:.2f}"
            cv2.putText(img, label, (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # 처리된 이미지를 임시 파일로 저장
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        temp_filename = temp_file.name
        cv2.imwrite(temp_filename, img)

        # 클라이언트에게 이미지 파일 전송
        return send_file(temp_filename, mimetype='image/jpeg')

    except Exception as e:
        # 예외 발생 시 에러 메시지 반환
        return jsonify({"error": str(e)}), 500

@app.route('/batch_process', methods=['POST'])
def batch_process():
    try:
        # 입력 경로와 출력 경로 가져오기
        input_dir = request.json.get('input_dir')
        output_dir = request.json.get('output_dir')

        if not os.path.exists(input_dir):
            return jsonify({"error": "Input directory does not exist"}), 400

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # VisualizationDemo 초기화
        args = get_parser().parse_args([])  # 기본 인자 설정으로 argparse 초기화
        args.input = input_dir + '/*.jpg'
        args.output = output_dir
        cfg = setup_cfg(args)
        detection_demo = VisualizationDemo(cfg)

        # 배치 처리 실행
        start_time_all = time.time()
        img_count = 0

        for img_path in glob.glob(args.input):
            print(f"Processing {img_path}...")
            img_name = os.path.basename(img_path)
            img_save_path = os.path.join(args.output, img_name)
            img = cv2.imread(img_path)

            if img is None:
                print(f"Failed to load {img_path}")
                continue

            start_time = time.time()

            prediction, vis_output, polygons = detection_demo.run_on_image(img)

            # 결과 저장
            txt_save_path = os.path.join(args.output, f"res_img_{img_name.split('.')[0]}.txt")
            save_result_to_txt(txt_save_path, prediction, polygons)
            vis_output.save(img_save_path)

            print(f"Time: {time.time() - start_time:.2f} s / img")
            img_count += 1

        avg_time = (time.time() - start_time_all) / img_count if img_count > 0 else 0
        print(f"Average Time: {avg_time:.2f} s / img")

        return jsonify({"message": "Batch processing completed", "average_time": avg_time}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 서버 실행
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
