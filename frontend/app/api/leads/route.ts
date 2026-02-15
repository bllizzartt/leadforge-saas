import { NextResponse } from 'next/server';
import { sql } from '@/lib/db';

// GET /api/leads - List all leads
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const limit = parseInt(searchParams.get('limit') || '100');
    const status = searchParams.get('status');
    
    let query = sql`SELECT * FROM leads`;
    
    if (status) {
      query = sql`SELECT * FROM leads WHERE status = ${status} LIMIT ${limit}`;
    } else {
      query = sql`SELECT * FROM leads LIMIT ${limit}`;
    }
    
    const result = await query;
    
    return NextResponse.json({ 
      success: true, 
      leads: result.rows,
      count: result.rowCount 
    });
  } catch (error) {
    console.error('Error fetching leads:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to fetch leads' },
      { status: 500 }
    );
  }
}

// POST /api/leads - Create new lead
export async function POST(request: Request) {
  try {
    const body = await request.json();
    
    const result = await sql`
      INSERT INTO leads (name, email, company, title, source, status)
      VALUES (${body.name}, ${body.email}, ${body.company}, ${body.title}, ${body.source || 'manual'}, 'new')
      RETURNING *
    `;
    
    return NextResponse.json({ 
      success: true, 
      lead: result.rows[0] 
    });
  } catch (error) {
    console.error('Error creating lead:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to create lead' },
      { status: 500 }
    );
  }
}
