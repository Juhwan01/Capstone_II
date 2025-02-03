FROM python:3.12

WORKDIR /app

# 먼저 requirements.txt 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# 현재 디렉토리의 모든 파일을 컨테이너의 /app 디렉토리로 복사
COPY . .

# 실행 명령
CMD ["python", "main.py"]