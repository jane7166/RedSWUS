import os
import uuid
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
CORS(app)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'video_analysis.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy()

# Video 테이블
class Video(db.Model):
    __tablename__ = 'video'

    video_code = db.Column(db.Integer, primary_key=True)
    upload_time = db.Column(db.DateTime, nullable=False)
    video_path = db.Column(db.String(255), nullable=False)

# YOLO Result 테이블
class YoloResult(db.Model):
    __tablename__ = 'yolo_result'

    yolo_result_code = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    video_code = db.Column(db.Integer, db.ForeignKey('video.video_code'), nullable=False)
    yolo_result_path = db.Column(db.String(255), nullable=False)

    video = db.relationship('Video', backref=db.backref('yolo_results', lazy=True))

# 1st Preprocessing Result 테이블
class FirstPreprocessingResult(db.Model):
    __tablename__ = '1st_preprocessing_result'

    first_result_code = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    video_code = db.Column(db.Integer, db.ForeignKey('video.video_code'), nullable=False)
    yolo_result_code = db.Column(db.String, db.ForeignKey('yolo_result.yolo_result_code'), nullable=False)
    first_result_path = db.Column(db.String(255), nullable=False)

    video = db.relationship('Video', backref=db.backref('first_preprocessing_results', lazy=True))
    yolo_result = db.relationship('YoloResult', backref=db.backref('first_preprocessing_results', lazy=True))

# STD Result 테이블
class StdResult(db.Model):
    __tablename__ = 'std_result'

    std_result_code = db.Column(db.Integer, primary_key=True)
    video_code = db.Column(db.Integer, db.ForeignKey('video.video_code'), nullable=False)
    first_result_code = db.Column(db.String, db.ForeignKey('1st_preprocessing_result.first_result_code'), nullable=False)
    std_result_path = db.Column(db.String(255), nullable=False)

    video = db.relationship('Video', backref=db.backref('std_results', lazy=True))
    first_result = db.relationship('FirstPreprocessingResult', backref=db.backref('std_results', lazy=True))

# 2nd Preprocessing Result 테이블
class SecondPreprocessingResult(db.Model):
    __tablename__ = '2nd_preprocessing'

    second_result_code = db.Column(db.Integer, primary_key=True)
    video_code = db.Column(db.Integer, db.ForeignKey('video.video_code'), nullable=False)
    std_result_code = db.Column(db.Integer, db.ForeignKey('std_result.std_result_code'), nullable=False)
    second_result_path = db.Column(db.String(255), nullable=False)

    video = db.relationship('Video', backref=db.backref('second_preprocessing_results', lazy=True))
    std_result = db.relationship('StdResult', backref=db.backref('second_preprocessing_results', lazy=True))

# STR Result 테이블
class StrResult(db.Model):
    __tablename__ = 'str_result'

    str_result_code = db.Column(db.Integer, primary_key=True)
    video_code = db.Column(db.Integer, db.ForeignKey('video.video_code'), nullable=False)
    second_result_code = db.Column(db.Integer, db.ForeignKey('2nd_preprocessing.second_result_code'), nullable=False)
    str_result_path = db.Column(db.String(255), nullable=False)

    video = db.relationship('Video', backref=db.backref('str_results', lazy=True))
    second_result = db.relationship('SecondPreprocessingResult', backref=db.backref('str_results', lazy=True))

# Detection Result 테이블
class DetectionResult(db.Model):
    __tablename__ = 'detection_result'

    detection_result_code = db.Column(db.Integer, primary_key=True)
    video_code = db.Column(db.Integer, db.ForeignKey('video.video_code'), nullable=False)
    yolo_result_code = db.Column(db.String, db.ForeignKey('yolo_result.yolo_result_code'), nullable=False)
    object_class = db.Column(db.String(255), nullable=False)
    confidence_score = db.Column(db.Float, nullable=False)
    detection_result_path = db.Column(db.String(255), nullable=False)

    video = db.relationship('Video', backref=db.backref('detection_results', lazy=True))
    yolo_result = db.relationship('YoloResult', backref=db.backref('detection_results', lazy=True))