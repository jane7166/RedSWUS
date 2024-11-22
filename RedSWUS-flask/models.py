from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()  # SQLAlchemy 객체 생성

# 감지 결과 저장 테이블 정의
class DetectionResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # 고유 ID
    file_name = db.Column(db.String(255), nullable=False)  # 업로드된 원본 파일명
    output_image_path = db.Column(db.String(255), nullable=False)  # 처리된 이미지 경로
    model_name = db.Column(db.String(50), nullable=False)  # 사용된 모델 이름
    created_at = db.Column(db.DateTime, default=db.func.now())  # 데이터 생성 시간
