from ultralytics import YOLO

# YOLOv8l 모델 로드 (모델 파일 경로를 지정)
model = YOLO('yolov8l.pt')  # yolov8l.pt는 예시로, 자신의 모델 파일 경로를 넣어주세요.

# 이미지 추론 (여러 객체가 포함된 이미지)
results = model(source='test3.png', conf=0.25)  # 'test.png'는 추론할 이미지 파일

# 추론 결과 출력
# 1. 감지된 객체의 바운딩 박스 좌표 (xyxy 형식)
print("Bounding Boxes (xyxy):", results[0].boxes.xyxy)

# 2. 각 객체의 신뢰도
print("Confidence Scores:", results[0].boxes.conf)

# 3. 각 객체의 클래스 정보
print("Classes:", results[0].boxes.cls)

# 4. 클래스 이름 (모델에서 학습된 클래스 이름을 출력)
for cls in results[0].boxes.cls:
    print(model.names[int(cls)])  # 클래스 번호를 클래스 이름으로 변환하여 출력

# 감지된 객체 시각화 (이미지에 객체 바운딩 박스 표시)
results[0].show()  # 첫 번째 결과 객체에서 show() 메서드를 호출

# 감지된 객체 결과 이미지 저장
results[0].save()  # 첫 번째 결과 객체에서 save() 메서드를 호출
