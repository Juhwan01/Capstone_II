from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from api.dependencies import get_async_db, get_current_active_user
from crud.crud_group_purchase import CRUDGroupPurchase, group_purchase
from schemas.group_purchases import (
    GroupPurchase, 
    GroupPurchaseCreate, 
    GroupPurchaseUpdate,
    GroupPurchaseDetail
)
from models.models import User, GroupPurchaseStatus
from services.s3_service import upload_images_to_s3
from utils.form_parser import parse_group_purchase_form

router = APIRouter(prefix="/group-purchases", tags=["group-purchases"])

@router.post("/", response_model=GroupPurchase)
async def create_group_purchase(
    *,
    db: AsyncSession = Depends(get_async_db),
    group_purchase_data: GroupPurchaseCreate = Depends(parse_group_purchase_form),
    files: Optional[List[UploadFile]] = File(None),
    current_user: User = Depends(get_current_active_user)
):
    """공동구매 생성 (이미지 업로드 포함)"""
    # 이미지 파일 확장자 검사
    if files:
        for file in files:
            file_ext = file.filename.split('.')[-1].lower()
            if file_ext not in {'png', 'jpg', 'jpeg', 'gif'}:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file extension: {file_ext}"
                )
        
        # S3 업로드
        image_urls = await upload_images_to_s3(files)
        if not image_urls:
            raise HTTPException(status_code=500, detail="Failed to upload images to S3")
        
        # 첫 번째 이미지를 대표 이미지로 설정
        group_purchase_data.image_url = image_urls[0]  # 이 필드를 스키마에 추가해야 함
    
    # 저장 가능 금액 계산
    saving_price = group_purchase_data.original_price - group_purchase_data.price
    
    # 공동구매 생성
    crud_group_purchase = CRUDGroupPurchase(db)
    
    try:
        group_purchase_obj = await crud_group_purchase.create_group_purchase(
            db=db,
            group_purchase_data=group_purchase_data,
            current_user=current_user,
            saving_price=saving_price,
            image_urls=image_urls if files else None
        )
        
        return group_purchase_obj
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[GroupPurchase])
async def list_group_purchases(
    db: AsyncSession = Depends(get_async_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user)
):
    """공동구매 목록 조회"""
    crud_group_purchase = CRUDGroupPurchase(db)
    group_purchases = await crud_group_purchase.get_multi(
        db=db,
        skip=skip,
        limit=limit
    )
    return group_purchases

@router.post("/{group_purchase_id}/join")
async def join_group_purchase(
    group_purchase_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """공동구매에 참여"""
    crud_group_purchase = CRUDGroupPurchase(db)
    result = await crud_group_purchase.join_group_purchase(
        db=db,
        group_purchase_id=group_purchase_id,
        current_user=current_user
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
        
    return result

@router.get("/{group_purchase_id}", response_model=GroupPurchaseDetail)
async def get_group_purchase(
    *,
    db: AsyncSession = Depends(get_async_db),
    group_purchase_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """공동구매 상세 조회"""
    crud_group_purchase = CRUDGroupPurchase(db)
    group_purchase_obj = await crud_group_purchase.get(db=db, id=group_purchase_id)
    if not group_purchase_obj:
        raise HTTPException(status_code=404, detail="Group purchase not found")
    return group_purchase_obj

@router.delete("/{group_purchase_id}")
async def delete_group_purchase(
    group_purchase_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """공동구매 삭제"""
    crud_group_purchase = CRUDGroupPurchase(db)
    result = await crud_group_purchase.delete_group_purchase(
        db=db,
        group_purchase_id=group_purchase_id,
        current_user=current_user
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
        
    return {"message": "Group purchase successfully deleted"}

@router.patch("/{group_purchase_id}", response_model=GroupPurchase)
async def update_group_purchase(
    *,
    group_purchase_id: int,
    group_purchase_data: GroupPurchaseUpdate = Depends(parse_group_purchase_form),
    files: Optional[List[UploadFile]] = File(None),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """공동구매 수정 (이미지 업데이트 포함)"""
    # 이미지 파일 처리
    if files:
        for file in files:
            file_ext = file.filename.split('.')[-1].lower()
            if file_ext not in {'png', 'jpg', 'jpeg', 'gif'}:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file extension: {file_ext}"
                )
        
        # S3 업로드
        image_urls = await upload_images_to_s3(files)
        if not image_urls:
            raise HTTPException(status_code=500, detail="Failed to upload new images to S3")
        
        # 첫 번째 이미지를 대표 이미지로 설정
        group_purchase_data.image_url = image_urls[0]

    crud_group_purchase = CRUDGroupPurchase(db)
    
    try:
        group_purchase_obj = await crud_group_purchase.update_group_purchase(
            db=db,
            group_purchase_id=group_purchase_id,
            current_user=current_user,
            obj_in=group_purchase_data,
            image_urls=image_urls if files else None
        )
        
        if not group_purchase_obj:
            raise HTTPException(status_code=404, detail="Group purchase not found")
            
        return group_purchase_obj
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{group_purchase_id}/leave")
async def leave_group_purchase(
    group_purchase_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """공동구매 참여 취소"""
    crud_group_purchase = CRUDGroupPurchase(db)
    result = await crud_group_purchase.leave_group_purchase(
        db=db,
        group_purchase_id=group_purchase_id,
        current_user=current_user
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
        
    return {
        "message": "공동구매 참여가 취소되었습니다",
        "group_purchase": result.get("group_purchase")
    }