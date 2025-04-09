import os
import cv2
import numpy as np
import torch
import uuid
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from models import FirstPreprocessingResult

class DetectronHandler:
    def __init__(self):
        os.makedirs("./stdoutput", exist_ok=True)

        # CUDA 디바이스 명시적으로 설정
        if torch.cuda.is_available():
            print("[INFO] CUDA 사용 가능 - GPU 디바이스 설정 중")
            torch.cuda.set_device(0)
            device = "cuda"
        else:
            print("[INFO] CUDA 사용 불가 - CPU로 설정")
            device = "cpu"
            
        torch.cuda.empty_cache()
        self.cfg = get_cfg()
        self.cfg.merge_from_file("./config.yaml")
        self.cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5
        self.cfg.MODEL.WEIGHTS = "./pt/model_0000599.pth"
        self.cfg.MODEL.DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
        self.predictor = DefaultPredictor(self.cfg)

    def handle_std_predict(self, first_result_code):
        torch.cuda.empty_cache()
        first_result = FirstPreprocessingResult.query.filter_by(first_result_code=first_result_code).first()
        if not first_result:
            return {"error": "First preprocessing result not found."}, 404
        
        file_path = first_result.first_result_path
        if not os.path.exists(file_path):
            return {"error": "File not found at the specified path."}, 404
        
        try:
            with open(file_path, 'rb') as file:
                np_img = np.frombuffer(file.read(), np.uint8)
            img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
            if img is None:
                return {"error": "Failed to decode the image."}, 400

            outputs = self.predictor(img)
            instances = outputs["instances"].to("cpu")
            boxes = instances.pred_boxes.tensor.numpy()
            classes = instances.pred_classes.numpy()
            scores = instances.scores.numpy()

            if boxes.size == 0:
                return 0

            cropped_paths = []
            for box, cls, score in zip(boxes, classes, scores):
                x1, y1, x2, y2 = map(int, box)
                x1 = max(0, x1 - 10)
                y1 = max(0, y1 - 10)
                x2 = min(img.shape[1], x2 + 10)
                y2 = min(img.shape[0], y2 + 10)
                cropped_img = img[y1:y2, x1:x2]

                original_name = os.path.basename(file_path)  # 예: 'image1.jpg'
                name_wo_ext, ext = os.path.splitext(original_name)     # 예: 'image1', '.jpg'
                filename = f"{name_wo_ext}_cropped_{cls}.jpg"
                
                output_path = os.path.join("./stdoutput", filename)
                cv2.imwrite(output_path, cropped_img)
                cropped_paths.append(output_path)

            return {
                "video_code": first_result.video_code,
                "first_result_code": first_result_code,
                "cropped_paths": cropped_paths,
                "boxes": boxes.tolist(),
                "classes": classes.tolist(),
                "scores": scores.tolist()
            }, 200

        except Exception as e:
            return {"error": f"Prediction failed: {str(e)}"}, 500
