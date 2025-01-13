from ultralytics import YOLO

# YOLOv8n-obb 모델 로드
model = YOLO('yolov8n-obb.pt')  # yolov8n-obb.pt는 예시로, 자신의 모델 파일 경로를 넣어주세요.

# 이미지 추론 (여러 객체가 포함된 이미지)
results = model(source='test3.png', conf=0.25)  # 'test.png'는 추론할 이미지 파일

# 결과 확인
if results:  # 결과가 None이 아닌지 확인
    print("Results:", results)  # 전체 결과 객체 확인

    # 1. 감지된 객체의 회전된 바운딩 박스 좌표 (xywh 및 회전 각도 포함)
    if hasattr(results[0], 'boxes') and hasattr(results[0].boxes, 'xywh'):
        print("Bounding Boxes (xywh, rotation):", results[0].boxes.xywh)  # 회전된 바운딩 박스
    else:
        print("Bounding boxes 정보가 없습니다.")

    # 2. 각 객체의 신뢰도
    if hasattr(results[0].boxes, 'conf'):
        print("Confidence Scores:", results[0].boxes.conf)

    # 3. 각 객체의 클래스 정보
    if hasattr(results[0].boxes, 'cls'):
        print("Classes:", results[0].boxes.cls)

    # 4. 클래스 이름 출력
    if hasattr(results[0].boxes, 'cls'):
        for cls in results[0].boxes.cls:
            print(model.names[int(cls)])  # 클래스 번호를 클래스 이름으로 변환하여 출력

    # 감지된 객체 시각화 (이미지에 객체 바운딩 박스 표시)
    results[0].show()  # 첫 번째 객체에서 show() 메서드를 호출

    # 감지된 객체 결과 이미지 저장
    results[0].save()  # 결과 이미지는 'runs/detect/exp' 폴더에 저장됨
else:
    print("결과가 없습니다. 이미지에 객체가 감지되지 않았을 수 있습니다.")
