from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from app.core.security import get_current_user
from app.models.models import Company, CompanySettings, User, UserRole
from app.schemas.schemas import (
    CompanyCreate, CompanyUpdate, CompanyResponse, 
    CompanySettingsUpdate, CompanySettingsResponse,
    UserCreate, UserUpdate, UserResponse, UserInCompany,
    PaginationParams, MessageResponse
)

router = APIRouter()


# ============ Company Routes ============

@router.get("/me", response_model=CompanyResponse)
async def get_current_company(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current company"""
    result = await db.execute(
        select(Company).where(Company.id == current_user.company_id)
    )
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.put("/me", response_model=CompanyResponse)
async def update_current_company(
    request: CompanyUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current company"""
    result = await db.execute(
        select(Company).where(Company.id == current_user.company_id)
    )
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    for field, value in request.model_dump(exclude_unset=True).items():
        setattr(company, field, value)
    
    await db.commit()
    await db.refresh(company)
    return company


# ============ Company Settings Routes ============

@router.get("/me/settings", response_model=CompanySettingsResponse)
async def get_company_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get company settings"""
    result = await db.execute(
        select(CompanySettings).where(CompanySettings.company_id == current_user.company_id)
    )
    settings = result.scalar_one_or_none()
    if not settings:
        # Create default settings
        settings = CompanySettings(company_id=current_user.company_id)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    return settings


@router.put("/me/settings", response_model=CompanySettingsResponse)
async def update_company_settings(
    request: CompanySettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update company settings"""
    result = await db.execute(
        select(CompanySettings).where(CompanySettings.company_id == current_user.company_id)
    )
    settings = result.scalar_one_or_none()
    if not settings:
        settings = CompanySettings(company_id=current_user.company_id)
        db.add(settings)
        await db.flush()
    
    for field, value in request.model_dump(exclude_unset=True).items():
        setattr(settings, field, value)
    
    await db.commit()
    await db.refresh(settings)
    return settings


# ============ User Management Routes ============

@router.get("/me/users", response_model=list[UserInCompany])
async def list_company_users(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all users in company"""
    result = await db.execute(
        select(User)
        .options(selectinload(User.company))
        .where(User.company_id == current_user.company_id)
        .order_by(User.created_at.desc())
    )
    return result.scalars().all()


@router.post("/me/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_company_user(
    request: UserCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new user in company (Admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can add users")
    
    # Check user limit
    from app.models.models import Company
    result = await db.execute(
        select(Company).where(Company.id == current_user.company_id)
    )
    company = result.scalar_one()
    
    user_count = await db.execute(
        select(User).where(User.company_id == current_user.company_id)
    )
    user_count = len(user_count.scalars().all())
    
    if user_count >= company.users_limit:
        raise HTTPException(
            status_code=403, 
            detail=f"User limit reached ({company.users_limit} users). Upgrade plan to add more."
        )
    
    # Check if email exists
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    from app.core.security import get_password_hash
    user = User(
        company_id=current_user.company_id,
        email=request.email,
        name=request.name,
        password_hash=get_password_hash(request.password),
        role=request.role
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.put("/me/users/{user_id}", response_model=UserResponse)
async def update_company_user(
    user_id: int,
    request: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update company user"""
    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.company_id == current_user.company_id
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Only admins can change roles
    if request.role is not None and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can change roles")
    
    # Can't demote yourself
    if user_id == current_user.id and request.role is not None:
        if request.role != UserRole.ADMIN:
            raise HTTPException(status_code=400, detail="Cannot demote yourself")
    
    for field, value in request.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/me/users/{user_id}", response_model=MessageResponse)
async def delete_company_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete company user (Admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can delete users")
    
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.company_id == current_user.company_id
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.delete(user)
    await db.commit()
    
    return MessageResponse(message="User deleted successfully")
