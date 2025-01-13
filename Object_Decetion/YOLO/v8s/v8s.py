from ultralytics import YOLO
import cv2
import os

# 모델 로드
model = YOLO("yolov8s.pt")

# 예측 실행 (결과 저장)
result = model.predict("test3.png", conf=0.5)

# 결과 이미지 저장 (경로 지정)
save_path = "v8s_test3.jpg"
result[0].save(save_path)

# 감지된 결과 이미지 표시
plots = result[0].plot()
cv2.imshow("plot", plots)
cv2.waitKey(0)
cv2.destroyAllWindows()

# 이미지가 저장된 경로 출력
print(f"Saved image to: {save_path}")
