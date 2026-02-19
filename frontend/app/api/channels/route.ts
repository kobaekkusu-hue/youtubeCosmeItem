import { NextResponse } from 'next/server';
import { getSupabaseServer } from '@/lib/supabase';

export async function GET() {
    const supabase = getSupabaseServer();
    // videos テーブルから channel_name のユニークなリストを取得
    const { data, error } = await supabase
        .from('videos')
        .select('channel_name');

    if (error) {
        console.error('Supabase Error (channels):', error);
        return NextResponse.json({ error: error.message }, { status: 500 });
    }

    // 重複を排除してソートして返す
    const channels = Array.from(new Set(data.map(v => v.channel_name))).filter(Boolean).sort();
    return NextResponse.json(channels);
}
