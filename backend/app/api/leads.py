from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_, text
from sqlalchemy.orm import selectinload

from app.core.security import get_current_user, get_current_company
from app.models.models import Lead, User, Company, ScrapingJob, CampaignLead
from app.schemas.schemas import (
    LeadCreate, LeadUpdate, LeadResponse, LeadListResponse,
    LeadImportRequest, PaginationParams, SortParams, FilterParams,
    MessageResponse, EmailStatus
)

router = APIRouter()


def build_lead_query(
    company_id: int,
    filters: Optional[FilterParams] = None,
    search: Optional[str] = None
):
    """Build lead query with filters"""
    conditions = [Lead.company_id == company_id]
    
    if filters:
        if filters.source:
            conditions.append(Lead.source == filters.source)
        if filters.email_status:
            conditions.append(Lead.email_status == filters.email_status)
        if filters.tags:
            conditions.append(Lead.tags.contains(filters.tags))
        if filters.date_from:
            conditions.append(Lead.created_at >= filters.date_from)
        if filters.date_to:
            conditions.append(Lead.created_at <= filters.date_to)
    
    if search:
        search_conditions = [
            Lead.full_name.ilike(f"%{search}%"),
            Lead.email.ilike(f"%{search}%"),
            Lead.company.ilike(f"%{search}%"),
            Lead.title.ilike(f"%{search}%"),
        ]
        conditions.append(or_(*search_conditions))
    
    return and_(*conditions)


