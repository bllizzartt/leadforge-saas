from datetime import datetime
from enum import Enum
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, 
    Text, JSON, Float, Enum as SQLEnum, BigInteger, Index
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    SALES = "sales"
    VIEWER = "viewer"


class PlanType(str, Enum):
    STARTER = "starter"
    GROWTH = "growth"
    SCALE = "scale"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    TRIALING = "trialing"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"


class LeadSource(str, Enum):
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"
    GOOGLE_MAPS = "google_maps"
    CUSTOM_URLS = "custom_urls"
    IMPORT = "import"
    API = "api"


class EmailStatus(str, Enum):
    UNVERIFIED = "unverified"
    VALID = "valid"
    RISKY = "risky"
    INVALID = "invalid"


class CampaignStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELED = "canceled"


class ScrapingStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class Company(Base):
    """Multi-tenant company model"""
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    plan = Column(SQLEnum(PlanType), default=PlanType.STARTER)
    subscription_status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.TRIALING)
    billing_email = Column(String(255), nullable=True)
    
    # Branding (white-label)
    logo_url = Column(String(500), nullable=True)
    primary_color = Column(String(20), default="#3B82F6")
    custom_domain = Column(String(255), nullable=True)
    
    # Stripe/Payment info
    stripe_customer_id = Column(String(100), nullable=True)
    subscription_id = Column(String(100), nullable=True)
    
    # Limits
    leads_limit = Column(Integer, default=500)
    users_limit = Column(Integer, default=1)
    emails_per_month = Column(Integer, default=1000)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    trial_ends_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    users = relationship("User", back_populates="company", cascade="all, delete-orphan")
    settings = relationship("CompanySettings", back_populates="company", cascade="all, delete-orphan")
    leads = relationship("Lead", back_populates="company", cascade="all, delete-orphan")
    campaigns = relationship("Campaign", back_populates="company", cascade="all, delete-orphan")
    scraping_jobs = relationship("ScrapingJob", back_populates="company", cascade="all, delete-orphan")
    daily_stats = relationship("DailyStats", back_populates="company", cascade="all, delete-orphan")


class CompanySettings(Base):
    """Company-specific settings for white-label customization"""
    __tablename__ = "company_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), unique=True, nullable=False)
    
    # Email Settings
    default_from_name = Column(String(255), nullable=True)
    default_from_email = Column(String(255), nullable=True)
    reply_to_email = Column(String(255), nullable=True)
    
    # Signature
    email_signature_html = Column(Text, nullable=True)
    
    # Notifications
    notify_on_new_lead = Column(Boolean, default=True)
    notify_on_campaign_complete = Column(Boolean, default=True)
    notify_email = Column(String(255), nullable=True)
    
    # Enrichment defaults
    auto_enrich = Column(Boolean, default=False)
    enrichment_sources = Column(JSON, default=list)
    
    # Scheduling
    timezone = Column(String(50), default="UTC")
    working_hours_start = Column(String(10), default="09:00")
    working_hours_end = Column(String(10), default="18:00")
    working_days = Column(JSON, default=[0, 1, 2, 3, 4])  # 0=Monday
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    company = relationship("Company", back_populates="settings")


