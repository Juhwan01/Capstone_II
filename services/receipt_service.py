from fastapi import UploadFile
from openai import OpenAI
import json
import requests
import uuid
import time
from core.config import settings
from datetime import datetime
from sqlalchemy import select
from models.models import Ingredient, TempReceipt
from sqlalchemy.ext.asyncio import AsyncSession

class ReceiptService:
    def __init__(self):
        self.ocr_api_url = settings.CLOVA_OCR_API_URL
        self.ocr_secret_key = settings.CLOVA_OCR_SECRET_KEY
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

    async def analyze_receipt(self, file: UploadFile, db: AsyncSession) -> list:
        # OCR 분석
        ocr_result = await self._process_ocr(file)
        print("OCR 결과:", ocr_result)
        
        # ChatGPT를 통한 데이터 추출
        extracted_items = await self._extract_data_with_gpt(ocr_result)
        print("추출된 아이템:", extracted_items)
        
        # 임시 테이블에 저장
        temp_items = []
        try:
            for item in extracted_items:
                print("저장할 아이템:", item)
                temp_item = TempReceipt(
                    name=item['name'],
                    value=float(item['amount'])
                )
                db.add(temp_item)
                temp_items.append(item)
            
            await db.commit()
            print("임시 데이터 저장 완료")
        except Exception as e:
            print("데이터베이스 저장 중 에러:", str(e))
            raise
        
        return temp_items

    async def save_to_ingredients(
        self, 
        db: AsyncSession, 
        temp_id: int, 
        category: str, 
        expiry_date: datetime
    ) -> Ingredient:
        """임시 데이터를 ingredients 테이블로 이동"""
        result = await db.execute(
            select(TempReceipt).where(TempReceipt.id == temp_id)
        )
        temp_item = result.scalar_one_or_none()
        
        if not temp_item:
            raise ValueError("임시 데이터를 찾을 수 없습니다")
            
        ingredient = Ingredient(
            name=temp_item.name,
            value=temp_item.value,
            category=category,
            expiry_date=expiry_date,
            location_lat=37.5665,  # 서울시청 위도
            location_lon=126.9780,  # 서울시청 경도
            nutrition={}
        )
        
        db.add(ingredient)
        await db.delete(temp_item)
        await db.commit()
        
        return ingredient

    async def _process_ocr(self, file: UploadFile) -> str:
        request_json = {
            'images': [{'format': 'jpg', 'name': 'receipt'}],
            'requestId': str(uuid.uuid4()),
            'version': 'V2',
            'timestamp': int(round(time.time() * 1000))
        }

        payload = {'message': json.dumps(request_json).encode('UTF-8')}
        files = [('file', await file.read())]
        headers = {'X-OCR-SECRET': self.ocr_secret_key}

        response = requests.request("POST", self.ocr_api_url, headers=headers, data=payload, files=files)
        json_data = response.json()

        # OCR 결과를 문자열로 변환
        string_result = ''
        for field in json_data['images'][0]['fields']:
            string_result += field['inferText'] + (' ' if not field['lineBreak'] else '\n')
            
        return string_result

    async def _extract_data_with_gpt(self, text: str) -> list:
        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system", 
                    "content": """영수증 데이터를 다음 JSON 형식으로 정확히 변환해주세요:
                    {
                        "items": [
                            {
                                "name": "상품명",
                                "quantity": 수량,
                                "amount": 가격,
                                "purchase_date": "YYYY-MM-DD"
                            }
                        ]
                    }
                    반드시 유효한 JSON 형식으로 응답해주세요."""
                },
                {"role": "user", "content": text}
            ]
        )

        try:
            # ChatGPT 응답에서 JSON 문자열 추출 및 파싱
            response_text = response.choices[0].message.content
            data = json.loads(response_text)
            return data.get('items', [])  # items 키가 없으면 빈 리스트 반환
        except (json.JSONDecodeError, KeyError) as e:
            print(f"GPT 응답 파싱 에러: {response_text}")
            return []