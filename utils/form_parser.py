from datetime import datetime
from decimal import Decimal
import json
from typing import Any, Dict, Optional
from fastapi import File, Form, UploadFile
from schemas.group_purchases import GroupPurchaseCreate, GroupPurchaseUpdate
from schemas.recipes import RecipeCreate
from schemas.sale import SaleCreate

async def parse_sale_form(
    ingredient_id: int = Form(...),
    ingredient_name: str = Form(...),
    seller_id: int = Form(...),
    value: float = Form(...),
    location_lat: float = Form(...),
    location_lon: float = Form(...),
    title: str = Form(...),
    expiry_date: str= Form(...),
    status: Optional[str] = Form(default="Available"),
    amount: int = Form(...),
    contents: Optional[str] = Form(None),
    category: str = Form(...)  # 카테고리 필드 추가
) -> SaleCreate:
    # SaleCreate 객체 생성
    return SaleCreate(
        ingredient_id=ingredient_id,
        ingredient_name=ingredient_name,
        seller_id=seller_id, 
        value=value,
        location_lat=location_lat,
        location_lon=location_lon,
        title=title,
        expiry_date=expiry_date,
        status=status,
        amount=amount,
        contents=contents,
        category=category  # 카테고리 필드 추가
    )
async def parse_recipe_form(
    name: str = Form(...),
    category: Optional[str] = Form(None),
    calories: Optional[int] = Form(None),
    carbs: Optional[float] = Form(None),
    protein: Optional[float] = Form(None),
    fat: Optional[float] = Form(None),
    sodium: Optional[float] = Form(None),
    ingredients: Optional[str] = Form(None),  # JSON 문자열로 전송
    instructions: Optional[str] = Form(None),  # JSON 문자열로 전송
) -> RecipeCreate:
    """
    Form 데이터를 RecipeCreate 모델로 변환하는 의존성 함수
    """
    # 안전하게 JSON 파싱 처리
    try:
        ingredients_dict = json.loads(ingredients) if ingredients and ingredients.strip() else {}
    except json.JSONDecodeError:
        ingredients_dict = {}
    
    try:
        instructions_list = json.loads(instructions) if instructions and instructions.strip() else []
    except json.JSONDecodeError:
        instructions_list = []
    
    # RecipeCreate 객체 생성
    return RecipeCreate(
        name=name,
        category=category,
        calories=calories,
        carbs=Decimal(str(carbs)) if carbs is not None else None,
        protein=Decimal(str(protein)) if protein is not None else None,
        fat=Decimal(str(fat)) if fat is not None else None,
        sodium=Decimal(str(sodium)) if sodium is not None else None,
        ingredients=ingredients_dict,
        instructions=instructions_list,
        cooking_img=[]  # 초기에는 빈 리스트로 설정
    )
# 공동구매 생성 폼 파서
async def parse_group_purchase_form(
    title: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),  # price_per_unit 대신 price
    original_price: float = Form(...),  # 새로 추가
    category: str = Form(...),
    max_participants: int = Form(5),  # 기본값을 5로 설정 (2보다 커야 함)
    end_date: datetime = Form(...)  # expires_at 대신 end_date
) -> GroupPurchaseCreate:
    """Form 데이터를 GroupPurchaseCreate 모델로 변환"""
    return GroupPurchaseCreate(
        title=title,
        description=description,
        price=price,
        original_price=original_price,
        category=category,
        max_participants=max_participants,
        end_date=end_date
    )

# 공동구매 업데이트 폼 파서
async def parse_group_purchase_update_form(
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    price: Optional[float] = Form(None),  # price_per_unit 대신 price
    original_price: Optional[float] = Form(None),  # 새로 추가
    status: Optional[str] = Form(None),
    end_date: Optional[datetime] = Form(None),  # expires_at 대신 end_date
    max_participants: Optional[int] = Form(None),
    category: Optional[str] = Form(None)
) -> GroupPurchaseUpdate:
    """Form 데이터를 GroupPurchaseUpdate 모델로 변환"""
    update_data = {}
    if title is not None:
        update_data["title"] = title
    if description is not None:
        update_data["description"] = description
    if price is not None:
        update_data["price"] = price
    if original_price is not None:
        update_data["original_price"] = original_price
    if status is not None:
        update_data["status"] = status
    if end_date is not None:
        update_data["end_date"] = end_date
    if max_participants is not None:
        update_data["max_participants"] = max_participants
    if category is not None:
        update_data["category"] = category
        
    return GroupPurchaseUpdate(**update_data)
async def parse_user_update_form(
    email: Optional[str] = Form(None),
    username: Optional[str] = Form(None),
    nickname: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    address_name: Optional[str] = Form(None),
    zone_no: Optional[str] = Form(None),
    location_lat: Optional[float] = Form(None),
    location_lon: Optional[float] = Form(None),
    profile_image: Optional[UploadFile] = File(None)
) -> tuple[Dict[str, Any], Optional[UploadFile]]:
    """
    Form 데이터를 UserUpdate 모델과 프로필 이미지로 변환하는 함수
    
    Returns:
        tuple: (업데이트 데이터 딕셔너리, 프로필 이미지 파일)
    """
    # 업데이트할 필드만 포함하는 딕셔너리 생성
    update_data = {}
    if email is not None:
        update_data["email"] = email
    if username is not None:
        update_data["username"] = username
    if nickname is not None:
        update_data["nickname"] = nickname
    if password is not None:
        update_data["password"] = password
    if address_name is not None:
        update_data["address_name"] = address_name
    if zone_no is not None:
        update_data["zone_no"] = zone_no
    if location_lat is not None:
        update_data["location_lat"] = location_lat
    if location_lon is not None:
        update_data["location_lon"] = location_lon
    
    return update_data, profile_image