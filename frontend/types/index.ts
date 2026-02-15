// User & Auth Types
export interface User {
  id: number;
  company_id: number;
  email: string;
  name: string;
  role: UserRole;
  is_active: boolean;
  avatar_url?: string;
  last_login_at?: string;
  created_at: string;
}

export enum UserRole {
  ADMIN = 'admin',
  MANAGER = 'manager',
  SALES = 'sales',
  VIEWER = 'viewer'
}

// Company Types
export interface Company {
  id: number;
  name: string;
  slug: string;
  plan: PlanType;
  subscription_status: SubscriptionStatus;
  logo_url?: string;
  primary_color: string;
  leads_limit: number;
  users_limit: number;
  created_at: string;
}

export enum PlanType {
  STARTER = 'starter',
  GROWTH = 'growth',
  SCALE = 'scale',
  ENTERPRISE = 'enterprise'
}

export enum SubscriptionStatus {
  ACTIVE = 'active',
  TRIALING = 'trialing',
  PAST_DUE = 'past_due',
  CANCELED = 'canceled',
  INCOMPLETE = 'incomplete'
}

// Lead Types
export interface Lead {
  id: number;
  company_id: number;
  first_name?: string;
  last_name?: string;
  full_name?: string;
  title?: string;
  company?: string;
  company_url?: string;
  email?: string;
  email_status: EmailStatus;
  phone?: string;
  linkedin_url?: string;
  twitter_handle?: string;
  location?: string;
  city?: string;
  country?: string;
  enrichment_data?: Record<string, any>;
  tech_stack?: string[];
  company_size?: string;
  company_industry?: string;
  source?: LeadSource;
  source_url?: string;
  tags: string[];
  notes?: string;
  created_at: string;
  updated_at: string;
}

export enum LeadSource {
  LINKEDIN = 'linkedin',
  INSTAGRAM = 'instagram',
  GOOGLE_MAPS = 'google_maps',
  CUSTOM_URLS = 'custom_urls',
  IMPORT = 'import',
  API = 'api'
}

export enum EmailStatus {
  UNVERIFIED = 'unverified',
  VALID = 'valid',
  RISKY = 'risky',
  INVALID = 'invalid'
}

export interface LeadCreate {
  first_name?: string;
  last_name?: string;
  title?: string;
  company?: string;
  email?: string;
  phone?: string;
  linkedin_url?: string;
  location?: string;
  source?: LeadSource;
}

export interface LeadListResponse {
  items: Lead[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

// Campaign Types
export interface Campaign {
  id: number;
  company_id: number;
  name: string;
  status: CampaignStatus;
  from_name?: string;
  from_email?: string;
  throttling_emails_per_hour: number;
  throttling_emails_per_day: number;
  total_leads: number;
  emails_sent: number;
  emails_opened: number;
  emails_clicked: number;
  emails_replied: number;
  emails_bounced: number;
  unsubscribes: number;
  created_by_id?: number;
  started_at?: string;
  completed_at?: string;
  created_at: string;
}

export enum CampaignStatus {
  DRAFT = 'draft',
  SCHEDULED = 'scheduled',
  RUNNING = 'running',
  PAUSED = 'paused',
  COMPLETED = 'completed',
  CANCELED = 'canceled'
}

export interface EmailSequence {
  id: number;
  campaign_id: number;
  step_order: number;
  subject: string;
  subject_variant?: string;
  body: string;
  body_variant?: string;
  delay_hours: number;
  emails_sent: number;
  emails_opened: number;
  emails_clicked: number;
  emails_replied: number;
  created_at: string;
}

export interface CampaignDetail extends Campaign {
  sequences: EmailSequence[];
  stats: {
    pending: number;
    sent: number;
    opened: number;
    clicked: number;
    replied: number;
    bounced: number;
    unsubscribed: number;
  };
}

export interface CampaignListResponse {
  items: Campaign[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

// Scraping Types
export interface ScrapingJob {
  id: number;
  company_id: number;
  source: LeadSource;
  status: ScrapingStatus;
  config: Record<string, any>;
  urls?: string[];
  leads_found: number;
  leads_enriched: number;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
}

export enum ScrapingStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELED = 'canceled'
}

export interface ScrapingJobListResponse {
  items: ScrapingJob[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

// Analytics Types
export interface DashboardStats {
  leads: LeadAnalytics;
  campaigns: CampaignAnalytics;
  recent_leads: Lead[];
  recent_campaigns: Campaign[];
}

export interface LeadAnalytics {
  total_leads: number;
  leads_today: number;
  leads_this_week: number;
  leads_this_month: number;
  by_source: Record<string, number>;
  by_industry: Record<string, number>;
  by_company_size: Record<string, number>;
}

export interface CampaignAnalytics {
  total_campaigns: number;
  active_campaigns: number;
  total_sent: number;
  total_opens: number;
  total_clicks: number;
  total_replies: number;
  avg_open_rate: number;
  avg_click_rate: number;
  avg_reply_rate: number;
}

// API Response Types
export interface MessageResponse {
  message: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}