@router.get("/", response_model=LeadListResponse)
async def list_leads(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    search: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    email_status: Optional[str] = Query(None),
    tags: Optional[List[str]] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List leads with pagination, sorting, and filtering"""
    
    # Build filters
    filters = FilterParams(
        source=source,
        email_status=email_status,
        tags=tags,
        date_from=date_from,
        date_to=date_to
    )
    
    conditions = build_lead_query(current_user.company_id, filters, search)
    
    # Count total
    count_query = select(func.count(Lead.id)).where(conditions)
    result = await db.execute(count_query)
    total = result.scalar()
    
    # Get leads
    sort_column = getattr(Lead, sort_by, Lead.created_at)
    sort_func = text(f"{sort_column.key} {sort_order}")
    
    query = (
        select(Lead)
        .where(conditions)
        .order_by(sort_func)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    
    result = await db.execute(query)
    leads = result.scalars().all()
    
    return LeadListResponse(
        items=leads,
        total=total,
        page=page,
        page_size=page_size,
        has_more=page * page_size < total
    )


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get single lead"""
    result = await db.execute(
        select(Lead).where(
            Lead.id == lead_id,
            Lead.company_id == current_user.company_id
        )
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.post("/", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    request: LeadCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new lead"""
    # Check lead limit
    result = await db.execute(
        select(Company).where(Company.id == current_user.company_id)
    )
    company = result.scalar_one()
    
    lead_count = await db.execute(
        select(func.count(Lead.id)).where(Lead.company_id == current_user.company_id)
    )
    lead_count = lead_count.scalar()
    
    if lead_count >= company.leads_limit:
        raise HTTPException(
            status_code=403,
            detail=f"Leads limit reached ({company.leads_limit}). Upgrade plan to add more."
        )
    
    # Build full name
    full_name = None
    if request.first_name or request.last_name:
        full_name = f"{request.first_name or ''} {request.last_name or ''}".strip()
    
    lead = Lead(
        company_id=current_user.company_id,
        full_name=full_name,
        created_by_id=current_user.id,
        **request.model_dump(exclude_unset=True)
    )
    
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    return lead


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: int,
    request: LeadUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update lead"""
    result = await db.execute(
        select(Lead).where(
            Lead.id == lead_id,
            Lead.company_id == current_user.company_id
        )
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Update full name if names changed
    if request.first_name is not None or request.last_name is not None:
        first_name = request.first_name or lead.first_name or ""
        last_name = request.last_name or lead.last_name or ""
        lead.full_name = f"{first_name} {last_name}".strip() or None
    
    for field, value in request.model_dump(exclude_unset=True).items():
        setattr(lead, field, value)
    
    await db.commit()
    await db.refresh(lead)
    return lead


@router.delete("/{lead_id}", response_model=MessageResponse)
async def delete_lead(
    lead_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete lead"""
    result = await db.execute(
        select(Lead).where(
            Lead.id == lead_id,
            Lead.company_id == current_user.company_id
        )
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    await db.delete(lead)
    await db.commit()
    
    return MessageResponse(message="Lead deleted successfully")


@router.post("/import", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def import_leads(
    request: LeadImportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Import multiple leads at once"""
    # Check lead limit
    result = await db.execute(
        select(Company).where(Company.id == current_user.company_id)
    )
    company = result.scalar_one()
    
    lead_count = await db.execute(
        select(func.count(Lead.id)).where(Lead.company_id == current_user.company_id)
    )
    lead_count = lead_count.scalar()
    
    if lead_count + len(request.leads) > company.leads_limit:
        raise HTTPException(
            status_code=403,
            detail=f"Not enough lead quota. Available: {company.leads_limit - lead_count}, Requested: {len(request.leads)}"
        )
    
    leads_to_add = []
    for lead_data in request.leads:
        full_name = None
        if lead_data.first_name or lead_data.last_name:
            full_name = f"{lead_data.first_name or ''} {lead_data.last_name or ''}".strip()
        
        leads_to_add.append(Lead(
            company_id=current_user.company_id,
            full_name=full_name,
            created_by_id=current_user.id,
            source=request.source,
            **lead_data.model_dump(exclude_unset=True)
        ))
    
    db.add_all(leads_to_add)
    await db.commit()
    
    return MessageResponse(message=f"Successfully imported {len(leads_to_add)} leads")


@router.post("/verify/{lead_id}", response_model=LeadResponse)
async def verify_lead_email(
    lead_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Trigger email verification for a lead"""
    from app.services.verification import verify_email_service
    
    result = await db.execute(
        select(Lead).where(
            Lead.id == lead_id,
            Lead.company_id == current_user.company_id
        )
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    if not lead.email:
        raise HTTPException(status_code=400, detail="Lead has no email address")
    
    # Verify email
    verification_result = await verify_email_service(lead.email)
    lead.email_status = verification_result.get("status", EmailStatus.UNVERIFIED)
    lead.enrichment_data = {
        **(lead.enrichment_data or {}),
        "email_verification": verification_result
    }
    
    await db.commit()
    await db.refresh(lead)
    return lead


@router.post("/enrich/{lead_id}", response_model=LeadResponse)
async def enrich_lead(
    lead_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Enrich lead with external data"""
    from app.services.enrichment import enrichment_service
    
    result = await db.execute(
        select(Lead).where(
            Lead.id == lead_id,
            Lead.company_id == current_user.company_id
        )
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Enrich lead
    enrichment_result = await enrichment_service.enrich_lead(lead)
    lead.enrichment_data = {
        **(lead.enrichment_data or {}),
        **(enrichment_result or {})
    }
    lead.enrichment_data["enriched_at"] = datetime.utcnow().isoformat()
    
    await db.commit()
    await db.refresh(lead)
    return lead


@router.get("/export/csv")
async def export_leads_csv(
    lead_ids: Optional[List[int]] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export leads as CSV"""
    from app.services.export import export_service
    
    conditions = [Lead.company_id == current_user.company_id]
    if lead_ids:
        conditions.append(Lead.id.in_(lead_ids))
    
    result = await db.execute(select(Lead).where(and_(*conditions)))
    leads = result.scalars().all()
    
    csv_content = export_service.leads_to_csv(leads)
    
    from fastapi.responses import Response
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads.csv"}
    )
