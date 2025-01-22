from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인 허용 (필요시 특정 도메인만 추가)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
