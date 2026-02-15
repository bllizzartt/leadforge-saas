#!/bin/bash
# Setup script for LeadForge on Vercel

echo "🚀 Setting up LeadForge for Vercel + PostgreSQL"
echo "================================================"

cd /Users/cortana/.openclaw/workspace/projects/leadforge-saas/frontend

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "Installing Vercel CLI..."
    npm i -g vercel
fi

echo ""
echo "✅ Dependencies installed!"
echo ""
echo "Next steps:"
echo "1. Run 'vercel login' to authenticate"
echo "2. Run 'vercel --prod' to deploy"
echo "3. Add PostgreSQL in Vercel Dashboard"
echo "4. Copy env vars from Vercel to .env.local"
echo "5. Run database schema.sql"
echo ""
echo "📖 Full guide: DATABASE_SETUP.md"
