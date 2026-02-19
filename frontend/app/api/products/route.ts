import { NextRequest, NextResponse } from 'next/server';
import { getSupabaseServer } from '@/lib/supabase';

export async function GET(request: NextRequest) {
    const { searchParams } = request.nextUrl;
    const query = searchParams.get('q');
    const category = searchParams.get('category');
    const brand = searchParams.get('brand');
    const channel = searchParams.get('channel');

    console.log(`DEBUG: Products API called with q=${query}, cat=${category}, brand=${brand}, channel=${channel}`);

    const supabase = getSupabaseServer();

    // 1. チャンネルフィルターがある場合、そのチャンネルの動画に関連する商品IDを取得
    let filteredProductIds: string[] | null = null;
    if (channel) {
        // reviews と videos を join して商品IDを抽出
        const { data: channelReviews, error: channelError } = await supabase
            .from('reviews')
            .select('product_id, videos!inner(channel_name)')
            .eq('videos.channel_name', channel);

        if (channelError) {
            console.error('Supabase Error (channel filtering):', channelError);
        } else {
            filteredProductIds = Array.from(new Set((channelReviews || []).map(r => r.product_id)));
        }
    }

    // 2. メインのクエリ構築
    let dbQuery = supabase
        .from('products')
        .select('*');

    if (query) {
        dbQuery = dbQuery.or(`name.ilike.%${query}%,brand.ilike.%${query}%,description.ilike.%${query}%`);
    }
    if (category) {
        dbQuery = dbQuery.eq('category', category);
    }
    if (brand) {
        dbQuery = dbQuery.eq('brand', brand);
    }
    if (filteredProductIds !== null) {
        if (filteredProductIds.length > 0) {
            dbQuery = dbQuery.in('id', filteredProductIds);
        } else {
            // 該当する商品がない場合は空配列を返すためのダミーフィルター
            dbQuery = dbQuery.eq('id', 'non-existent-id');
        }
    }

    const { data, error } = await dbQuery.order('created_at', { ascending: false });

    if (error) {
        console.error('Supabase Error (products):', error);
        return NextResponse.json({ error: error.message }, { status: 500 });
    }

    // 3. レビュー数を取得
    const { data: allReviews, error: reviewError } = await supabase.from('reviews').select('product_id');

    if (reviewError) {
        console.error('Supabase Error (reviews count):', reviewError);
    }

    const reviewCounts = (allReviews || []).reduce((acc: any, r: any) => {
        acc[r.product_id] = (acc[r.product_id] || 0) + 1;
        return acc;
    }, {});

    const productsWithStats = (data || []).map(p => ({
        ...p,
        review_count: reviewCounts[p.id] || 0,
        positive_rate: 100
    }));

    return NextResponse.json(productsWithStats);
}
