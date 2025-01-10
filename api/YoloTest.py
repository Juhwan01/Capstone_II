import requests
from collections import Counter

# API 호출 코드는 그대로 유지
API_URL = "https://api-inference.huggingface.co/models/facebook/detr-resnet-101"
headers = {"Authorization": "Bearer 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"}

def query(filename):
    with open(filename, "rb") as f:
        data = f.read()
    response = requests.post(API_URL, headers=headers, data=data)
    return response.json()

def process_output(output):
    # 1. 단순 라벨 목록 추출
    unique_labels = list(set(item['label'] for item in output))
    
    # 2. 신뢰도가 높은(0.7 이상) 결과만 카운팅
    confident_detections = [item for item in output if item['score'] > 0.5]
    label_counts = Counter(item['label'] for item in confident_detections)
    
    print("감지된 모든 객체 종류:")
    print(unique_labels)
    print("\n신뢰도 70% 이상 객체 카운트:")
    for label, count in label_counts.items():
        print(f"{label}: {count}개")

# API 호출 및 결과 처리
output = query("test1.jpg")
print(output)
