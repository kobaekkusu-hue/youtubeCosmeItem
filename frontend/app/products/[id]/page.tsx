'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useParams, useSearchParams } from 'next/navigation';
import { Loader2, ThumbsUp, ThumbsDown, Minus, ArrowLeft, ExternalLink, Play, Star, ShoppingBag, Beaker, Info } from 'lucide-react';
import Link from 'next/link';

const API_BASE = 'http://localhost:8000';

interface Review {
    id: string;
    video_id: string;
    timestamp_seconds: number;
    sentiment: string;
    summary: string;
    video_title: string;
    video_thumbnail: string;
    channel_name: string;
    created_at: string;
}

interface ProductDetail {
    id: string;
    name: string;
    brand: string;
    category: string;
    image_url: string;
    description: string;
    price: string;
    ingredients: string;
    volume: string;
    how_to_use: string;
    features: string;
    amazon_url: string;
    cosme_url: string;
    cosme_rating: number;
    review_count: number;
    positive_rate: number;
    reviews: Review[];
    thumbnail_url?: string;
}

export default function ProductDetailPage() {
    return (
        <Suspense fallback={
            <div className="flex items-center justify-center min-h-screen">
                <Loader2 className="animate-spin h-8 w-8 text-violet-400" />
            </div>
        }>
            <ProductDetailContent />
        </Suspense>
    );
}

