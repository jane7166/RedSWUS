import os
import cv2
import numpy as np
import tempfile
import torch
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from models import StdResult, db, FirstPreprocessingResult



class DetectronHandler:
    def __init__(self):
        # Detectron2 설정 및 모델 초기화
        torch.cuda.empty_cache() 
        self.cfg = get_cfg()
        self.cfg.merge_from_file("./config.yaml")
        self.cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5
        self.cfg.MODEL.WEIGHTS = "./pt/model_0000599.pth"
        self.cfg.MODEL.DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
        self.predictor = DefaultPredictor(self.cfg)

    def handle_std_predict(self, first_result_code):
        """
        STD 예측을 처리하는 메서드.
        """
        torch.cuda.empty_cache() 
        first_result = FirstPreprocessingResult.query.filter_by(first_result_code=first_result_code).first()
        if not first_result:
            print("First preprocessing result not found.")
            return {"error": "First preprocessing result not found."}, 404
        file_path = first_result.first_result_path
        print(f"Processing file path: {first_result.first_result_path}")
        if not os.path.exists(file_path):
            print("Failed to load the image.")
            return {"error": "File not found at the specified path."}, 404
        try: 
            with open(file_path, 'rb') as file:
                np_img = np.frombuffer(file.read(), np.uint8)  # 파일 데이터를 NumPy 배열로 변환

            # NumPy 배열을 OpenCV 이미지로 디코딩
            img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
            if img is None:
                return {"error": "Failed to load the image for prediction."}, 400

            # Detectron2 예측 실행
            
            outputs = self.predictor(img)
            print("Prediction completed.")
            instances = outputs["instances"].to("cpu")
            boxes = instances.pred_boxes.tensor.numpy()
            classes = instances.pred_classes.numpy()
            scores = instances.scores.numpy()
            # 바운딩 박스대로 이미지 크롭

            if boxes.size == 0:
                return 0

            for box, cls, score in zip(boxes, classes, scores):
                x1, y1, x2, y2 = box

                # 여유 공간 추가 (10픽셀씩)
                x1 = max(0, int(x1) - 10)
                y1 = max(0, int(y1) - 10)
                x2 = min(img.shape[1], int(x2) + 10)
                y2 = min(img.shape[0], int(y2) + 10)

                cropped_img = img[y1:y2, x1:x2]

                # 임시 파일로 저장
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'_cropped_{cls}.jpg')
                temp_filename = temp_file.name

                # 경로 문자열 교체: /tmp -> ./stdoutput
                temp_filename = temp_filename.replace('/tmp/', './stdoutput/')
                cv2.imwrite(temp_filename, cropped_img)

            std_result =  StdResult(
                video_code=first_result.video_code,
                first_result_code=first_result.first_result_code,
                std_result_path=temp_filename
            )

            db.session.add(std_result)
            db.session.commit()

            print(first_result_code, temp_filename)

            return {
                "std_result_code": std_result.std_result_code,
                "boxes": boxes.tolist(),
                "classes": classes.tolist(),
                "scores": scores.tolist(),
                "cropped_images": temp_filename  # 크롭된 이미지 경로 리스트 추가
            }, 200

        except Exception as e:
            return {"error": f"Prediction failed: {str(e)}"}, 500


# DetectronHandler 인스턴스 생성
detectron_handler = DetectronHandler()


def run_all_handlers(first_result_list):
    """
    STD 예측 및 후속 처리를 실행하는 함수.
    """

    std_result_list = []

    for first_result_code in first_result_list:
        # STD Predict 실행
        std_response = detectron_handler.handle_std_predict(first_result_code)
        if std_response == 0:
            continue

        if std_response[1] != 200:
            return std_response

        # STD Predict 결과 처리
        std_result_code = std_response[0].get("std_result_code")
        print(std_result_code)
        std_result_list.append(std_result_code)

    print(std_result_list)
    return {
        "status": "success",
        "std_result_list": std_result_list
    }, 200

__all__ = ["run_all_handlers"]
