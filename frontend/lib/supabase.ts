import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY || '';

// クライアントサイド用（Anon）
export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// サーバーサイド用（Service Role - RLSをバイパス）
// SUPABASE_SERVICE_ROLE_KEY が設定されている場合のみ作成
export const getSupabaseServer = () => {
    if (!supabaseServiceKey) {
        console.warn('SUPABASE_SERVICE_ROLE_KEY is not defined. Falling back to Anon key.');
        return supabase;
    }
    return createClient(supabaseUrl, supabaseServiceKey, {
        auth: {
            autoRefreshToken: false,
            persistSession: false
        }
    });
};
