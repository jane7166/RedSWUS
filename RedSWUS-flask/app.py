from flask import Flask, jsonify, request
import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="torch")
from models import db
from video_handlers import handle_upload_video
from yolo_handlers import handle_yolo_predict
from firstPrepro_handlers import handle_firstPrepro
from std_handlers import run_all_handlers
from secondPrepro_handlers import handle_secondPrepro
from str_handlers import handle_str_predict

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///video_analysis.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

@app.route('/full_pipeline', methods=['POST'])
def full_pipeline():
    try:
        # Step 1: 비디오 업로드
        upload_response = handle_upload_video()
        if upload_response[1] != 200:
            return jsonify(upload_response[0]), upload_response[1]
        video_id = upload_response[0].get("video_id")

        # Step 2: YOLO 탐지 수행
        yolo_response = handle_yolo_predict(video_id=video_id)
        if yolo_response[1] != 200:
            return jsonify(yolo_response[0]), yolo_response[1]
        yolo_result_code = yolo_response[0].get("yolo_result_code")

        # Step 3: 1차 전처리 수행
        first_prepro_response = handle_firstPrepro(yolo_result_code=yolo_result_code)
        if first_prepro_response[1] != 200:
            return jsonify(first_prepro_response[0]), first_prepro_response[1]
        first_result_code = first_prepro_response[0].get("first_result_code")

        # Step 4: STD 수행
        std_response = run_all_handlers(first_result_code=first_result_code)
        if std_response[1] != 200:
            return jsonify(std_response[0]), std_response[1]
        std_result_code = std_response[0].get("std_result_code")

        # Step 5: 2차 전처리 수행
        second_prepro_response = handle_secondPrepro(std_result_code=std_result_code)
        if second_prepro_response[1] != 200:
            return jsonify(second_prepro_response[0]), second_prepro_response[1]
        second_result_code = second_prepro_response[0].get("second_result_code")

        # Step 6: STR 탐지 수행
        str_response = handle_str_predict(second_result_code=second_result_code)
        if str_response[1] != 200:
            return jsonify(str_response[0]), str_response[1]

        # 파이프라인 성공 결과 반환
        return jsonify({
            "status": "success",
            "message": "Full pipeline completed successfully.",
            "str_result": str_response[0]
        }), 200

    except Exception as e:
        # 파이프라인 중 오류 발생 시 반환
        return jsonify({
            "status": "error",
            "message": f"An error occurred during full pipeline execution: {str(e)}"
        }), 500

# 서버 실행
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
