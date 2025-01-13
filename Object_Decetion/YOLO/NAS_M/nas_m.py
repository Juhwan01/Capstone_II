from ultralytics import NAS
import cv2
import os

# YOLO-NAS M 모델 로드
model_m = NAS("yolo_nas_m.pt")

# 모델 정보 출력 (선택 사항)
model_m.info()

# COCO8 데이터셋으로 모델 검증
results_m = model_m.val(data="coco8.yaml")

# YOLO-NAS M 모델로 'test3.png' 이미지 추론
results_m = model_m("test.png")

# 저장할 디렉토리 설정
output_dir = "output_images"
os.makedirs(output_dir, exist_ok=True)  # 폴더가 없으면 생성

# 결과 저장 (YOLO-NAS M 모델)
for idx, result in enumerate(results_m):
    # confidence가 0.5 이상인 객체가 있으면 이미지 저장
    if result.boxes.conf is not None and any(conf > 0.5 for conf in result.boxes.conf):
        # 이미지 저장 경로 지정 (이미지 이름은 "test3_detected.jpg")
        output_image_path = os.path.join(output_dir, f"test3_detected_{idx + 1}.jpg")
        detected_image = result.plot()  # 감지된 객체가 표시된 이미지 생성
        cv2.imwrite(output_image_path, detected_image)  # 이미지 저장
        print(f"Saved image with detected objects using YOLO-NAS M at {output_image_path}.")
    else:
        print(f"No objects detected with high confidence in image {idx + 1} (YOLO-NAS M), not saving.")

print("Processing complete.")
