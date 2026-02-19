import { NextRequest, NextResponse } from 'next/server';
import { supabase } from '@/lib/supabase';

export async function GET(
    request: NextRequest,
    { params }: { params: { id: string } }
) {
    const id = params.id;

    // 商品情報を取得
    const { data: product, error: productError } = await supabase
        .from('products')
        .select('*')
        .eq('id', id)
        .single();

    if (productError) {
        return NextResponse.json({ error: productError.message }, { status: 500 });
    }

    // 関連レビューを取得
    const { data: reviews, error: reviewsError } = await supabase
        .from('reviews')
        .select('*')
        .eq('product_id', id)
        .order('timestamp_seconds', { ascending: true });

    if (reviewsError) {
        return NextResponse.json({ error: reviewsError.message }, { status: 500 });
    }

    return NextResponse.json({ ...product, reviews });
}
