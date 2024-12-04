import os
import torch
import cv2
import numpy as np
import glob
import tempfile
import time
from flask import Flask, request, jsonify, send_file
from models import db, FirstPreprocessingResult
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from model_detection import setup_cfg, get_parser, VisualizationDemo, save_result_to_txt

# Detectron2 설정 및 모델 불러오기
cfg = get_cfg()
cfg.merge_from_file("./config.yaml")  # YAML 파일 경로 설정
cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5  # 예측 점수 임계값 설정
cfg.MODEL.WEIGHTS = "./pt/model_0000599.pth"  # 모델 가중치 파일 경로 설정
cfg.MODEL.DEVICE = "cuda" if torch.cuda.is_available() else "cpu"  # GPU 사용 가능하면 GPU 사용

predictor = DefaultPredictor(cfg)

@app.route('/get_first_preprocessing', methods=['GET'])
def get_first_preprocessing():
    video_code = request.args.get('video_code')
    if not video_code:
        return jsonify({"error": "video_code parameter is required"}), 400

    first_result = FirstPreprocessingResult.query.filter_by(video_code=video_code).first()
    if not first_result:
        return jsonify({"error": "No preprocessing result found for this video_code"}), 404

    file_path = first_result.first_result_path
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found on server"}), 404

    return send_file(file_path, mimetype='image/jpeg')

@app.route('/detect_visual', methods=['POST'])
def detect_objects_visual():
    if 'image' not in request.files:
        return jsonify({"error": "이미지가 제공되지 않았습니다."}), 400

    try:
        # 이미지를 읽어오기
        file = request.files['image']
        np_img = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

        if img is None:
            return jsonify({"error": "이미지를 로드하지 못했습니다."}), 400

        # Detectron2를 사용하여 객체 탐지 실행
        outputs = predictor(img)
        instances = outputs["instances"].to("cpu")
        boxes = instances.pred_boxes.tensor.numpy()
        classes = instances.pred_classes.numpy()
        scores = instances.scores.numpy()

        # 시각화된 전체 이미지에 바운딩 박스와 레이블 그리기
        for box, cls, score in zip(boxes, classes, scores):
            x1, y1, x2, y2 = box
            cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            label = f"Class: {cls}, Score: {score:.2f}"
            cv2.putText(img, label, (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # 크롭된 객체 이미지 저장
        cropped_image_paths = []
        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = map(int, box)
            # 크롭 영역에 마진 추가
            margin = 10
            x1 = max(0, x1 - margin)
            y1 = max(0, y1 - margin)
            x2 = min(img.shape[1], x2 + margin)
            y2 = min(img.shape[0], y2 + margin)

            cropped_img = img[y1:y2, x1:x2]
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'_cropped_{i}.jpg')
            cropped_filename = temp_file.name
            cv2.imwrite(cropped_filename, cropped_img)
            cropped_image_paths.append(cropped_filename)

        # 시각화된 전체 이미지 저장
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        temp_filename = temp_file.name
        cv2.imwrite(temp_filename, img)

        # 결과 반환: 시각화된 이미지와 크롭된 이미지 경로
        return jsonify({
            "visualized_image": temp_filename,
            "cropped_images": cropped_image_paths
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/batch_process', methods=['POST'])
def batch_process():
    try:
        input_dir = request.json.get('input_dir')
        output_dir = request.json.get('output_dir')

        if not os.path.exists(input_dir):
            return jsonify({"error": "Input directory does not exist"}), 400

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        args = get_parser().parse_args([])
        args.input = input_dir + '/*.jpg'
        args.output = output_dir
        cfg = setup_cfg(args)
        detection_demo = VisualizationDemo(cfg)

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