from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, text
from sqlalchemy.orm import selectinload

from app.core.security import get_current_user
from app.models.models import (
    Lead, Campaign, CampaignLead, Company, DailyStats, User
)
from app.schemas.schemas import (
    DashboardStats, LeadAnalytics, CampaignAnalytics,
    DateRange
)

router = APIRouter()


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard statistics"""
    company_id = current_user.company_id
    
    # Get date ranges
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Lead stats
    total_leads_result = await db.execute(
        select(func.count(Lead.id)).where(Lead.company_id == company_id)
    )
    total_leads = total_leads_result.scalar()
    
    leads_today_result = await db.execute(
        select(func.count(Lead.id)).where(
            Lead.company_id == company_id,
            Lead.created_at >= today
        )
    )
    leads_today = leads_today_result.scalar()
    
    leads_week_result = await db.execute(
        select(func.count(Lead.id)).where(
            Lead.company_id == company_id,
            Lead.created_at >= week_ago
        )
    )
    leads_week = leads_week_result.scalar()
    
    leads_month_result = await db.execute(
        select(func.count(Lead.id)).where(
            Lead.company_id == company_id,
            Lead.created_at >= month_ago
        )
    )
    leads_month = leads_month_result.scalar()
    
    # Leads by source
    source_stats_result = await db.execute(
        select(Lead.source, func.count(Lead.id))
        .where(Lead.company_id == company_id)
        .group_by(Lead.source)
    )
    by_source = {str(source) or "unknown": count for source, count in source_stats_result.fetchall()}
    
    # Campaign stats
    total_campaigns_result = await db.execute(
        select(func.count(Campaign.id)).where(Campaign.company_id == company_id)
    )
    total_campaigns = total_campaigns_result.scalar()
    
    active_campaigns_result = await db.execute(
        select(func.count(Campaign.id)).where(
            Campaign.company_id == company_id,
            Campaign.status == "running"
        )
    )
    active_campaigns = active_campaigns_result.scalar()
    
    # Email stats
    emails_sent_result = await db.execute(
        select(func.sum(Campaign.emails_sent)).where(Campaign.company_id == company_id)
    )
    emails_sent = emails_sent_result.scalar() or 0
    
    emails_opened_result = await db.execute(
        select(func.sum(Campaign.emails_opened)).where(Campaign.company_id == company_id)
    )
    emails_opened = emails_opened_result.scalar() or 0
    
    emails_clicked_result = await db.execute(
        select(func.sum(Campaign.emails_clicked)).where(Campaign.company_id == company_id)
    )
    emails_clicked = emails_clicked_result.scalar() or 0
    
    emails_replied_result = await db.execute(
        select(func.sum(Campaign.emails_replied)).where(Campaign.company_id == company_id)
    )
    emails_replied = emails_replied_result.scalar() or 0
    
    # Calculate rates
    open_rate = (emails_opened / emails_sent * 100) if emails_sent > 0 else 0
    click_rate = (emails_clicked / emails_sent * 100) if emails_sent > 0 else 0
    reply_rate = (emails_replied / emails_sent * 100) if emails_sent > 0 else 0
    
    # Recent leads
    recent_leads_result = await db.execute(
        select(Lead)
        .where(Lead.company_id == company_id)
        .order_by(Lead.created_at.desc())
        .limit(5)
    )
    recent_leads = recent_leads_result.scalars().all()
    
    # Recent campaigns
    recent_campaigns_result = await db.execute(
        select(Campaign)
        .where(Campaign.company_id == company_id)
        .order_by(Campaign.created_at.desc())
        .limit(5)
    )
    recent_campaigns = recent_campaigns_result.scalars().all()
    
    return DashboardStats(
        leads=LeadAnalytics(
            total_leads=total_leads,
            leads_today=leads_today,
            leads_this_week=leads_week,
            leads_this_month=leads_month,
            by_source=by_source,
            by_industry={},
            by_company_size={}
        ),
        campaigns=CampaignAnalytics(
            total_campaigns=total_campaigns,
            active_campaigns=active_campaigns,
            total_sent=emails_sent,
            total_opens=emails_opened,
            total_clicks=emails_clicked,
            total_replies=emails_replied,
            avg_open_rate=round(open_rate, 2),
            avg_click_rate=round(click_rate, 2),
            avg_reply_rate=round(reply_rate, 2)
        ),
        recent_leads=recent_leads,
        recent_campaigns=recent_campaigns
    )


@router.get("/leads")
async def get_lead_analytics(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get lead analytics"""
    company_id = current_user.company_id
    
    # Count by source
    by_source_result = await db.execute(
        select(Lead.source, func.count(Lead.id))
        .where(Lead.company_id == company_id)
        .group_by(Lead.source)
    )
    by_source = {str(source) or "unknown": count for source, count in by_source_result.fetchall()}
    
    # Count by email status
    by_email_status_result = await db.execute(
        select(Lead.email_status, func.count(Lead.id))
        .where(Lead.company_id == company_id)
        .group_by(Lead.email_status)
    )
    by_email_status = {str(status) or "unknown": count for status, count in by_email_status_result.fetchall()}
    
    # Count by company size
    by_company_size_result = await db.execute(
        select(Lead.company_size, func.count(Lead.id))
        .where(
            Lead.company_id == company_id,
            Lead.company_size.isnot(None)
        )
        .group_by(Lead.company_size)
    )
    by_company_size = {str(size) or "unknown": count for size, count in by_company_size_result.fetchall()}
    
    return {
        "by_source": by_source,
        "by_email_status": by_email_status,
        "by_company_size": by_company_size,
        "total": await db.execute(select(func.count(Lead.id)).where(Lead.company_id == company_id))
    }


