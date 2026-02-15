# Vercel + PostgreSQL Setup for LeadForge

## Option 1: Vercel Postgres (Recommended)

### Step 1: Install Vercel Postgres

```bash
cd /Users/cortana/.openclaw/workspace/projects/leadforge-saas/frontend
npm install @vercel/postgres
```

### Step 2: Create Database Schema

Create `frontend/lib/db/schema.sql`:

```sql
-- Companies (multi-tenant)
CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    plan VARCHAR(50) DEFAULT 'starter',
    billing_email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'member',
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Leads
CREATE TABLE leads (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    name VARCHAR(255),
    title VARCHAR(255),
    company VARCHAR(255),
    email VARCHAR(255),
    email_status VARCHAR(50) DEFAULT 'unverified',
    phone VARCHAR(50),
    linkedin VARCHAR(500),
    website VARCHAR(500),
    industry VARCHAR(100),
    company_size VARCHAR(50),
    location VARCHAR(255),
    source VARCHAR(100),
    status VARCHAR(50) DEFAULT 'new',
    score INTEGER DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Campaigns
CREATE TABLE campaigns (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'draft',
    from_name VARCHAR(255),
    from_email VARCHAR(255),
    subject_template TEXT,
    body_template TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Campaign Leads (junction)
CREATE TABLE campaign_leads (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES campaigns(id),
    lead_id INTEGER REFERENCES leads(id),
    status VARCHAR(50) DEFAULT 'pending',
    sent_at TIMESTAMP,
    opened_at TIMESTAMP,
    clicked_at TIMESTAMP,
    replied_at TIMESTAMP,
    UNIQUE(campaign_id, lead_id)
);

-- Email Sequences
CREATE TABLE email_sequences (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES campaigns(id),
    step_order INTEGER NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    delay_hours INTEGER DEFAULT 24,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scraping Jobs
CREATE TABLE scraping_jobs (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    source VARCHAR(100) NOT NULL,
    query TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    leads_found INTEGER DEFAULT 0,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Activity Log
CREATE TABLE activities (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_leads_company ON leads(company_id);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_email ON leads(email);
CREATE INDEX idx_campaigns_company ON campaigns(company_id);
CREATE INDEX idx_activities_company ON activities(company_id);
```

### Step 3: Database Connection

Create `frontend/lib/db/index.ts`:

```typescript
import { sql } from '@vercel/postgres';
import { drizzle } from 'drizzle-orm/vercel-postgres';

// For server components and API routes
export const db = drizzle(sql);

// Raw SQL helper
export { sql };
```

### Step 4: Environment Variables

Create `frontend/.env.local`:

```
# Vercel Postgres
POSTGRES_URL="your-vercel-postgres-url"
POSTGRES_PRISMA_URL="your-vercel-postgres-prisma-url"
POSTGRES_URL_NON_POOLING="your-vercel-postgres-non-pooling-url"
POSTGRES_USER="your-user"
POSTGRES_HOST="your-host"
POSTGRES_PASSWORD="your-password"
POSTGRES_DATABASE="your-database"

# App
NEXT_PUBLIC_APP_URL="http://localhost:3000"
JWT_SECRET="your-jwt-secret-here"
```

### Step 5: Deploy to Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
vercel --prod
```

## Option 2: Local PostgreSQL (Development)

```bash
# Install PostgreSQL
brew install postgresql@14

# Start PostgreSQL
brew services start postgresql@14

# Create database
createdb leadforge

# Run schema
psql leadforge < schema.sql
```

## Database Migrations

Using Drizzle ORM:

```bash
# Generate migration
npx drizzle-kit generate

# Push to database
npx drizzle-kit push
```

## API Routes with Database

Example: `frontend/app/api/leads/route.ts`

```typescript
import { NextResponse } from 'next/server';
import { sql } from '@vercel/postgres';

export async function GET() {
  try {
    const leads = await sql`SELECT * FROM leads LIMIT 100`;
    return NextResponse.json({ leads: leads.rows });
  } catch (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const result = await sql`
      INSERT INTO leads (name, email, company, title)
      VALUES (${body.name}, ${body.email}, ${body.company}, ${body.title})
      RETURNING *
    `;
    return NextResponse.json({ lead: result.rows[0] });
  } catch (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
```

## Next Steps

1. Set up Vercel Postgres in dashboard
2. Copy connection strings to .env.local
3. Run schema.sql to create tables
4. Test API endpoints
5. Deploy to Vercel
