from flask import Flask, request, jsonify
from PIL import Image
import torch
from torchvision import transforms as T
import io

# Flask 애플리케이션 생성
app = Flask(__name__)

# parseq 모델 전용 클래스
class ParseqApp:
    def __init__(self):
        # 모델 캐시 초기화
        self._model = None
        # 입력 이미지를 전처리하는 파이프라인 정의
        self._preprocess = T.Compose([
            T.Resize((32, 128), T.InterpolationMode.BICUBIC),
            T.ToTensor(),
            T.Normalize(0.5, 0.5)
        ])

    def _load_model(self):
        # parseq 모델 로드 (한 번만 실행)
        if self._model is None:
            self._model = torch.hub.load('baudm/parseq', 'parseq', pretrained=True, trust_repo=True).eval()
        return self._model

    @torch.inference_mode()
    def predict(self, image: Image.Image):
        # parseq 모델 가져오기
        model = self._load_model()
        # 이미지 전처리
        image = self._preprocess(image.convert('RGB')).unsqueeze(0)
        # 모델 추론 수행
        pred = model(image).softmax(-1)
        # 결과 디코딩
        label, _ = model.tokenizer.decode(pred)
        raw_label, raw_confidence = model.tokenizer.decode(pred, raw=True)
        # 결과 포맷팅
        max_len = len(label[0]) + 1
        conf = list(map('{:0.1f}'.format, raw_confidence[0][:max_len].tolist()))
        return {
            "text": label[0],
            "raw_text": raw_label[0][:max_len],
            "confidence": conf
        }

# ParseqApp 인스턴스 생성
app_instance = ParseqApp()

# 기본 페이지 엔드포인트 추가
@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "message": "Welcome to the Parseq OCR API! Use POST /predict to send an image for prediction."
    })

# Flask 엔드포인트 생성
@app.route('/predict', methods=['POST'])
def predict():
    try:
        # 요청에서 파일 추출
        file = request.files.get('file')
        if not file:
            return jsonify({"status": "error", "message": "No file provided. Please upload an image file."}), 400

        # 파일을 PIL 이미지로 변환
        image = Image.open(io.BytesIO(file.read()))

        # ParseqApp 클래스의 predict 메서드 호출
        result = app_instance.predict(image)

        return jsonify({"status": "success", "result": result})
    except Exception as e:
        return jsonify({"status": "error", "message": f"An error occurred: {str(e)}"}), 500

# 서버 실행
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
