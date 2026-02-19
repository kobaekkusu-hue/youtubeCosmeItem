import { NextResponse } from 'next/server';
import { getSupabaseServer } from '@/lib/supabase';

export async function GET() {
    const supabase = getSupabaseServer();
    const { data, error } = await supabase
        .from('products')
        .select('brand');

    if (error) {
        console.error('Supabase Error (brands):', error);
        return NextResponse.json({ error: error.message }, { status: 500 });
    }

    const brands = Array.from(new Set(data.map(p => p.brand))).filter(Boolean);
    return NextResponse.json(brands);
}
