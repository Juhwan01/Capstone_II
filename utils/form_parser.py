import datetime
from decimal import Decimal
import json
from typing import Optional
from fastapi import Form
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
    target_amount: int = Form(...),
    current_amount: int = Form(0),
    price_per_unit: float = Form(...),
    status: str = Form("active"),
    expires_at: datetime = Form(...),
    location_lat: float = Form(...),
    location_lon: float = Form(...),
    max_participants: Optional[int] = Form(None),
    category: Optional[str] = Form(None)
) -> GroupPurchaseCreate:
    """Form 데이터를 GroupPurchaseCreate 모델로 변환"""
    return GroupPurchaseCreate(
        title=title,
        description=description,
        target_amount=target_amount,
        current_amount=current_amount,
        price_per_unit=price_per_unit,
        status=status,
        expires_at=expires_at,
        location_lat=location_lat,
        location_lon=location_lon,
        max_participants=max_participants,
        category=category
    )

# 공동구매 업데이트 폼 파서
async def parse_group_purchase_update_form(
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    target_amount: Optional[int] = Form(None),
    current_amount: Optional[int] = Form(None),
    price_per_unit: Optional[float] = Form(None),
    status: Optional[str] = Form(None),
    expires_at: Optional[datetime] = Form(None), # type: ignore
    location_lat: Optional[float] = Form(None),
    location_lon: Optional[float] = Form(None),
    max_participants: Optional[int] = Form(None),
    category: Optional[str] = Form(None)
) -> GroupPurchaseUpdate:
    """Form 데이터를 GroupPurchaseUpdate 모델로 변환"""
    update_data = {}
    if title is not None:
        update_data["title"] = title
    if description is not None:
        update_data["description"] = description
    if target_amount is not None:
        update_data["target_amount"] = target_amount
    if current_amount is not None:
        update_data["current_amount"] = current_amount
    if price_per_unit is not None:
        update_data["price_per_unit"] = price_per_unit
    if status is not None:
        update_data["status"] = status
    if expires_at is not None:
        update_data["expires_at"] = expires_at
    if location_lat is not None:
        update_data["location_lat"] = location_lat
    if location_lon is not None:
        update_data["location_lon"] = location_lon
    if max_participants is not None:
        update_data["max_participants"] = max_participants
    if category is not None:
        update_data["category"] = category
        
    return GroupPurchaseUpdate(**update_data)