@router.get("/campaigns")
async def get_campaign_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get campaign analytics"""
    company_id = current_user.company_id
    
    # Get all campaign stats
    campaigns_result = await db.execute(
        select(Campaign).where(Campaign.company_id == company_id)
    )
    campaigns = campaigns_result.scalars().all()
    
    # Group by status
    by_status = {}
    for campaign in campaigns:
        status_key = campaign.status
        if status_key not in by_status:
            by_status[status_key] = {"count": 0, "sent": 0, "opened": 0, "clicked": 0}
        by_status[status_key]["count"] += 1
        by_status[status_key]["sent"] += campaign.emails_sent or 0
        by_status[status_key]["opened"] += campaign.emails_opened or 0
        by_status[status_key]["clicked"] += campaign.emails_clicked or 0
    
    # Calculate overall rates
    total_sent = sum(c.emails_sent or 0 for c in campaigns)
    total_opened = sum(c.emails_opened or 0 for c in campaigns)
    total_clicked = sum(c.emails_clicked or 0 for c in campaigns)
    total_replied = sum(c.emails_replied or 0 for c in campaigns)
    
    return {
        "total_campaigns": len(campaigns),
        "by_status": by_status,
        "total_sent": total_sent,
        "total_opened": total_opened,
        "total_clicked": total_clicked,
        "total_replied": total_replied,
        "avg_open_rate": round(total_opened / total_sent * 100, 2) if total_sent > 0 else 0,
        "avg_click_rate": round(total_clicked / total_sent * 100, 2) if total_sent > 0 else 0,
        "avg_reply_rate": round(total_replied / total_sent * 100, 2) if total_sent > 0 else 0
    }


@router.get("/team")
async def get_team_activity(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get team activity stats"""
    company_id = current_user.company_id
    
    # Get users and their activity
    users_result = await db.execute(
        select(User).where(User.company_id == company_id)
    )
    users = users_result.scalars().all()
    
    activity = []
    for user in users:
        leads_added = await db.execute(
            select(func.count(Lead.id)).where(Lead.created_by_id == user.id)
        )
        leads_added = leads_added.scalar()
        
        campaigns_created = await db.execute(
            select(func.count(Campaign.id)).where(Campaign.created_by_id == user.id)
        )
        campaigns_created = campaigns_created.scalar()
        
        activity.append({
            "user_id": user.id,
            "user_name": user.name,
            "leads_added": leads_added,
            "campaigns_created": campaigns_created,
            "emails_sent": 0  # Would need campaign_leads table join
        })
    
    return {"users": activity, "total_users": len(users)}
