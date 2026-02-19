import { NextResponse } from 'next/server';
import { supabase } from '@/lib/supabase';

export async function GET() {
    const { data, error } = await supabase
        .from('products')
        .select('brand')
        .not('brand', 'is', null);

    if (error) {
        return NextResponse.json({ error: error.message }, { status: 500 });
    }

    // 重複を除去してソート
    const brands = Array.from(new Set(data.map(item => item.brand))).sort();

    return NextResponse.json(brands);
}
