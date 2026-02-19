import { NextRequest, NextResponse } from 'next/server';
import { supabase } from '@/lib/supabase';

export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    const { id } = await params;

    // 商品情報を取得
    const { data: product, error: productError } = await supabase
        .from('products')
        .select('*')
        .eq('id', id)
        .single();

    if (productError) {
        return NextResponse.json({ error: productError.message }, { status: 500 });
    }

    // 関連レビューとビデオ情報を取得 (inner join)
    const { data: reviews, error: reviewsError } = await supabase
        .from('reviews')
        .select(`
      id,
      video_id,
      timestamp_seconds,
      sentiment,
      summary,
      created_at,
      videos (
        title,
        channel_name,
        thumbnail_url
      )
    `)
        .eq('product_id', id)
        .order('timestamp_seconds', { ascending: true });

    if (reviewsError) {
        return NextResponse.json({ error: reviewsError.message }, { status: 500 });
    }

    // フロントエンドの期待する形式（フラットな構造）に変換
    const flattenedReviews = (reviews || []).map((r: any) => ({
        id: r.id,
        video_id: r.video_id,
        timestamp_seconds: r.timestamp_seconds,
        sentiment: r.sentiment,
        summary: r.summary,
        video_title: r.videos?.title || 'Unknown Title',
        video_thumbnail: r.videos?.thumbnail_url || '',
        channel_name: r.videos?.channel_name || 'Unknown Channel',
        created_at: r.created_at
    }));

    const positiveReviews = flattenedReviews.filter(r => r.sentiment === 'positive').length;
    const positive_rate = flattenedReviews.length > 0 ? Math.round((positiveReviews / flattenedReviews.length) * 100) : 0;

    return NextResponse.json({
        ...product,
        reviews: flattenedReviews,
        review_count: flattenedReviews.length,
        positive_rate
    });
}
