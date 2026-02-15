from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from enum import Enum


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


# ============ Auth Schemas ============

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None
    company_id: Optional[int] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str
    company_name: str
    company_slug: str = Field(min_length=3, max_length=50, pattern="^[a-z0-9-]+$")


# ============ Company Schemas ============

class CompanyBase(BaseModel):
    name: str
    slug: str


class CompanyCreate(CompanyBase):
    plan: PlanType = PlanType.STARTER
    billing_email: Optional[EmailStr] = None


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    custom_domain: Optional[str] = None
    billing_email: Optional[EmailStr] = None


class CompanyResponse(CompanyBase):
    id: int
    plan: PlanType
    subscription_status: SubscriptionStatus
    logo_url: Optional[str]
    primary_color: str
    leads_limit: int
    users_limit: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class CompanySettingsBase(BaseModel):
    default_from_name: Optional[str] = None
    default_from_email: Optional[EmailStr] = None
    timezone: str = "UTC"
    auto_enrich: bool = False


class CompanySettingsUpdate(CompanySettingsBase):
    email_signature_html: Optional[str] = None
    notify_on_new_lead: Optional[bool] = None
    notify_on_campaign_complete: Optional[bool] = None
    notify_email: Optional[EmailStr] = None
    working_hours_start: Optional[str] = None
    working_hours_end: Optional[str] = None
    working_days: Optional[List[int]] = None


class CompanySettingsResponse(CompanySettingsBase):
    id: int
    company_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============ User Schemas ============

class UserBase(BaseModel):
    email: EmailStr
    name: str


class UserCreate(UserBase):
    password: str = Field(min_length=8)
    role: UserRole = UserRole.SALES


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    company_id: int
    role: UserRole
    is_active: bool
    avatar_url: Optional[str]
    last_login_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserInCompany(UserResponse):
    """User response with company info for admin view"""
    pass


# ============ Lead Schemas ============

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


class LeadBase(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    location: Optional[str] = None
    source: Optional[LeadSource] = None


class LeadCreate(LeadBase):
    pass


class LeadUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    location: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


class LeadResponse(LeadBase):
    id: int
    company_id: int
    full_name: Optional[str]
    email_status: EmailStatus
    enrichment_data: Optional[dict]
    tech_stack: Optional[List[str]]
    company_size: Optional[str]
    company_industry: Optional[str]
    tags: List[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class LeadListResponse(BaseModel):
    items: List[LeadResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class LeadImportRequest(BaseModel):
    leads: List[LeadCreate]
    source: LeadSource = LeadSource.IMPORT


class LeadExportRequest(BaseModel):
    lead_ids: List[int]
    format: str = "csv"  # csv, json


# ============ Scraping Schemas ============

class ScrapingStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class ScrapingSource(str, Enum):
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"
    GOOGLE_MAPS = "google_maps"
    CUSTOM_URLS = "custom_urls"


class ScrapingConfigBase(BaseModel):
    industry: Optional[str] = None
    location: Optional[str] = None
    company_size: Optional[str] = None
    job_titles: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    limit: int = 100


class LinkedInScrapingConfig(ScrapingConfigBase):
    search_url: Optional[str] = None
    sales_navigator: bool = True


class GoogleMapsScrapingConfig(ScrapingConfigBase):
    query: str
    radius_km: int = 10


class CustomUrlsConfig(BaseModel):
    urls: List[str] = Field(..., min_length=1)


class ScrapingJobCreate(BaseModel):
    source: ScrapingSource
    config: dict
    urls: Optional[List[str]] = None


class ScrapingJobResponse(BaseModel):
    id: int
    company_id: int
    source: ScrapingSource
    status: ScrapingStatus
    config: dict
    leads_found: int
    leads_enriched: int
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ScrapingJobListResponse(BaseModel):
    items: List[ScrapingJobResponse]
    total: int


# ============ Campaign Schemas ============

class CampaignStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELED = "canceled"


class CampaignBase(BaseModel):
    name: str
    from_name: Optional[str] = None
    from_email: Optional[EmailStr] = None


class CampaignCreate(CampaignBase):
    lead_ids: Optional[List[int]] = None
    from_name: Optional[str] = None
    from_email: Optional[EmailStr] = None
    throttling_emails_per_hour: int = 10
    throttling_emails_per_day: int = 100


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[CampaignStatus] = None
    from_name: Optional[str] = None
    from_email: Optional[EmailStr] = None
    throttling_emails_per_hour: Optional[int] = None
    throttling_emails_per_day: Optional[int] = None


class CampaignResponse(CampaignBase):
    id: int
    company_id: int
    status: CampaignStatus
    total_leads: int
    emails_sent: int
    emails_opened: int
    emails_clicked: int
    emails_replied: int
    unsubscribes: int
    created_by_id: Optional[int]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class CampaignListResponse(BaseModel):
    items: List[CampaignResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class CampaignDetailResponse(CampaignResponse):
    sequences: List["EmailSequenceResponse"]
    stats: dict


# ============ Email Sequence Schemas ============

class EmailSequenceBase(BaseModel):
    step_order: int
    subject: str
    subject_variant: Optional[str] = None
    body: str
    body_variant: Optional[str] = None
    delay_hours: int = 24


class EmailSequenceCreate(EmailSequenceBase):
    pass


class EmailSequenceUpdate(BaseModel):
    subject: Optional[str] = None
    subject_variant: Optional[str] = None
    body: Optional[str] = None
    body_variant: Optional[str] = None
    delay_hours: Optional[int] = None


class EmailSequenceResponse(EmailSequenceBase):
    id: int
    campaign_id: int
    emails_sent: int
    emails_opened: int
    emails_clicked: int
    emails_replied: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============ Analytics Schemas ============

class DateRange(BaseModel):
    start_date: datetime
    end_date: datetime


class LeadAnalytics(BaseModel):
    total_leads: int
    leads_today: int
    leads_this_week: int
    leads_this_month: int
    by_source: dict
    by_industry: dict
    by_company_size: dict


class CampaignAnalytics(BaseModel):
    total_campaigns: int
    active_campaigns: int
    total_sent: int
    total_opens: int
    total_clicks: int
    total_replies: int
    avg_open_rate: float
    avg_click_rate: float
    avg_reply_rate: float


class DashboardStats(BaseModel):
    leads: LeadAnalytics
    campaigns: CampaignAnalytics
    recent_leads: List[LeadResponse]
    recent_campaigns: List[CampaignResponse]


class RevenueData(BaseModel):
    date: datetime
    revenue: float
    leads_converted: int
    avg_deal_size: float


class TeamActivity(BaseModel):
    user_id: int
    user_name: str
    leads_added: int
    campaigns_created: int
    emails_sent: int


# ============ Common Schemas ============

class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 20


class SortParams(BaseModel):
    sort_by: str = "created_at"
    sort_order: str = "desc"


class FilterParams(BaseModel):
    search: Optional[str] = None
    source: Optional[LeadSource] = None
    email_status: Optional[EmailStatus] = None
    tags: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
