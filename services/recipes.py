import requests
from sqlalchemy import select
from api.dependencies import get_async_db
from models.models import Recipe
from db.session import AsyncSessionLocal
from openai import OpenAI
from typing import Dict, List
import json
import asyncio
from datetime import datetime
from core.config import settings

keyId = "639e8e893d6445718216"
serviceId = "COOKRCP01"
startIdx = 1
endIdx = 10

class IngredientParser:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def parse_ingredients(self, ingredients_text: str) -> Dict[str, float]:
        try:
            lines = ingredients_text.split('\n')
            filtered_lines = [line for line in lines if line and not line.strip() in ['고명', '새우두부계란찜']]
            cleaned_text = ', '.join(filtered_lines)
            
            prompt = f"""
            다음 레시피 재료 목록을 단순한 재료:수량 형태의 JSON으로 변환해주세요.
            항목 구분이나 카테고리 없이 각 재료를 최상위 레벨의 키로 취급하여 변환해주세요.
            각 재료는 재료명을 key로, 괄호 안에 있는 숫자를 추출하여 value로 저장해주세요.
            분수는 실수로 변환해주세요 (예: 1/2 -> 0.5, 3/4 -> 0.75).
            '마리', '줄기', '모' 등의 단위가 있는 경우 해당 숫자를 그대로 사용합니다.
            
            규칙:
            1. 중첩된 객체 없이 모든 재료를 최상위 레벨에 나열
            2. 재료명만 키로 사용하고 수량을 값으로 사용
            3. 분량이 명시되지 않은 재료는 제외
            4. 카테고리나 구분 없이 단순 재료:수량 매핑으로만 구성
            
            예시:
            
            입력: "멸치육수(물 1.5컵, 멸치 3마리), 채소(양파 2개, 당근 1개)"
            출력: {{"물": 1.5, "멸치": 3, "양파": 2, "당근": 1}}
            입력: "연두부 75g(3/4모), 칵테일새우 20g(5마리)"
            출력: {{"연두부": 0.75, "칵테일새우": 5}}
            
            재료 목록:
            {cleaned_text}
            """

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "system",
                    "content": "레시피 재료를 단순한 재료:수량 형태의 JSON으로 변환하는 assistant입니다."
                }, {
                    "role": "user",
                    "content": prompt
                }],
                temperature=0.1,
                max_tokens=1000
            )

            parsed_text = response.choices[0].message.content.strip()
            parsed_text = parsed_text.replace('```json', '').replace('```', '').strip()
            
            print(f"정제된 GPT 응답: {parsed_text}")
            
            result = json.loads(parsed_text)
            print(f"파싱 성공: {result}")
            return result
                
        except Exception as e:
            print(f"파싱 에러: {str(e)}")
            return {}
        
def fetch_recipe_data(keyId: str, serviceId: str, startIdx: int, endIdx: int, dataType: str = "json") -> dict:
    """
    식품안전나라 레시피 API에서 데이터 가져오기
    """
    base_url = "http://openapi.foodsafetykorea.go.kr/api"
    url = f"{base_url}/{keyId}/{serviceId}/{dataType}/{startIdx}/{endIdx}"
    
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"API Error: {response.status_code}")
        return {}

