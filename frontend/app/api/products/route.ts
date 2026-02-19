import { NextRequest, NextResponse } from 'next/server';
import { supabase } from '@/lib/supabase';

export async function GET(request: NextRequest) {
    const { searchParams } = new URL(request.url);
    const query = searchParams.get('q');
    const category = searchParams.get('category');
    const brand = searchParams.get('brand');

    let dbQuery = supabase
        .from('products')
        .select(`
      id, name, brand, category, image_url, description, price, volume, review_count, positive_rate, thumbnail_url
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

    const { data, error } = await dbQuery.order('review_count', { ascending: false });

    if (error) {
        return NextResponse.json({ error: error.message }, { status: 500 });
    }

    return NextResponse.json(data);
}
