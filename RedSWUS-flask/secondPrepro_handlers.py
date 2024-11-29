import os
from flask import request, jsonify
from skimage.io import imread
from skimage.color import rgb2gray
from scipy.ndimage import convolve
import numpy as np
from scipy.ndimage import gaussian_filter
import imageio.v2 as imageio
import matplotlib.pyplot as plt
from models import db, SecondPreprocessingResult, StdResult

# Second Preprocessing 핸들러 클래스
class SecondPreproAPP:
    def __init__(self, input_folder, output_folder):
        self.input_folder = input_folder
        self.output_folder = output_folder
        os.makedirs(self.output_folder, exist_ok=True)
        
        # PSF(Point Spread Function) 정의 (가우시안 필터 사용)
        self.psf = np.zeros((5, 5))  # 5x5 배열 생성
        self.psf[2, 2] = 1           # 중심에 값을 1로 설정
        self.psf = gaussian_filter(self.psf, sigma=1)  # 가우시안 필터 적용

    def process_images(self):
        std_result_code = request.form.get('std_result_code')

        # std_result_code가 없으면 에러 반환
        if not std_result_code:
            return jsonify({"status": "error", "message": "std_result_code is required."}), 400
        
        # 데이터베이스에서 STD 결과 조회
        std_result = StdResult.query.filter_by(std_result_code=std_result_code).first()
        if not std_result:
            return jsonify({"status": "error", "message": f"StdResult with ID {std_result_code} not found."}), 404

        input_image_path = std_result.std_result_path
        if not os.path.exists(input_image_path):
            return jsonify({"status": "error", "message": f"File not found at {input_image_path}."}), 404
        
        try:
            # 이미지 로드 및 처리
            image = imread(input_image_path)
            
            # 이미지를 흑백으로 변환 (RGBA -> RGB -> 그레이스케일)
            if image.ndim == 3 and image.shape[2] == 4:  # RGBA인 경우
                image = image[..., :3]  # RGB로 변환
            if image.ndim == 3:
                image = rgb2gray(image)

            # 컨볼루션 적용
            convolved = convolve(image, self.psf)

            # 처리된 이미지 저장 (파일 형식 유지)
            output_filename = f"second_prepro_{std_result_code}.png"
            output_image_path = os.path.join(self.output_folder, output_filename)
            imageio.imwrite(output_image_path, (convolved * 255).astype(np.uint8))  # 0-255 범위로 변환하여 저장

            # 처리된 이미지 데이터베이스에 저장
            second_prepro_result = SecondPreprocessingResult(
                video_code=std_result.video_code,
                std_result_code=std_result_code,
                second_result_path=output_image_path
            )
            db.session.add(second_prepro_result)
            db.session.commit()

            # 처리된 이미지 표시 (옵션)
            plt.imshow(convolved, cmap='gray')
            plt.axis('off')  # 축 숨기기
            plt.show()

            return jsonify({
                "status": "success",
                "message": "Second preprocessing completed successfully.",
                "second_result_path": output_image_path
            }), 200

        except Exception as e:
            return jsonify({"status": "error", "message": f"An error occurred: {str(e)}"}), 500

# SecondPreproAPP 인스턴스 생성
second_prepro_app = SecondPreproAPP(input_folder='/content/drive/MyDrive/crop/local_80',
                                    output_folder='/content/drive/MyDrive/crop_prepro/80')

# 핸들러 함수
def handle_secondPrepro():
    return second_prepro_app.process_images()