async def init_api_data(recipe_data: dict) -> List[dict]:
    """
    API 데이터 초기화 및 가공
    """
    api_data_list = []
    ingredient_parser = IngredientParser(api_key=settings.OPENAI_API_KEY)
    
    rows = recipe_data.get("COOKRCP01", {}).get("row", [])
    total_rows = len(rows)
    
    print(f"총 {total_rows}개의 레시피 처리 시작")
    
    for idx, row in enumerate(rows, 1):
        try:
            # 조리 과정 및 이미지 추출
            manual_list = []
            manual_img_list = []
            for i in range(1, 21):
                step = row.get(f"MANUAL{str(i).zfill(2)}")
                img = row.get(f"MANUAL_IMG{str(i).zfill(2)}")
                if step and step != "데이터 없음":
                    manual_list.append(step)
                    manual_img_list.append(img if img != "데이터 없음" else None)

            # 영양 정보 추출 및 변환
            try:
                calories = int(row.get("INFO_ENG", "0").replace(" ", "")) if row.get("INFO_ENG") else 0
                carbs = float(row.get("INFO_CAR", "0").replace(" ", "")) if row.get("INFO_CAR") else 0.0
                protein = float(row.get("INFO_PRO", "0").replace(" ", "")) if row.get("INFO_PRO") else 0.0
                fat = float(row.get("INFO_FAT", "0").replace(" ", "")) if row.get("INFO_FAT") else 0.0
                sodium = float(row.get("INFO_NA", "0").replace(" ", "")) if row.get("INFO_NA") else 0.0
            except ValueError as e:
                print(f"영양 정보 변환 오류 ({row.get('RCP_NM')}): {e}")
                calories, carbs, protein, fat, sodium = 0, 0.0, 0.0, 0.0, 0.0

            # 재료 텍스트 파싱
            raw_ingredients = row.get("RCP_PARTS_DTLS", "")
            print(f"\n원본 재료 텍스트: {raw_ingredients}")
            if raw_ingredients and raw_ingredients != "데이터 없음":
                parsed_ingredients = ingredient_parser.parse_ingredients(raw_ingredients)
                print(f"파싱된 재료: {parsed_ingredients}")
            else:
                parsed_ingredients = {}

            api_dict = {
                "name": row.get("RCP_NM", ""),
                "category": row.get("RCP_PAT2", "기타"),
                "ingredients": parsed_ingredients,
                "image_large": row.get("ATT_FILE_NO_MK"),
                "image_small": row.get("ATT_FILE_NO_MAIN"),
                "instructions": manual_list,
                "cooking_img": manual_img_list,
                "calories": calories,
                "carbs": carbs,
                "protein": protein,
                "fat": fat,
                "sodium": sodium
            }

            api_data_list.append(api_dict)
            print(f"레시피 처리 중: {idx}/{total_rows} - {api_dict['name']}")

        except Exception as e:
            print(f"레시피 처리 오류 ({row.get('RCP_NM', 'Unknown')}): {e}")
            continue

    return api_data_list

async def init():
    """
    레시피 데이터 초기화 및 데이터베이스 저장
    """
    try:
        print("레시피 데이터 가져오기 시작")
        recipe_data = fetch_recipe_data(keyId, serviceId, startIdx, endIdx)
        if not recipe_data:
            print("API에서 데이터를 가져오지 못했습니다.")
            return

        print("레시피 데이터 가공 시작")
        api_data = await init_api_data(recipe_data)

        print("데이터베이스 저장 시작")
        async with AsyncSessionLocal() as session:
            for api_dict in api_data:
                try:
                    # 기존 레시피 확인
                    stmt = select(Recipe).where(Recipe.name == api_dict['name'])
                    result = await session.execute(stmt)
                    existing_recipe = result.scalar_one_or_none()
                    
                    if not existing_recipe:
                        # 새 레시피 추가
                        new_recipe = Recipe(
                            name=api_dict['name'],
                            category=api_dict['category'],
                            ingredients=api_dict['ingredients'],  # 파싱된 재료 딕셔너리
                            image_large=api_dict['image_large'],
                            image_small=api_dict['image_small'],
                            instructions=api_dict['instructions'],
                            cooking_img=api_dict['cooking_img'],
                            calories=api_dict['calories'],
                            carbs=api_dict['carbs'],
                            protein=api_dict['protein'],
                            fat=api_dict['fat'],
                            sodium=api_dict['sodium']
                        )
                        session.add(new_recipe)
                        print(f"새 레시피 추가: {api_dict['name']}")
                
                except Exception as e:
                    print(f"레시피 저장 오류 ({api_dict['name']}): {e}")
                    continue

            await session.commit()
            print("데이터베이스 저장 완료")

    except Exception as e:
        print(f"초기화 중 오류 발생: {e}")
        raise