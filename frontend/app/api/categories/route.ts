import { NextResponse } from 'next/server';
import { supabase } from '@/lib/supabase';

export async function GET() {
    const { data, error } = await supabase
        .from('products')
        .select('category')
        .not('category', 'is', null);

    if (error) {
        return NextResponse.json({ error: error.message }, { status: 500 });
    }

    // 重複を除去してソート
    const categories = Array.from(new Set(data.map(item => item.category))).sort();

    return NextResponse.json(categories);
}
