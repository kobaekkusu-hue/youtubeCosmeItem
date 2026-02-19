import { NextResponse } from 'next/server';
import { getSupabaseServer } from '@/lib/supabase';

export async function GET() {
    const supabase = getSupabaseServer();
    const { data, error } = await supabase
        .from('products')
        .select('category');

    if (error) {
        console.error('Supabase Error (categories):', error);
        return NextResponse.json({ error: error.message }, { status: 500 });
    }

    const categories = Array.from(new Set(data.map(p => p.category))).filter(Boolean);
    return NextResponse.json(categories);
}
