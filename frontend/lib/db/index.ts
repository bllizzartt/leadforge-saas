import { sql } from '@vercel/postgres';
import { drizzle } from 'drizzle-orm/vercel-postgres';

// Database connection for server components and API routes
export const db = drizzle(sql);

// Raw SQL for custom queries
export { sql };

// Helper function for transactions
export async function withTransaction<T>(
  callback: (db: typeof db) => Promise<T>
): Promise<T> {
  try {
    return await callback(db);
  } catch (error) {
    console.error('Database error:', error);
    throw error;
  }
}
