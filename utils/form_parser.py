from fastapi import Form
from schemas.sale import SaleCreate

def parse_sale_form(
    ingredient_id: int = Form(...),
    ingredient_name: str = Form(...),
    seller_id: int = Form(...),
    title: str = Form(...),
    value: float = Form(...),
    location_lat: float = Form(...),
    location_lon: float = Form(...),
    expiry_date: str = Form(...),
    status: str = Form("Available"),
    contents: str = Form(...),
    amount: int = Form(...)
) -> SaleCreate:
    """
    Form 데이터를 SaleCreate Pydantic 모델로 변환 (파일 제외)
    """
    return SaleCreate(
        ingredient_id=ingredient_id,
        ingredient_name=ingredient_name,
        seller_id=seller_id,
        amount= amount,
        value=value,
        location_lat=location_lat,
        location_lon=location_lon,
        expiry_date=expiry_date,
        title=title,
        status=status,
        contents=contents
    )
