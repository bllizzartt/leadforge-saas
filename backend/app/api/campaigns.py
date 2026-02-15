from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.orm import selectinload

from app.core.security import get_current_user
from app.models.models import (
    Campaign, EmailSequence, CampaignLead, Lead, User, Company
)
from app.schemas.schemas import (
    CampaignCreate, CampaignUpdate, CampaignResponse, CampaignListResponse,
    CampaignDetailResponse, EmailSequenceCreate, EmailSequenceUpdate,
    EmailSequenceResponse, PaginationParams, MessageResponse, CampaignStatus
)

router = APIRouter()


@router.get("/", response_model=CampaignListResponse)
async def list_campaigns(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[CampaignStatus] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List campaigns with pagination"""
    conditions = [Campaign.company_id == current_user.company_id]
    if status_filter:
        conditions.append(Campaign.status == status_filter)
    
    from sqlalchemy import and_
    
    # Count total
    count_query = select(func.count(Campaign.id)).where(and_(*conditions))
    result = await db.execute(count_query)
    total = result.scalar()
    
    # Get campaigns
    query = (
        select(Campaign)
        .where(and_(*conditions))
        .order_by(Campaign.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    
    result = await db.execute(query)
    campaigns = result.scalars().all()
    
    return CampaignListResponse(
        items=campaigns,
        total=total,
        page=page,
        page_size=page_size,
        has_more=page * page_size < total
    )


@router.get("/{campaign_id}", response_model=CampaignDetailResponse)
async def get_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get campaign with sequences"""
    result = await db.execute(
        select(Campaign)
        .options(
            selectinload(Campaign.sequences),
            selectinload(Campaign.campaign_leads)
        )
        .where(
            Campaign.id == campaign_id,
            Campaign.company_id == current_user.company_id
        )
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Calculate stats
    stats = {
        "pending": 0,
        "sent": 0,
        "opened": 0,
        "clicked": 0,
        "replied": 0,
        "bounced": 0,
        "unsubscribed": 0
    }
    
    for cl in campaign.campaign_leads:
        status_key = cl.status if cl.status in stats else "pending"
        stats[status_key] += 1
    
    return CampaignDetailResponse(
        **campaign.__dict__,
        sequences=sorted(campaign.sequences, key=lambda x: x.step_order),
        stats=stats
    )


@router.post("/", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    request: CampaignCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new campaign"""
    # Get company settings for defaults
    result = await db.execute(
        select(Company).where(Company.id == current_user.company_id)
    )
    company = result.scalar_one()
    from app.models.models import CompanySettings
    settings_result = await db.execute(
        select(CompanySettings).where(CompanySettings.company_id == current_user.company_id)
    )
    settings = settings_result.scalar_one_or_none()
    
    campaign = Campaign(
        company_id=current_user.company_id,
        name=request.name,
        from_name=request.from_name or settings.default_from_name if settings else None,
        from_email=request.from_email or settings.default_from_email if settings else None,
        throttling_emails_per_hour=request.throttling_emails_per_hour,
        throttling_emails_per_day=request.throttling_emails_per_day,
        created_by_id=current_user.id
    )
    
    db.add(campaign)
    await db.flush()
    
    # Add lead count if leads specified
    if request.lead_ids:
        count = len(request.lead_ids)
        campaign.total_leads = count
        
        # Link leads to campaign
        campaign_leads = [
            CampaignLead(campaign_id=campaign.id, lead_id=lead_id)
            for lead_id in request.lead_ids
        ]
        db.add_all(campaign_leads)
    
    await db.commit()
    await db.refresh(campaign)
    return campaign


@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: int,
    request: CampaignUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update campaign"""
    result = await db.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.company_id == current_user.company_id
        )
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Can't edit running campaign
    if campaign.status == CampaignStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Cannot edit running campaign")
    
    for field, value in request.model_dump(exclude_unset=True).items():
        setattr(campaign, field, value)
    
    await db.commit()
    await db.refresh(campaign)
    return campaign


@router.delete("/{campaign_id}", response_model=MessageResponse)
async def delete_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete campaign"""
    result = await db.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.company_id == current_user.company_id
        )
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    await db.delete(campaign)
    await db.commit()
    
    return MessageResponse(message="Campaign deleted successfully")


# ============ Campaign Actions ============

@router.post("/{campaign_id}/start", response_model=CampaignResponse)
async def start_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start campaign"""
    result = await db.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.company_id == current_user.company_id
        )
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if campaign.status != CampaignStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Campaign is not in draft status")
    
    # Check for sequences
    seq_result = await db.execute(
        select(func.count(EmailSequence.id)).where(EmailSequence.campaign_id == campaign_id)
    )
    if seq_result.scalar() == 0:
        raise HTTPException(status_code=400, detail="Campaign has no email sequences")
    
    # Check for leads
    lead_result = await db.execute(
        select(func.count(CampaignLead.id)).where(CampaignLead.campaign_id == campaign_id)
    )
    if lead_result.scalar() == 0:
        raise HTTPException(status_code=400, detail="Campaign has no leads")
    
    campaign.status = CampaignStatus.RUNNING
    campaign.started_at = datetime.utcnow()
    
    # TODO: Schedule Celery tasks for sending emails
    
    await db.commit()
    await db.refresh(campaign)
    return campaign


@router.post("/{campaign_id}/pause", response_model=CampaignResponse)
async def pause_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Pause running campaign"""
    result = await db.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.company_id == current_user.company_id
        )
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if campaign.status != CampaignStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Campaign is not running")
    
    campaign.status = CampaignStatus.PAUSED
    
    # TODO: Cancel scheduled Celery tasks
    
    await db.commit()
    await db.refresh(campaign)
    return campaign


@router.post("/{campaign_id}/resume", response_model=CampaignResponse)
async def resume_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Resume paused campaign"""
    result = await db.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.company_id == current_user.company_id
        )
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if campaign.status != CampaignStatus.PAUSED:
        raise HTTPException(status_code=400, detail="Campaign is not paused")
    
    campaign.status = CampaignStatus.RUNNING
    
    # TODO: Restart Celery tasks
    
    await db.commit()
    await db.refresh(campaign)
    return campaign


