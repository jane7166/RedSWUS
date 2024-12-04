from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Video 테이블
class Video(db.Model):
    __tablename__ = 'video'
    
    video_code = db.Column(db.Integer, primary_key=True)  # Video 고유 코드 (PK)
    upload_time = db.Column(db.DateTime, nullable=False)  # 업로드 시간
    video_path = db.Column(db.String(255), nullable=False)  # 비디오 파일 경로

# YOLO Result 테이블
class YoloResult(db.Model):
    __tablename__ = 'yolo_result'
    
    yolo_result_code = db.Column(db.Integer, primary_key=True)  # YOLO 결과 코드 (PK)
    video_code = db.Column(db.Integer, db.ForeignKey('video.video_code'), nullable=False)  # Video 코드 (FK)
    yolo_result_path = db.Column(db.String(255), nullable=False)  # YOLO 결과 경로
    
    # 관계 설정
    video = db.relationship('Video', backref=db.backref('yolo_results', lazy=True))

# 1st Preprocessing Result 테이블
class FirstPreprocessingResult(db.Model):
    __tablename__ = '1st_preprocessing_result'
    
    first_result_code = db.Column(db.Integer, primary_key=True)  # 1차 전처리 결과 코드 (PK)
    video_code = db.Column(db.Integer, db.ForeignKey('video.video_code'), nullable=False)  # Video 코드 (FK)
    yolo_result_code = db.Column(db.Integer, db.ForeignKey('yolo_result.yolo_result_code'), nullable=False)  # YOLO 결과 코드 (FK)
    first_result_path = db.Column(db.String(255), nullable=False)  # 1차 전처리 결과 경로
    
    # 관계 설정
    video = db.relationship('Video', backref=db.backref('first_preprocessing_results', lazy=True))
    yolo_result = db.relationship('YoloResult', backref=db.backref('first_preprocessing_results', lazy=True))

# STD Result 테이블
class StdResult(db.Model):
    __tablename__ = 'std_result'
    
    std_result_code = db.Column(db.Integer, primary_key=True)  # STD 결과 코드 (PK)
    video_code = db.Column(db.Integer, db.ForeignKey('video.video_code'), nullable=False)  # Video 코드 (FK)
    first_result_code = db.Column(db.Integer, db.ForeignKey('1st_preprocessing_result.first_result_code'), nullable=False)  # 1차 전처리 결과 코드 (FK)
    std_result_path = db.Column(db.String(255), nullable=False)  # STD 결과 경로
    
    # 관계 설정
    video = db.relationship('Video', backref=db.backref('std_results', lazy=True))
    first_result = db.relationship('FirstPreprocessingResult', backref=db.backref('std_results', lazy=True))

# 2nd Preprocessing Result 테이블
class SecondPreprocessingResult(db.Model):
    __tablename__ = '2nd_preprocessing'
    
    second_result_code = db.Column(db.Integer, primary_key=True)  # 2차 전처리 결과 코드 (PK)
    video_code = db.Column(db.Integer, db.ForeignKey('video.video_code'), nullable=False)  # Video 코드 (FK)
    std_result_code = db.Column(db.Integer, db.ForeignKey('std_result.std_result_code'), nullable=False)  # STD 결과 코드 (FK)
    second_result_path = db.Column(db.String(255), nullable=False)  # 2차 전처리 결과 경로
    
    # 관계 설정
    video = db.relationship('Video', backref=db.backref('second_preprocessing_results', lazy=True))
    std_result = db.relationship('StdResult', backref=db.backref('second_preprocessing_results', lazy=True))

# STR Result 테이블
class StrResult(db.Model):
    __tablename__ = 'str_result'
    
    str_result_code = db.Column(db.Integer, primary_key=True)  # STR 결과 코드 (PK)
    video_code = db.Column(db.Integer, db.ForeignKey('video.video_code'), nullable=False)  # Video 코드 (FK)
    second_result_code = db.Column(db.Integer, db.ForeignKey('2nd_preprocessing.second_result_code'), nullable=False)  # 2차 전처리 결과 코드 (FK)
    str_result_path = db.Column(db.String(255), nullable=False)  # STR 결과 경로
    
    # 관계 설정
    video = db.relationship('Video', backref=db.backref('str_results', lazy=True))
    second_result = db.relationship('SecondPreprocessingResult', backref=db.backref('str_results', lazy=True))

class DetectionResult(db.Model):
    __tablename__ = 'detection_result'
    
    detection_result_code = db.Column(db.Integer, primary_key=True)  # 감지 결과 코드 (PK)
    video_code = db.Column(db.Integer, db.ForeignKey('video.video_code'), nullable=False)  # Video 코드 (FK)
    yolo_result_code = db.Column(db.Integer, db.ForeignKey('yolo_result.yolo_result_code'), nullable=False)  # YOLO 결과 코드 (FK)
    object_class = db.Column(db.String(255), nullable=False)  # 감지된 객체 클래스
    confidence_score = db.Column(db.Float, nullable=False)  # 객체 감지 신뢰도 점수
    detection_result_path = db.Column(db.String(255), nullable=False)  # 감지된 결과 이미지 경로
    
    # 관계 설정
    video = db.relationship('Video', backref=db.backref('detection_results', lazy=True))
    yolo_result = db.relationship('YoloResult', backref=db.backref('detection_results', lazy=True))

