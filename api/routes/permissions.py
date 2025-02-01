from fastapi import APIRouter, Depends
from api.dependencies import (
    get_current_active_user,
    check_chef,
    check_master_or_above,
    check_expert_or_above
)
from models.models import User, UserRole

router = APIRouter(prefix="/permissions", tags=["permissions"])

@router.get("/check")
async def check_user_permissions(
    current_user: User = Depends(get_current_active_user)
):
    """현재 사용자의 권한 체크"""
    permissions = {
        "role": current_user.role,
        "trust_score": current_user.trust_score,
        "permissions": {
            "can_write_global_announcements": current_user.role == UserRole.CHEF,
            "can_create_recipe_class": current_user.role == UserRole.CHEF,
            "can_host_bulk_purchase": current_user.role in [UserRole.CHEF, UserRole.MASTER],
            "can_host_regular_purchase": current_user.role in [UserRole.CHEF, UserRole.MASTER, UserRole.EXPERT],
            "basic_features": True  # 모든 사용자가 기본 기능 사용 가능
        }
    }
    return permissions

@router.get("/check-chef")
async def check_chef_permission(current_user: User = Depends(check_chef)):
    """셰프 권한 체크"""
    return {"message": "셰프 권한이 있습니다"}

@router.get("/check-master")
async def check_master_permission(current_user: User = Depends(check_master_or_above)):
    """요리마스터 이상 권한 체크"""
    return {"message": "요리마스터 이상 권한이 있습니다"}

@router.get("/check-expert")
async def check_expert_permission(current_user: User = Depends(check_expert_or_above)):
    """집밥달인 이상 권한 체크"""
    return {"message": "집밥달인 이상 권한이 있습니다"}