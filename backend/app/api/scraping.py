from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.orm import selectinload

from app.core.security import get_current_user
from app.models.models import (
    ScrapingJob, Lead, Campaign, Company, User, ScrapingStatus as DBScrapingStatus
)
from app.schemas.schemas import (
    ScrapingJobCreate, ScrapingJobResponse, ScrapingJobListResponse,
    ScrapingSource, ScrapingConfigBase, LinkedInScrapingConfig,
    GoogleMapsScrapingConfig, MessageResponse
)

router = APIRouter()


@router.get("/jobs", response_model=ScrapingJobListResponse)
async def list_scraping_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List scraping jobs with pagination"""
    conditions = [ScrapingJob.company_id == current_user.company_id]
    if status_filter:
        conditions.append(ScrapingJob.status == status_filter)
    
    from sqlalchemy import and_
    
    # Count total
    count_query = select(func.count(ScrapingJob.id)).where(and_(*conditions))
    result = await db.execute(count_query)
    total = result.scalar()
    
    # Get jobs
    query = (
        select(ScrapingJob)
        .where(and_(*conditions))
        .order_by(ScrapingJob.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    
    result = await db.execute(query)
    jobs = result.scalars().all()
    
    return ScrapingJobListResponse(
        items=jobs,
        total=total,
        page=page,
        page_size=page_size,
        has_more=page * page_size < total
    )


@router.get("/jobs/{job_id}", response_model=ScrapingJobResponse)
async def get_scraping_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get scraping job details"""
    result = await db.execute(
        select(ScrapingJob).where(
            ScrapingJob.id == job_id,
            ScrapingJob.company_id == current_user.company_id
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Scraping job not found")
    return job


@router.post("/jobs", response_model=ScrapingJobResponse, status_code=status.HTTP_201_CREATED)
async def create_scraping_job(
    request: ScrapingJobCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new scraping job"""
    # Check if scraping is allowed
    from app.models.models import PlanType
    result = await db.execute(
        select(Company).where(Company.id == current_user.company_id)
    )
    company = result.scalar_one()
    
    if company.plan in [PlanType.STARTER]:
        raise HTTPException(
            status_code=403,
            detail="Scraping is not available on your plan. Upgrade to Growth or higher."
        )
    
    job = ScrapingJob(
        company_id=current_user.company_id,
        source=request.source,
        config=request.config or {},
        urls=request.urls,
        status=DBScrapingStatus.PENDING,
        created_by_id=current_user.id
    )
    
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    # Start scraping asynchronously (in real app, this would be Celery task)
    return job


@router.post("/jobs/{job_id}/start", response_model=ScrapingJobResponse)
async def start_scraping_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start a pending scraping job"""
    result = await db.execute(
        select(ScrapingJob).where(
            ScrapingJob.id == job_id,
            ScrapingJob.company_id == current_user.company_id
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Scraping job not found")
    
    if job.status not in [DBScrapingStatus.PENDING, DBScrapingStatus.FAILED]:
        raise HTTPException(status_code=400, detail="Job is not pending or failed")
    
    job.status = DBScrapingStatus.RUNNING
    job.started_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(job)
    
    # Run scraping (mock implementation)
    await run_scraping_job(job.id, db)
    
    return job


@router.post("/jobs/{job_id}/cancel", response_model=ScrapingJobResponse)
async def cancel_scraping_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel running scraping job"""
    result = await db.execute(
        select(ScrapingJob).where(
            ScrapingJob.id == job_id,
            ScrapingJob.company_id == current_user.company_id
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Scraping job not found")
    
    if job.status == DBScrapingStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Job is already completed")
    
    job.status = DBScrapingStatus.CANCELED
    job.completed_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(job)
    return job


@router.delete("/jobs/{job_id}", response_model=MessageResponse)
async def delete_scraping_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete scraping job"""
    result = await db.execute(
        select(ScrapingJob).where(
            ScrapingJob.id == job_id,
            ScrapingJob.company_id == current_user.company_id
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Scraping job not found")
    
    await db.delete(job)
    await db.commit()
    
    return MessageResponse(message="Scraping job deleted successfully")


# ============ Direct Scraping Endpoints ============

@router.post("/linkedin")
async def scrape_linkedin(
    config: LinkedInScrapingConfig,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Quick scrape from LinkedIn (creates job and runs immediately)"""
    job = ScrapingJob(
        company_id=current_user.company_id,
        source="linkedin",
        config=config.model_dump(),
        status=DBScrapingStatus.RUNNING,
        started_at=datetime.utcnow(),
        created_by_id=current_user.id
    )
    db.add(job)
    await db.flush()
    
    # Run mock scraping
    leads_data = await mock_linkedin_scraper(config)
    
    # Create leads
    leads = []
    for data in leads_data:
        lead = Lead(
            company_id=current_user.company_id,
            source_job_id=job.id,
            full_name=data.get("name"),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            title=data.get("title"),
            company=data.get("company"),
            email=data.get("email"),
            location=data.get("location"),
            linkedin_url=data.get("linkedin_url"),
            source="linkedin",
            enrichment_data=data.get("enrichment", {})
        )
        db.add(lead)
        leads.append(lead)
    
    job.leads_found = len(leads)
    job.status = DBScrapingStatus.COMPLETED
    job.completed_at = datetime.utcnow()
    
    await db.commit()
    
    return {
        "message": f"Scraped {len(leads)} leads from LinkedIn",
        "job_id": job.id,
        "leads_found": len(leads)
    }


@router.post("/google-maps")
async def scrape_google_maps(
    config: GoogleMapsScrapingConfig,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Quick scrape from Google Maps (creates job and runs immediately)"""
    job = ScrapingJob(
        company_id=current_user.company_id,
        source="google_maps",
        config=config.model_dump(),
        status=DBScrapingStatus.RUNNING,
        started_at=datetime.utcnow(),
        created_by_id=current_user.id
    )
    db.add(job)
    await db.flush()
    
    # Run mock scraping
    leads_data = await mock_google_maps_scraper(config)
    
    # Create leads
    leads = []
    for data in leads_data:
        lead = Lead(
            company_id=current_user.company_id,
            source_job_id=job.id,
            full_name=data.get("name"),
            title=data.get("title"),
            company=data.get("company"),
            email=data.get("email"),
            phone=data.get("phone"),
            location=data.get("location"),
            company_url=data.get("website"),
            source="google_maps",
            enrichment_data=data.get("enrichment", {})
        )
        db.add(lead)
        leads.append(lead)
    
    job.leads_found = len(leads)
    job.status = DBScrapingStatus.COMPLETED
    job.completed_at = datetime.utcnow()
    
    await db.commit()
    
    return {
        "message": f"Scraped {len(leads)} businesses from Google Maps",
        "job_id": job.id,
        "leads_found": len(leads)
    }


# ============ Helper Functions ============

async def run_scraping_job(job_id: int, db: AsyncSession):
    """Background scraping job runner (called from Celery in production)"""
    result = await db.execute(
        select(ScrapingJob).where(ScrapingJob.id == job_id)
    )
    job = result.scalar_one_or_none()
    
    if not job:
        return
    
    try:
        if job.source == "linkedin":
            config = LinkedInScrapingConfig(**job.config)
            leads_data = await mock_linkedin_scraper(config)
        elif job.source == "google_maps":
            config = GoogleMapsScrapingConfig(**job.config)
            leads_data = await mock_google_maps_scraper(config)
        else:
            leads_data = []
        
        # Create leads
        for data in leads_data:
            lead = Lead(
                company_id=job.company_id,
                source_job_id=job.id,
                full_name=data.get("name"),
                first_name=data.get("first_name"),
                last_name=data.get("last_name"),
                title=data.get("title"),
                company=data.get("company"),
                email=data.get("email"),
                location=data.get("location"),
                linkedin_url=data.get("linkedin_url"),
                source=job.source,
                enrichment_data=data.get("enrichment", {})
            )
            db.add(lead)
        
        job.leads_found = len(leads_data)
        job.status = DBScrapingStatus.COMPLETED
        
    except Exception as e:
        job.status = DBScrapingStatus.FAILED
        job.error_message = str(e)
    
    job.completed_at = datetime.utcnow()
    await db.commit()


async def mock_linkedin_scraper(config: LinkedInScrapingConfig):
    """Mock LinkedIn scraper - returns sample data"""
    import random
    
    sample_leads = [
        {
            "name": "John Smith",
            "first_name": "John",
            "last_name": "Smith",
            "title": "VP of Engineering",
            "company": "TechCorp Inc",
            "email": "john.smith@techcorp.com",
            "location": "San Francisco, CA",
            "linkedin_url": "https://linkedin.com/in/johnsmith",
            "enrichment": {
                "company_size": "500-1000 employees",
                "industry": "Technology",
                "tech_stack": ["React", "Python", "AWS"]
            }
        },
        {
            "name": "Sarah Johnson",
            "first_name": "Sarah",
            "last_name": "Johnson",
            "title": "Head of Product",
            "company": "InnovateLabs",
            "email": "sarah.j@innovatelabs.io",
            "location": "New York, NY",
            "linkedin_url": "https://linkedin.com/in/sarahjohnson",
            "enrichment": {
                "company_size": "50-200 employees",
                "industry": "SaaS",
                "tech_stack": ["Vue.js", "Node.js", "GCP"]
            }
        },
        {
            "name": "Michael Chen",
            "first_name": "Michael",
            "last_name": "Chen",
            "title": "CEO",
            "company": "StartupXYZ",
            "email": "mchen@startupxyz.com",
            "location": "Austin, TX",
            "linkedin_url": "https://linkedin.com/in/michaelchen",
            "enrichment": {
                "company_size": "10-50 employees",
                "industry": "FinTech",
                "tech_stack": ["React Native", "Go", "PostgreSQL"]
            }
        },
    ]
    
    # Return subset based on limit
    return sample_leads[:min(config.limit, len(sample_leads))]


async def mock_google_maps_scraper(config: GoogleMapsScrapingConfig):
    """Mock Google Maps scraper - returns sample data"""
    sample_businesses = [
        {
            "name": "Acme Coffee Roasters",
            "title": "Owner",
            "company": "Acme Coffee Roasters",
            "email": "contact@acmecoffee.com",
            "phone": "+1-555-0101",
            "location": config.location or "San Francisco, CA",
            "website": "https://acmecoffee.com",
            "enrichment": {
                "company_size": "10-50 employees",
                "industry": "Food & Beverage"
            }
        },
        {
            "name": "TechStart Solutions",
            "title": "Managing Director",
            "company": "TechStart Solutions",
            "email": "info@techstart.io",
            "phone": "+1-555-0102",
            "location": config.location or "San Francisco, CA",
            "website": "https://techstart.io",
            "enrichment": {
                "company_size": "50-200 employees",
                "industry": "IT Services"
            }
        },
        {
            "name": "Green Leaf Wellness",
            "title": "Founder",
            "company": "Green Leaf Wellness",
            "email": "hello@greenleafwellness.com",
            "phone": "+1-555-0103",
            "location": config.location or "San Francisco, CA",
            "website": "https://greenleafwellness.com",
            "enrichment": {
                "company_size": "10-50 employees",
                "industry": "Healthcare"
            }
        },
    ]
    
    return sample_businesses[:min(config.limit, len(sample_businesses))]
