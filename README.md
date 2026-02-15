LeadForge - SmartLead.ai Alternative You Own
=============================================

A multi-tenant lead generation SaaS platform built for Blok Blok Studio. Sell this platform to your clients as a white-label solution.

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+

### Development Setup

```bash
# Clone and enter directory
cd leadforge-saas

# Start infrastructure
docker-compose up -d postgres redis

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your settings
uvicorn app.main:app --reload

# Frontend setup
cd frontend
npm install
npm run dev
```

### Production Deployment

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js 14)                    │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────────┐   │
│  │Dashboard│ │  Leads  │ │Campaigns│ │   Analytics     │   │
│  └─────────┘ └─────────┘ └─────────┘ └─────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API
┌────────────────────────▼────────────────────────────────────┐
│                   Backend (FastAPI)                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    API Routes                         │  │
│  │  /auth  /companies  /leads  /campaigns  /analytics   │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐  │
│  │  Celery     │ │  Scrapy     │ │  Email Services      │  │
│  │  Workers    │ │  Spiders    │ │  (Verification)      │  │
│  └─────────────┘ └─────────────┘ └─────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    Infrastructure                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────────────┐   │
│  │PostgreSQL│ │  Redis   │ │  External APIs            │   │
│  │(Multitenant)│        │ │  (Hunter, Clearbit, etc)  │   │
│  └──────────┘ └──────────┘ └──────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
leadforge-saas/
├── backend/
│   ├── app/
│   │   ├── api/              # API endpoints
│   │   │   ├── auth.py       # Authentication routes
│   │   │   ├── companies.py  # Company/tenant management
│   │   │   ├── leads.py      # Lead CRUD & enrichment
│   │   │   ├── campaigns.py  # Campaign management
│   │   │   ├── analytics.py  # Analytics & reporting
│   │   │   └── scraping.py   # Scraping job management
│   │   ├── core/             # Core configuration
│   │   │   ├── config.py     # Settings & environment
│   │   │   ├── security.py   # JWT, passwords, encryption
│   │   │   └── tenant.py     # Multi-tenant middleware
│   │   ├── models/           # SQLAlchemy models
│   │   │   ├── company.py    # Company, users, settings
│   │   │   ├── lead.py       # Leads, jobs, enrichment
│   │   │   └── campaign.py   # Campaigns, sequences, tracking
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   │   ├── enrichment.py # Lead enrichment
│   │   │   ├── verification.py # Email verification
│   │   │   ├── email.py      # Email sending
│   │   │   └── scraping.py   # Scraping orchestration
│   │   ├── workers/          # Celery tasks
│   │   └── main.py           # FastAPI app factory
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/
│   │   ├── (auth)/           # Auth pages (login, register)
│   │   ├── dashboard/        # Main dashboard
│   │   ├── leads/           # Lead management
│   │   ├── campaigns/        # Campaign builder
│   │   ├── analytics/        # Analytics dashboard
│   │   └── settings/         # Company settings
│   ├── components/
│   │   ├── ui/               # Reusable UI components
│   │   ├── forms/            # Form components
│   │   └── charts/           # Analytics charts
│   └── lib/                  # Utilities & API client
├── docker-compose.yml
├── docker-compose.prod.yml
└── README.md
```

## 🎯 Features

### Lead Discovery
- **LinkedIn Sales Navigator** - Extract leads from LinkedIn searches
- **Instagram Business** - Find business accounts and contact info
- **Google Maps** - Local business discovery with radius filtering
- **Custom URLs** - Import leads from any URL list
- **Advanced Filters** - Industry, location, company size, job titles

### Lead Enrichment
- **Clearbit Integration** - Company & contact data
- **Hunter.io** - Email finder & verification
- **Website Scraping** - Extract company info from websites
- **Social Discovery** - Find LinkedIn, Twitter, Facebook profiles
- **Tech Stack Detection** - BuiltWith API integration

### Email Verification
- **Hunter.io Verification** - Check email deliverability
- **NeverBounce** - Professional verification
- **Catch-all Detection** - Identify catch-all domains
- **Role-based Detection** - Filter generic emails (sales@, info@)
- **Scoring System** - Valid, Risky, Invalid categories

### Campaign Management
- **Sequence Builder** - Create 3-5 step email sequences
- **Personalization** - Use {{first_name}}, {{company}}, etc.
- **A/B Testing** - Test subject lines and email content
- **Smart Scheduling** - Send at optimal times
- **Throttling** - Control email velocity to avoid spam

### Analytics
- **Lead Generation** - Track leads by source, time period
- **Campaign Performance** - Opens, clicks, replies, bounces
- **Revenue Attribution** - Connect leads to revenue
- **Team Activity** - Monitor user actions
- **Cost per Lead** - Calculate acquisition costs

## 💰 Pricing (Sell to Your Clients)

| Tier | Monthly | Leads | Users | Features |
|------|---------|-------|-------|----------|
| **Starter** | $99 | 500/mo | 1 | Basic scrapers |
| **Growth** | $299 | 5,000/mo | 5 | All scrapers, enrichment |
| **Scale** | $799 | 25,000/mo | Unlimited | API access, priority |
| **Enterprise** | Custom | Unlimited | Unlimited | Dedicated IP, SLA |

### Client Onboarding Package
- **Setup Fee**: $2,000 - $5,000
- **Monthly Retainer**: $500 - $1,000
- **Includes**: Lead generation setup + Email campaigns

## 🔐 Multi-Tenant Security

- **Row-Level Security**: PostgreSQL RLS ensures data isolation
- **JWT Authentication**: Secure, stateless sessions
- **Role-Based Access**: Admin, Sales, Viewer roles
- **White-Label Ready**: Custom branding per company
- **API Keys**: Per-company API access for Scale+ plans

## 📦 Database Schema

### Core Tables
```sql
-- Companies (tenants)
companies (id, name, slug, plan, billing_email, created_at)

