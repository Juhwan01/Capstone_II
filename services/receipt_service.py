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
from fastapi import HTTPException

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
        items = await self._extract_data_with_gpt(ocr_result)
        print("GPT 추출 결과:", items)
        print("GPT 추출 결과 타입:", type(items))
        if items:
            print("첫 번째 아이템:", items[0])
            print("첫 번째 아이템 타입:", type(items[0]))
        
        try:
            temp_items = []
            for item in items:
                print("현재 처리 중인 아이템:", item)
                # TempReceipt 테이블에 저장 (name만 사용)
                temp_receipt = TempReceipt(
                    name=item['name']
                )
                print("생성된 TempReceipt:", temp_receipt.__dict__)  # 객체의 속성 확인
                db.add(temp_receipt)
                await db.flush()
                
                # 원본 아이템에 temp_id 추가
                item['temp_id'] = temp_receipt.id
                temp_items.append(item)
            
            await db.commit()
            print("저장 완료된 아이템들:", temp_items)
            return temp_items
            
        except Exception as e:
            print(f"에러 발생 위치: {e.__traceback__.tb_frame.f_code.co_name}")
            print(f"에러 발생 라인: {e.__traceback__.tb_lineno}")
            print(f"에러 메시지: {str(e)}")
            print(f"에러 타입: {type(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"영수증 분석 중 오류가 발생했습니다: {str(e)}"
            )

    async def save_to_ingredients(
        self, 
        db: AsyncSession, 
        temp_id: int, 
        category: str, 
        expiry_date: datetime,
        user_id: int
    ) -> Ingredient:
        try:
            # 1. 임시 데이터 조회
            result = await db.execute(
                select(TempReceipt).where(TempReceipt.id == temp_id)
            )
            temp_item = result.scalar_one_or_none()
            
            if not temp_item:
                raise ValueError(f"임시 데이터를 찾을 수 없습니다. (ID: {temp_id})")
            
            # 2. ingredients 테이블에 저장
            ingredient = Ingredient(
                name=temp_item.name,
                category=category,
                expiry_date=expiry_date,
                amount=1,  # 기본값으로 1 설정
                user_id=user_id  # user_id 추가
            )
            
            # 3. 데이터베이스 반영
            db.add(ingredient)
            await db.delete(temp_item)
            await db.commit()
            
            return ingredient
            
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"식재료 저장 중 오류가 발생했습니다: {str(e)}"
            )

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
                    }"""
                },
                {"role": "user", "content": text}
            ]
        )
        
        try:
            response_text = response.choices[0].message.content
            print("GPT 원본 응답:", response_text)
            data = json.loads(response_text)
            return data.get('items', [])
        except Exception as e:
            print(f"GPT 응답 파싱 에러: {str(e)}")
            print(f"GPT 응답 원문: {response_text}")
            return []