@router.post("/{campaign_id}/cancel", response_model=CampaignResponse)
async def cancel_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel campaign"""
    result = await db.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.company_id == current_user.company_id
        )
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if campaign.status in [CampaignStatus.COMPLETED, CampaignStatus.CANCELED]:
        raise HTTPException(status_code=400, detail="Campaign already completed or canceled")
    
    campaign.status = CampaignStatus.CANCELED
    campaign.completed_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(campaign)
    return campaign


# ============ Email Sequence Routes ============

@router.get("/{campaign_id}/sequences", response_model=list[EmailSequenceResponse])
async def get_campaign_sequences(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get campaign email sequences"""
    # Verify campaign access
    result = await db.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.company_id == current_user.company_id
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    result = await db.execute(
        select(EmailSequence)
        .where(EmailSequence.campaign_id == campaign_id)
        .order_by(EmailSequence.step_order)
    )
    return result.scalars().all()


@router.post("/{campaign_id}/sequences", response_model=EmailSequenceResponse, status_code=status.HTTP_201_CREATED)
async def add_sequence(
    campaign_id: int,
    request: EmailSequenceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add email sequence to campaign"""
    # Verify campaign access
    result = await db.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.company_id == current_user.company_id
        )
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if campaign.status != CampaignStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Can only add sequences to draft campaigns")
    
    sequence = EmailSequence(
        campaign_id=campaign_id,
        **request.model_dump()
    )
    
    db.add(sequence)
    await db.commit()
    await db.refresh(sequence)
    return sequence


@router.put("/{campaign_id}/sequences/{sequence_id}", response_model=EmailSequenceResponse)
async def update_sequence(
    campaign_id: int,
    sequence_id: int,
    request: EmailSequenceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update email sequence"""
    result = await db.execute(
        select(EmailSequence).where(
            EmailSequence.id == sequence_id,
            EmailSequence.campaign_id == campaign_id
        )
    )
    sequence = result.scalar_one_or_none()
    if not sequence:
        raise HTTPException(status_code=404, detail="Sequence not found")
    
    for field, value in request.model_dump(exclude_unset=True).items():
        setattr(sequence, field, value)
    
    await db.commit()
    await db.refresh(sequence)
    return sequence


@router.delete("/{campaign_id}/sequences/{sequence_id}", response_model=MessageResponse)
async def delete_sequence(
    campaign_id: int,
    sequence_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete email sequence"""
    result = await db.execute(
        select(EmailSequence).where(
            EmailSequence.id == sequence_id,
            EmailSequence.campaign_id == campaign_id
        )
    )
    sequence = result.scalar_one_or_none()
    if not sequence:
        raise HTTPException(status_code=404, detail="Sequence not found")
    
    await db.delete(sequence)
    await db.commit()
    
    return MessageResponse(message="Sequence deleted successfully")


@router.post("/{campaign_id}/sequences/reorder")
async def reorder_sequences(
    campaign_id: int,
    sequence_ids: List[int],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Reorder email sequences"""
    # Verify campaign access
    result = await db.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.company_id == current_user.company_id
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    for index, seq_id in enumerate(sequence_ids):
        await db.execute(
            update(EmailSequence)
            .where(EmailSequence.id == seq_id)
            .values(step_order=index + 1)
        )
    
    await db.commit()
    
    return MessageResponse(message="Sequences reordered successfully")


# ============ Campaign Leads ============

@router.post("/{campaign_id}/leads", response_model=MessageResponse)
async def add_leads_to_campaign(
    campaign_id: int,
    lead_ids: List[int],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add leads to campaign"""
    result = await db.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.company_id == current_user.company_id
        )
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if campaign.status != CampaignStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Can only add leads to draft campaigns")
    
    # Verify all leads belong to company
    result = await db.execute(
        select(Lead.id).where(
            Lead.id.in_(lead_ids),
            Lead.company_id == current_user.company_id
        )
    )
    valid_lead_ids = [r[0] for r in result.fetchall()]
    
    # Add campaign leads
    new_entries = [
        CampaignLead(campaign_id=campaign_id, lead_id=lead_id)
        for lead_id in valid_lead_ids
        if lead_id not in [cl.lead_id for cl in campaign.campaign_leads]
    ]
    
    db.add_all(new_entries)
    campaign.total_leads = len(campaign.campaign_leads) + len(new_entries)
    
    await db.commit()
    
    return MessageResponse(message=f"Added {len(new_entries)} leads to campaign")