-- Company Settings
company_settings (company_id, branding, limits, features)

-- Users
users (id, company_id, email, role, name, password_hash)

-- Lead Discovery
scraping_jobs (id, company_id, source, config, status, leads_found)
leads (id, company_id, source_job_id, name, title, company, 
       email, email_status, phone, linkedin, enrichment_data)

-- Campaigns
campaigns (id, company_id, name, status, from_email)
email_sequences (id, campaign_id, step_order, subject, body)
campaign_leads (campaign_id, lead_id, status, sent_at, opened_at, clicked_at)

-- Analytics
daily_stats (company_id, date, leads_added, emails_sent, opens, clicks, replies)
```

## 🔧 Environment Variables

### Backend (.env)
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/leadforge
REDIS_URL=redis://localhost:6379

# JWT
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# External APIs (get free tiers)
CLEARBIT_KEY=your-clearbit-key
HUNTER_KEY=your-hunter-key
NEVERBOUNCE_KEY=your-neverbounce-key

# Email (SMTP or API)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-email
SMTP_PASSWORD=your-password

# Scraping
LINKEDIN_COOKIE=your-cookie
```

## 🚢 Deployment

### Railway/Render (Backend)
1. Connect GitHub repository
2. Set environment variables
3. Deploy from Dockerfile

### Vercel (Frontend)
1. Connect GitHub repository
2. Set `NEXT_PUBLIC_API_URL` env var
3. Deploy automatically

### Cloudflare
- Use Cloudflare Workers for proxy
- Enable WAF rules
- Configure DNS

## 📊 Monitoring

- **Health Check**: GET /health
- **Metrics**: Prometheus compatible
- **Logs**: Structured JSON, sent to your logger
- **Errors**: Sentry integration ready

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest --cov=app

# Frontend tests
cd frontend
npm run test
```

## 📝 License

Proprietary - Blok Blok Studio

## 💼 Sales Deck

See `docs/sales-deck.md` for client presentation template.

---

Built with ❤️ for Blok Blok Studio