class User(Base):
    """User model with role-based access"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.SALES)
    is_active = Column(Boolean, default=True)
    avatar_url = Column(String(500), nullable=True)
    
    # Activity tracking
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    last_activity_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    company = relationship("Company", back_populates="users")
    created_leads = relationship("Lead", back_populates="created_by")
    created_campaigns = relationship("Campaign", back_populates="created_by")
    
    __table_args__ = (
        Index("ix_users_company_email", "company_id", "email", unique=True),
    )


class ScrapingJob(Base):
    """Scraping job tracking"""
    __tablename__ = "scraping_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    source = Column(SQLEnum(LeadSource), nullable=False)
    status = Column(SQLEnum(ScrapingStatus), default=ScrapingStatus.PENDING)
    
    # Configuration
    config = Column(JSON, nullable=False)  # {industry, location, company_size, etc.}
    urls = Column(JSON, nullable=True)  # For custom URL scraping
    
    # Results
    leads_found = Column(Integer, default=0)
    leads_enriched = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    
    # Tracking
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    company = relationship("Company", back_populates="scraping_jobs")
    created_by = relationship("User")
    leads = relationship("Lead", back_populates="source_job")


class Lead(Base):
    """Lead model with enrichment data"""
    __tablename__ = "leads"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    source_job_id = Column(Integer, ForeignKey("scraping_jobs.id"), nullable=True, index=True)
    
    # Contact Info
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    full_name = Column(String(255), nullable=True, index=True)
    title = Column(String(255), nullable=True, index=True)
    company = Column(String(255), nullable=True, index=True)
    company_url = Column(String(500), nullable=True)
    
    # Contact Details
    email = Column(String(255), nullable=True, index=True)
    email_status = Column(SQLEnum(EmailStatus), default=EmailStatus.UNVERIFIED)
    phone = Column(String(50), nullable=True)
    
    # Social
    linkedin_url = Column(String(500), nullable=True)
    twitter_handle = Column(String(100), nullable=True)
    instagram_handle = Column(String(100), nullable=True)
    
    # Location
    location = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    
    # Enrichment Data
    enrichment_data = Column(JSON, nullable=True)  # Clearbit, Hunter, etc. data
    tech_stack = Column(JSON, nullable=True)  # BuiltWith data
    company_size = Column(String(50), nullable=True)
    company_revenue = Column(String(100), nullable=True)
    company_industry = Column(String(100), nullable=True)
    funding_status = Column(String(50), nullable=True)
    
    # Source tracking
    source = Column(SQLEnum(LeadSource), nullable=True)
    source_url = Column(String(500), nullable=True)
    
    # Tags & Notes
    tags = Column(JSON, default=list)
    notes = Column(Text, nullable=True)
    
    # Creator
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    company = relationship("Company", back_populates="leads")
    source_job = relationship("ScrapingJob", back_populates="leads")
    created_by = relationship("User", back_populates="created_leads")
    campaign_leads = relationship("CampaignLead", back_populates="lead")
    
    __table_args__ = (
        Index("ix_leads_company_source", "company_id", "source"),
        Index("ix_leads_company_created", "company_id", "created_at"),
    )


class Campaign(Base):
    """Email campaign model"""
    __tablename__ = "campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    status = Column(SQLEnum(CampaignStatus), default=CampaignStatus.DRAFT)
    
    # Email Settings
    from_name = Column(String(255), nullable=True)
    from_email = Column(String(255), nullable=True)
    reply_to = Column(String(255), nullable=True)
    
    # Configuration
    throttling_emails_per_hour = Column(Integer, default=10)
    throttling_emails_per_day = Column(Integer, default=100)
    
    # Statistics
    total_leads = Column(Integer, default=0)
    emails_sent = Column(Integer, default=0)
    emails_opened = Column(Integer, default=0)
    emails_clicked = Column(Integer, default=0)
    emails_replied = Column(Integer, default=0)
    emails_bounced = Column(Integer, default=0)
    unsubscribes = Column(Integer, default=0)
    
    # Tracking
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    company = relationship("Company", back_populates="campaigns")
    created_by = relationship("User", back_populates="created_campaigns")
    sequences = relationship("EmailSequence", back_populates="campaign", cascade="all, delete-orphan", order_by="EmailSequence.step_order")
    campaign_leads = relationship("CampaignLead", back_populates="campaign", cascade="all, delete-orphan")


class EmailSequence(Base):
    """Email sequence steps"""
    __tablename__ = "email_sequences"
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False, index=True)
    step_order = Column(Integer, nullable=False)
    
    # Content
    subject = Column(String(255), nullable=False)
    subject_variant = Column(String(255), nullable=True)  # A/B testing
    body = Column(Text, nullable=False)
    body_variant = Column(Text, nullable=True)  # A/B testing
    
    # Timing
    delay_hours = Column(Integer, default=24)
    
    # Tracking
    emails_sent = Column(Integer, default=0)
    emails_opened = Column(Integer, default=0)
    emails_clicked = Column(Integer, default=0)
    emails_replied = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    campaign = relationship("Campaign", back_populates="sequences")


class CampaignLead(Base):
    """Campaign-lead relationship with tracking"""
    __tablename__ = "campaign_leads"
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    
    # Status
    status = Column(String(50), default="pending")  # pending, sent, opened, clicked, replied, bounced, unsubscribed
    current_step = Column(Integer, default=0)
    
    # Tracking
    sent_at = Column(DateTime(timezone=True), nullable=True)
    opened_at = Column(DateTime(timezone=True), nullable=True)
    clicked_at = Column(DateTime(timezone=True), nullable=True)
    replied_at = Column(DateTime(timezone=True), nullable=True)
    bounced_at = Column(DateTime(timezone=True), nullable=True)
    unsubscribed_at = Column(DateTime(timezone=True), nullable=True)
    
    # A/B test tracking
    subject_variant = Column(String(255), nullable=True)
    body_variant = Column(Text, nullable=True)
    
    # Engagement score
    engagement_score = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    campaign = relationship("Campaign", back_populates="campaign_leads")
    lead = relationship("Lead", back_populates="campaign_leads")
    
    __table_args__ = (
        Index("ix_campaign_leads_status", "campaign_id", "status"),
        Index("ix_campaign_leads_sent", "campaign_id", "sent_at"),
    )


class DailyStats(Base):
    """Daily aggregated statistics"""
    __tablename__ = "daily_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Lead stats
    leads_added = Column(Integer, default=0)
    leads_enriched = Column(Integer, default=0)
    leads_exported = Column(Integer, default=0)
    
    # Campaign stats
    emails_sent = Column(Integer, default=0)
    emails_opened = Column(Integer, default=0)
    emails_clicked = Column(Integer, default=0)
    emails_replied = Column(Integer, default=0)
    emails_bounced = Column(Integer, default=0)
    unsubscribes = Column(Integer, default=0)
    
    # Scraping stats
    scraping_jobs_run = Column(Integer, default=0)
    scraping_leads_found = Column(Integer, default=0)
    
    # Revenue attribution
    leads_to_customers = Column(Integer, default=0)
    revenue_generated = Column(Float, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index("ix_daily_stats_company_date", "company_id", "date", unique=True),
    )
