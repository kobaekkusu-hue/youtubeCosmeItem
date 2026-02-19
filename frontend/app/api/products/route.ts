import { NextRequest, NextResponse } from 'next/server';
import { getSupabaseServer } from '@/lib/supabase';

export async function GET(request: NextRequest) {
    const { searchParams } = new URL(request.url);
    const query = searchParams.get('q');
    const category = searchParams.get('category');
    const brand = searchParams.get('brand');

    const supabase = getSupabaseServer();

    let dbQuery = supabase
        .from('products')
        .select(`
      id, name, brand, category, image_url, description, price, volume, cosme_rating, thumbnail_url
    `);

    if (query) {
        dbQuery = dbQuery.or(`name.ilike.%${query}%,brand.ilike.%${query}%,description.ilike.%${query}%`);
    }
    if (category) {
        dbQuery = dbQuery.eq('category', category);
    }
    if (brand) {
        dbQuery = dbQuery.eq('brand', brand);
    }

    const { data, error } = await dbQuery.order('created_at', { ascending: false });

    if (error) {
        console.error('Supabase Error (products):', error);
        return NextResponse.json({ error: error.message }, { status: 500 });
    }

    // レビュー数を取得
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