function ProductDetailContent() {
    const params = useParams();
    const searchParams = useSearchParams();
    const id = params.id as string;
    const [product, setProduct] = useState<ProductDetail | null>(null);
    const [loading, setLoading] = useState(true);
    const [playingVideo, setPlayingVideo] = useState<{ videoId: string; timestamp: number } | null>(null);
    const [activeTab, setActiveTab] = useState<'overview' | 'ingredients' | 'reviews'>('overview');

    const backURL = (() => {
        const p = new URLSearchParams();
        ['q', 'category', 'brand'].forEach(k => { const v = searchParams.get(k); if (v) p.set(k, v); });
        return p.toString() ? `/?${p.toString()}` : '/';
    })();

    useEffect(() => {
        if (!id) return;
        (async () => {
            try {
                const res = await fetch(`${API_BASE}/products/${id}`);
                if (res.ok) setProduct(await res.json());
            } catch (e) { console.error(e); }
            finally { setLoading(false); }
        })();
    }, [id]);

    if (loading) return (
        <div className="flex items-center justify-center min-h-screen">
            <Loader2 className="animate-spin h-8 w-8 text-violet-400" />
        </div>
    );

    if (!product) return (
        <div className="text-center py-32 min-h-screen flex flex-col items-center justify-center">
            <p className="text-lg text-gray-300 font-light mb-4">商品が見つかりません</p>
            <Link href={backURL} className="text-violet-500 hover:text-violet-600 text-sm transition-colors">← 検索結果に戻る</Link>
        </div>
    );

    // レビューをチャンネルごとにグループ化
    const groupedReviews = product.reviews.reduce((acc, r) => {
        const key = r.video_id;
        if (!acc[key]) acc[key] = { channel: r.channel_name, title: r.video_title, thumbnail: r.video_thumbnail, videoId: r.video_id, reviews: [] };
        acc[key].reviews.push(r);
        return acc;
    }, {} as Record<string, { channel: string; title: string; thumbnail: string; videoId: string; reviews: Review[] }>);

    // features のパース
    let featuresList: string[] = [];
    if (product.features) {
        try { featuresList = JSON.parse(product.features); } catch { featuresList = []; }
    }

    return (
        <div className="min-h-screen bg-[#fafafa]">
            {/* ナビゲーション */}
            <nav className="bg-white/80 backdrop-blur-md border-b border-gray-100 sticky top-0 z-50">
                <div className="max-w-6xl mx-auto px-4 sm:px-6 py-3">
                    <Link href={backURL} className="inline-flex items-center gap-2 text-sm text-gray-400 hover:text-violet-600 transition-colors group">
                        <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
                        検索結果に戻る
                    </Link>
                </div>
            </nav>

            <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8 sm:py-12">
                {/* 商品メインセクション */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 mb-16">
                    {/* 左: 商品画像 */}
                    <div className="flex items-start justify-center">
                        <div className="bg-white rounded-3xl p-6 sm:p-8 w-full aspect-square flex items-center justify-center border border-gray-100 shadow-sm lg:sticky lg:top-24">
                            {product.image_url && product.image_url !== '' ? (
                                <img src={product.image_url} alt={product.name} className="max-w-full max-h-full object-contain" />
                            ) : product.thumbnail_url ? (
                                <img src={product.thumbnail_url} alt={product.name} className="max-w-full max-h-full object-cover rounded-2xl" />
                            ) : (
                                <span className="text-gray-200 text-sm tracking-widest">NO IMAGE</span>
                            )}
                        </div>
                    </div>

                    {/* 右: 商品情報 */}
                    <div className="space-y-8">
                        {/* 基本情報 */}
                        <div className="space-y-3">
                            {product.brand && (
                                <p className="text-sm text-violet-500 font-medium">{product.brand}</p>
                            )}
                            <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 leading-tight tracking-tight">
                                {product.name}
                            </h1>
                            <div className="flex items-center gap-3 flex-wrap">
                                {product.category && (
                                    <span className="text-xs bg-gray-100 text-gray-500 px-3 py-1 rounded-full">{product.category}</span>
                                )}
                                {product.volume && (
                                    <span className="text-xs bg-gray-100 text-gray-500 px-3 py-1 rounded-full">{product.volume}</span>
                                )}
                            </div>
                        </div>

                        {/* 価格 */}
                        {product.price && (
                            <div className="flex items-baseline gap-2">
                                <p className="text-3xl font-bold text-gray-900">{product.price}</p>
                            </div>
                        )}

                        {/* 評価 */}
                        <div className="grid grid-cols-3 gap-3">
                            <div className="stat-card p-4 text-center">
                                <p className="text-[10px] text-gray-400 mb-1">YouTubeレビュー</p>
                                <p className="text-2xl font-bold text-gray-800">{product.review_count}</p>
                            </div>
                            <div className={`stat-card p-4 text-center ${product.positive_rate >= 70 ? 'bg-emerald-50 border-emerald-100' : ''}`}>
                                <p className="text-[10px] text-gray-400 mb-1">好評率</p>
                                <p className={`text-2xl font-bold ${product.positive_rate >= 70 ? 'text-emerald-500' : 'text-gray-800'}`}>
                                    {product.positive_rate}%
                                </p>
                            </div>
                            {product.cosme_rating && (
                                <div className="stat-card p-4 text-center bg-orange-50 border-orange-100">
                                    <p className="text-[10px] text-gray-400 mb-1 flex items-center justify-center gap-1">
                                        <Star className="w-3 h-3 text-orange-400 fill-orange-400" /> @cosme
                                    </p>
                                    <p className="text-2xl font-bold text-orange-500">{product.cosme_rating}</p>
                                </div>
                            )}
                        </div>

                        {/* 商品説明 */}
                        {product.description && (
                            <div className="space-y-2">
                                <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-1.5">
                                    <Info className="w-4 h-4 text-violet-400" /> 商品説明
                                </h3>
                                <p className="text-sm text-gray-500 leading-relaxed">{product.description}</p>
                            </div>
                        )}

                        {/* 特徴 */}
                        {featuresList.length > 0 && (
                            <div className="space-y-2">
                                <h3 className="text-sm font-semibold text-gray-700">特徴</h3>
                                <ul className="space-y-1.5">
                                    {featuresList.slice(0, 5).map((f, i) => (
                                        <li key={i} className="flex items-start gap-2 text-sm text-gray-500">
                                            <span className="text-violet-400 mt-0.5 shrink-0">•</span>
                                            <span className="leading-relaxed">{f}</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {/* 使い方 */}
                        {product.how_to_use && (
                            <div className="space-y-2">
                                <h3 className="text-sm font-semibold text-gray-700">使い方</h3>
                                <p className="text-sm text-gray-500 leading-relaxed bg-violet-50/50 p-4 rounded-xl border border-violet-100/50">
                                    {product.how_to_use}
                                </p>
                            </div>
                        )}

                        {/* 外部リンク */}
                        <div className="flex gap-3 pt-2">
                            {product.amazon_url && (
                                <a href={product.amazon_url} target="_blank" rel="noopener noreferrer"
                                    className="flex items-center gap-2 px-4 py-2.5 bg-[#FF9900]/10 text-[#c77a00] rounded-xl text-sm font-medium hover:bg-[#FF9900]/20 transition-colors border border-[#FF9900]/20">
                                    <ShoppingBag className="w-4 h-4" /> Amazonで見る <ExternalLink className="w-3 h-3" />
                                </a>
                            )}
                            {product.cosme_url && (
                                <a href={product.cosme_url} target="_blank" rel="noopener noreferrer"
                                    className="flex items-center gap-2 px-4 py-2.5 bg-rose-50 text-rose-500 rounded-xl text-sm font-medium hover:bg-rose-100 transition-colors border border-rose-100">
                                    <Star className="w-4 h-4" /> @cosmeで見る <ExternalLink className="w-3 h-3" />
                                </a>
                            )}
                        </div>
                    </div>
                </div>

                {/* タブナビゲーション */}
                <div className="border-b border-gray-200 mb-8">
                    <div className="flex gap-8">
                        {[
                            { key: 'overview', label: '概要' },
                            { key: 'ingredients', label: '成分', show: !!product.ingredients },
                            { key: 'reviews', label: `動画レビュー (${product.review_count})` },
                        ].filter(t => t.show !== false).map(tab => (
                            <button
                                key={tab.key}
                                onClick={() => setActiveTab(tab.key as typeof activeTab)}
                                className={`pb-3 text-sm font-medium border-b-2 transition-colors ${activeTab === tab.key
                                    ? 'border-violet-500 text-violet-600'
                                    : 'border-transparent text-gray-400 hover:text-gray-600'
                                    }`}
                            >
                                {tab.label}
                            </button>
                        ))}
                    </div>
                </div>

                {/* 動画プレイヤー */}
                {playingVideo && (
                    <div className="mb-10 animate-fade-in-up">
                        <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden shadow-sm">
                            <div className="aspect-video">
                                <iframe
                                    src={`https://www.youtube.com/embed/${playingVideo.videoId}?start=${playingVideo.timestamp}&autoplay=1&rel=0`}
                                    title="YouTube video"
                                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                    allowFullScreen
                                    className="w-full h-full border-0"
                                ></iframe>
                            </div>
                        </div>
                        <button onClick={() => setPlayingVideo(null)} className="mt-2 text-sm text-gray-400 hover:text-gray-600 transition-colors">
                            × プレイヤーを閉じる
                        </button>
                    </div>
                )}

                {/* タブコンテンツ */}
                {activeTab === 'overview' && (
                    <div className="space-y-8 animate-fade-in-up">
                        {/* 特徴の詳細表示 */}
                        {featuresList.length > 0 && (
                            <div className="bg-white rounded-2xl border border-gray-100 p-8">
                                <h2 className="text-lg font-bold text-gray-800 mb-4">商品の特徴</h2>
                                <ul className="space-y-3">
                                    {featuresList.map((f, i) => (
                                        <li key={i} className="flex items-start gap-3 text-sm text-gray-600">
                                            <span className="w-6 h-6 rounded-full bg-violet-100 text-violet-500 flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">{i + 1}</span>
                                            <span className="leading-relaxed">{f}</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {/* 使い方の詳細 */}
                        {product.how_to_use && (
                            <div className="bg-white rounded-2xl border border-gray-100 p-8">
                                <h2 className="text-lg font-bold text-gray-800 mb-4">使い方</h2>
                                <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-line">{product.how_to_use}</p>
                            </div>
                        )}

                        {/* 何もない場合はレビューへ誘導 */}
                        {!featuresList.length && !product.how_to_use && (
                            <div className="text-center py-12">
                                <p className="text-gray-300 text-sm">概要情報はまだ登録されていません</p>
                                <button onClick={() => setActiveTab('reviews')} className="mt-3 text-violet-500 text-sm hover:text-violet-600">
                                    動画レビューを見る →
                                </button>
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'ingredients' && product.ingredients && (
                    <div className="animate-fade-in-up">
                        <div className="bg-white rounded-2xl border border-gray-100 p-8">
                            <h2 className="text-lg font-bold text-gray-800 mb-2 flex items-center gap-2">
                                <Beaker className="w-5 h-5 text-violet-400" /> 全成分表示
                            </h2>
                            <p className="text-xs text-gray-400 mb-6">成分は配合量の多い順に記載されています</p>
                            <p className="text-sm text-gray-600 leading-loose">{product.ingredients}</p>
                        </div>
                    </div>
                )}

                {activeTab === 'reviews' && (
                    <div className="space-y-4 animate-fade-in-up">
                        {Object.values(groupedReviews).map((group) => (
                            <div key={group.videoId} className="review-card p-6">
                                <div className="flex items-start gap-4 mb-4">
                                    <div className="relative shrink-0 cursor-pointer group" onClick={() => setPlayingVideo({ videoId: group.videoId, timestamp: group.reviews[0].timestamp_seconds })}>
                                        <img src={group.thumbnail} alt="" className="w-36 h-20 object-cover rounded-lg bg-gray-100" />
                                        <div className="absolute inset-0 bg-black/30 rounded-lg flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                                            <Play className="w-8 h-8 text-white fill-white" />
                                        </div>
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-xs text-gray-400 mb-0.5">{group.channel}</p>
                                        <p className="text-sm font-medium text-gray-800 line-clamp-2 leading-snug">{group.title}</p>
                                        <a href={`https://www.youtube.com/watch?v=${group.videoId}`} target="_blank" rel="noopener noreferrer"
                                            className="inline-flex items-center gap-1 text-[10px] text-violet-400 hover:text-violet-600 mt-1.5 transition-colors">
                                            YouTubeで見る <ExternalLink className="w-3 h-3" />
                                        </a>
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    {group.reviews.map(review => (
                                        <div key={review.id}
                                            className="flex items-start gap-3 py-3 border-t border-gray-50 first:border-t-0 cursor-pointer hover:bg-gray-50/50 -mx-2 px-2 rounded-lg transition-colors"
                                            onClick={() => setPlayingVideo({ videoId: review.video_id, timestamp: review.timestamp_seconds })}
                                        >
                                            <SentimentBadge sentiment={review.sentiment} />
                                            <p className="text-sm text-gray-600 leading-relaxed flex-1">{review.summary}</p>
                                            <span className="text-[10px] text-violet-400 bg-violet-50 px-2 py-0.5 rounded font-mono shrink-0 mt-0.5">
                                                {formatTimestamp(review.timestamp_seconds)}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </main>
        </div>
    );
}

function SentimentBadge({ sentiment }: { sentiment: string }) {
    if (sentiment === 'positive') return (
        <span className="inline-flex items-center gap-1 text-[10px] font-medium text-emerald-600 bg-emerald-50 px-2 py-1 rounded-full shrink-0 mt-0.5">
            <ThumbsUp className="w-3 h-3" /> 好評
        </span>
    );
    if (sentiment === 'negative') return (
        <span className="inline-flex items-center gap-1 text-[10px] font-medium text-rose-600 bg-rose-50 px-2 py-1 rounded-full shrink-0 mt-0.5">
            <ThumbsDown className="w-3 h-3" /> 不評
        </span>
    );
    return (
        <span className="inline-flex items-center gap-1 text-[10px] font-medium text-gray-400 bg-gray-50 px-2 py-1 rounded-full shrink-0 mt-0.5">
            <Minus className="w-3 h-3" /> 中立
        </span>
    );
}

function formatTimestamp(s: number) {
    return `${Math.floor(s / 60)}:${(s % 60).toString().padStart(2, '0')}`;
}
