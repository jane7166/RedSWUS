# str_handlers.py
from flask import request, jsonify
from models import db, SecondPreprocessingResult, StrResult
from PIL import Image
import os
import torch
from torchvision import transforms as T

# STR 모델 관련 클래스
class STRApp:
    def __init__(self):
        self._model = None
        self._preprocess = T.Compose([
            T.Resize((32, 128), T.InterpolationMode.BICUBIC),
            T.ToTensor(),
            T.Normalize(0.5, 0.5)
        ])

    def _load_model(self):
        if self._model is None:
            self._model = torch.hub.load('baudm/parseq', 'parseq', pretrained=True, trust_repo=True, weights_only = True).eval()
        return self._model

    def get_second_preprocessing_result(self, second_result_code):
        return SecondPreprocessingResult.query.filter_by(second_result_code=second_result_code).first()


    def save_str_result(self, video_code, second_result_code, str_result_path):
        str_result = StrResult(
            video_code=video_code,
            second_result_code=second_result_code,
            str_result_path=str_result_path
        )
        db.session.add(str_result)
        db.session.commit()

    @torch.inference_mode()
    def STRpredict(self, image: Image.Image):
        model = self._load_model()
        image = self._preprocess(image.convert('RGB')).unsqueeze(0)
        pred = model(image).softmax(-1)
        label, _ = model.tokenizer.decode(pred)
        raw_label, raw_confidence = model.tokenizer.decode(pred, raw=True)
        max_len = len(label[0]) + 1
        conf = list(map('{:0.1f}'.format, raw_confidence[0][:max_len].tolist()))
        return {
            "text": label[0],
            "raw_text": raw_label[0][:max_len],
            "confidence": conf
        }

# STRApp 인스턴스 생성
str_app = STRApp()

# 핸들러 함수
def handle_str_predict():
    try:
        second_result_code = request.form.get('second_result_code')
        if not second_result_code:
            return jsonify({"status": "error", "message": "second_result_code is required."}), 400

        second_result = str_app.get_second_preprocessing_result(second_result_code)
        if not second_result:
            return jsonify({"status": "error", "message": f"Second result with ID {second_result_code} not found."}), 404

        secondprepro_path = second_result.second_result_path
        if not os.path.exists(secondprepro_path):
            return jsonify({"status": "error", "message": f"File not found at {secondprepro_path}."}), 404

        secondimage = Image.open(secondprepro_path)

        text_result = str_app.STRpredict(secondimage)

        str_result_path = os.path.join("uploaded_videos", f"str_result_{second_result_code}.txt")
        with open(str_result_path, "w") as f:
            f.write(text_result['text'])

        str_app.save_str_result(second_result.video_code, second_result_code, str_result_path)

        return jsonify({
            "status": "success",
            "message": "STR result saved successfully.",
            "result": text_result,
            "str_result_path": str_result_path
        })

    except Exception as e:
        return jsonify({"status": "error", "message": f"An error occurred: {str(e)}"}), 500
