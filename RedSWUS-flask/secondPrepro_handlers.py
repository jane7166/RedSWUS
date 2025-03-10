import os
from flask import jsonify
from skimage.io import imread
from skimage.color import rgb2gray
from scipy.ndimage import convolve
import numpy as np
from scipy.ndimage import gaussian_filter
import imageio.v2 as imageio
from models import db, SecondPreprocessingResult, StdResult

# Second Preprocessing 핸들러 클래스
class SecondPreproAPP:
    def __init__(self, output_folder):
        self.output_folder = output_folder
        os.makedirs(self.output_folder, exist_ok=True)  # 폴더가 없으면 생성

        # PSF(Point Spread Function) 정의 (가우시안 필터 사용)
        self.psf = np.zeros((5, 5))  # 5x5 배열 생성
        self.psf[2, 2] = 1           # 중심에 값을 1로 설정
        self.psf = gaussian_filter(self.psf, sigma=1)  # 가우시안 필터 적용


    def process_images(self, std_result_code):
        """ 특정 std_result_code에 해당하는 이미지 처리 """

        try:
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

            # 이미지 로드 및 처리
            image = imread(input_image_path)

            # 이미지를 흑백으로 변환 (RGBA -> RGB -> 그레이스케일)
            if image.ndim == 3 and image.shape[2] == 4:
                image = image[..., :3]  # RGB로 변환
            if image.ndim == 3:
                image = rgb2gray(image)

            # 컨볼루션 적용
            convolved = convolve(image, self.psf)

            # 저장 경로 설정
            output_filename = f"second_prepro_{std_result_code}.png"
            output_image_path = os.path.join(self.output_folder, output_filename)
            output_image_path = os.path.abspath(output_image_path)

            # 이미지 저장
            try:
                imageio.imwrite(output_image_path, (convolved * 255).astype(np.uint8))
            except Exception as e:
                return jsonify({"status": "error", "message": f"Failed to save image: {str(e)}"}), 500

            # 파일이 실제로 저장되었는지 확인
            if not os.path.exists(output_image_path):
                return jsonify({"status": "error", "message": f"Image was not saved at {output_image_path}."}), 500

            # DB 저장
            second_prepro_result = SecondPreprocessingResult(
                video_code=std_result.video_code,
                std_result_code=std_result_code,
                second_result_path=output_image_path
            )
            db.session.add(second_prepro_result)
            db.session.commit()

            return {
                "status": "success",
                "message": "Second preprocessing completed successfully.",
                "second_result_path": output_image_path,
                "second_code_number": second_prepro_result.second_result_code
            }, 200

        except Exception as e:
            return jsonify({"status": "error", "message": f"An error occurred: {str(e)}"}), 500


# SecondPreproAPP 인스턴스 생성
second_prepro_app = SecondPreproAPP(output_folder='./second_preprocessed')

# 특정한 std_result_code 리스트를 받아서 second preprocessing 실행
def handle_secondPrepro(std_result_codes):
    """입력된 std_result_code 리스트만 처리"""
    second_code_list = []

    for std_result_code in std_result_codes:
        res = second_prepro_app.process_images(std_result_code)

        # 처리 결과 직접 확인
        if isinstance(res, tuple) and res[0].get("status") == "success":
            second_code_list.append(res[0].get("second_code_number"))

    return {
        "status": "success",
        "message": "Second preprocessing completed successfully.",
        "second_result_list": second_code_list
    }, 200


# DB에서 모든 std_result_code를 가져와 second preprocessing 실행
def handle_secondPrepro_all():
    """DB에서 모든 std_result_code를 가져와 처리"""
    std_results = StdResult.query.all()
    std_result_codes = [std.std_result_code for std in std_results]

    if not std_result_codes:
        return {
            "status": "error",
            "message": "No std_result_code found in database."
        }, 404

    return handle_secondPrepro(std_result_codes)
