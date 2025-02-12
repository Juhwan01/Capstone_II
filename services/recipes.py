import requests
from sqlalchemy import select
from api.dependencies import get_async_db
from models.models import Recipe
from db.session import AsyncSessionLocal

keyId = "639e8e893d6445718216"
serviceId = "COOKRCP01"
startIdx = 1
endIdx = 100
manual_list = []
manual_img_list = []

import asyncpg

async def init():
    print("✅ init() 내부 실행 시작됨")  # 로그 추가

    try:
        print("🔹 DB 연결 시도 중...")  # 로그 추가
        conn = await asyncpg.connect(
            user="root",
            password="3321",
            database="recipe_db",
            host="svc.sel5.cloudtype.app",
            port=31872,
            timeout=10  # 10초 내 응답 없으면 오류 발생
        )
        print("✅ DB 연결 성공!")  # 로그 추가
        await conn.close()
        print("✅ DB 연결 종료 완료!")  # 로그 추가

    except Exception as e:
        print(f"🚨 init() 내부 에러 발생: {e}")  # 오류 발생 시 로그 출력


def fetch_recipe_data(keyId, serviceId, startIdx, endIdx, dataType="json"):
    base_url = "http://openapi.foodsafetykorea.go.kr/api"
    url = f"{base_url}/{keyId}/{serviceId}/{dataType}/{startIdx}/{endIdx}"
    
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()
    else:
        return f"Error: {response.status_code}"

def init_api_data(recipe_data):
    api_data_list = []
    
    rows = recipe_data.get("COOKRCP01", {}).get("row", [])
    
    for row in rows:
        manual_list = []
        manual_img_list = []
        
        for i in range(1, 21):
            data = row.get(f"MANUAL{str(i).zfill(2)}", "데이터 없음")
            img_data = row.get(f"MANUAL_IMG{str(i).zfill(2)}", "데이터 없음")
            if data:
                manual_list.append(data)
                manual_img_list.append(img_data)
            else:
                break
        
        try:
            calories = int(row.get("INFO_ENG", 0)) if row.get("INFO_ENG", 0).isdigit() else 0
            carbs = float(row.get("INFO_CAR", 0.0)) if row.get("INFO_CAR", 0.0).replace('.', '', 1).isdigit() else 0.0
            protein = float(row.get("INFO_PRO", 0.0)) if row.get("INFO_PRO", 0.0).replace('.', '', 1).isdigit() else 0.0
            fat = float(row.get("INFO_FAT", 0.0)) if row.get("INFO_FAT", 0.0).replace('.', '', 1).isdigit() else 0.0
            sodium = float(row.get("INFO_NA", 0.0)) if row.get("INFO_NA", 0.0).replace('.', '', 1).isdigit() else 0.0
        except ValueError:
            calories, carbs, protein, fat, sodium = 0, 0.0, 0.0, 0.0, 0.0
        
        api_dict = {
            "name": row.get("RCP_NM", "데이터 없음"),
            "category": row.get("RCP_PAT2", "데이터 없음"),
            "ingredient": row.get("RCP_PARTS_DTLS", "데이터 없음"),
            "image_large": row.get("ATT_FILE_NO_MK", "데이터 없음"),
            "image_small": row.get("ATT_FILE_NO_MAIN", "데이터 없음"),
            "manual": manual_list,
            "manual_img": manual_img_list,
            "nutrition": {
                "sodium": sodium,
                "protein": protein,
                "fat": fat,
                "carbohydrate": carbs,
                "calories": calories
            }
        }
    
        api_data_list.append(api_dict)
    
    return api_data_list


async def init():
    recipe_data = fetch_recipe_data(keyId, serviceId, startIdx, endIdx, dataType="json")
    api_data = init_api_data(recipe_data=recipe_data)
    async with AsyncSessionLocal() as session:
        for api_dict in api_data:
            recipe_name = api_dict['name']
            stmt = select(Recipe).filter(Recipe.name == recipe_name)
            result = await session.execute(stmt)
            existing_recipe = result.scalar_one_or_none()
            
            if not existing_recipe:  # 기존 레시피가 없으면 새 레시피 추가
                new_recipe = Recipe(
                    name=api_dict['name'],
                    category=api_dict['category'],
                    ingredients=api_dict['ingredient'],
                    image_large=api_dict['image_large'],
                    image_small=api_dict['image_small'],
                    instructions=api_dict['manual'],  # manual은 instructions에 매핑
                    cooking_img=api_dict['manual_img'],  # manual_img는 cooking_img에 매핑
                    sodium=api_dict['nutrition'].get('sodium', None),  # sodium 필드에 매핑
                    protein=api_dict['nutrition'].get('protein', None),  # protein 필드에 매핑
                    fat=api_dict['nutrition'].get('fat', None),  # fat 필드에 매핑
                    carbs=api_dict['nutrition'].get('carbohydrate', None),  # carbohydrate 필드에 매핑
                    calories=api_dict['nutrition'].get('calories', None)  # calories 필드에 매핑
                )
                session.add(new_recipe)
        
        await session.commit()

    print("데이터 추가 완료")
