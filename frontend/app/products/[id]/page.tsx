'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useParams, useSearchParams } from 'next/navigation';
import { Loader2, ThumbsUp, ThumbsDown, Minus, ArrowLeft, ExternalLink, Play, Star, ShoppingBag, Beaker, Info, X } from 'lucide-react';
import Link from 'next/link';

const API_BASE = '/api';

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
                if (res.ok) {
                    const data = await res.json();
                    if (data && typeof data === 'object' && !data.error) {
                        setProduct(data);
                    } else {
                        console.error('Invalid product data:', data);
                        setProduct(null);
                    }
                }
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
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 mb-16">
                    {/* 左: 商品画像 */}
                    <div className="flex items-start justify-center">
                        <div className="bg-white rounded-3xl p-8 w-full aspect-square flex items-center justify-center border border-rose-100 shadow-sm lg:sticky lg:top-24 relative overflow-hidden">
                            {/* 背景装飾 */}
                            <div className="absolute top-0 left-0 w-32 h-32 bg-rose-50 rounded-full blur-3xl opacity-50 -translate-x-1/2 -translate-y-1/2 pointer-events-none"></div>
                            <div className="absolute bottom-0 right-0 w-40 h-40 bg-lime-50 rounded-full blur-3xl opacity-50 translate-x-1/3 translate-y-1/3 pointer-events-none"></div>

                            {product.image_url && product.image_url !== '' ? (
                                <img src={product.image_url} alt={product.name} className="max-w-full max-h-full object-contain relative z-10" />
                            ) : product.thumbnail_url ? (
                                <img src={product.thumbnail_url} alt={product.name} className="max-w-full max-h-full object-cover rounded-2xl relative z-10" />
                            ) : (
                                <span className="text-gray-200 text-sm tracking-widest relative z-10">NO IMAGE</span>
                            )}
                        </div>
                    </div>

                    {/* 右: 商品情報 */}
                    <div className="space-y-8">
                        {/* 基本情報 */}
                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                {product.brand && (
                                    <span className="text-sm font-bold text-rose-500 bg-rose-50 px-3 py-1 rounded-full">{product.brand}</span>
                                )}
                                <div className="flex gap-2">
                                    {product.category && <span className="text-xs text-gray-400 border border-gray-100 px-2 py-1 rounded">{product.category}</span>}
                                </div>
                            </div>

                            <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 leading-tight tracking-tight">
                                {product.name}
                            </h1>
                        </div>

                        {/* 評価対比 */}
                        <div className="grid grid-cols-2 gap-4">
                            {/* YouTube Heat */}
                            <div className="bg-white border border-rose-100 rounded-xl p-4 shadow-sm relative overflow-hidden">
                                <div className="absolute top-0 right-0 w-16 h-16 bg-rose-50 rounded-bl-full opacity-50 pointer-events-none"></div>
                                <p className="text-[10px] font-bold text-rose-400 mb-1 flex items-center gap-1 uppercase tracking-wider">
                                    <Play className="w-3 h-3 fill-rose-400" /> YouTube Heat
                                </p>
                                <div className="flex items-end gap-2">
                                    <span className="text-2xl font-bold text-gray-800">{product.review_count}</span>
                                    <span className="text-xs text-gray-400 mb-1">Reviews</span>
                                </div>
                                <p className="text-[10px] text-gray-400 mt-1">動画での話題性・熱量</p>
                            </div>

                            {/* @cosme Cool */}
                            <div className="bg-white border border-lime-100 rounded-xl p-4 shadow-sm relative overflow-hidden">
                                <div className="absolute top-0 right-0 w-16 h-16 bg-lime-50 rounded-bl-full opacity-50 pointer-events-none"></div>
                                <p className="text-[10px] font-bold text-lime-600 mb-1 flex items-center gap-1 uppercase tracking-wider">
                                    <Star className="w-3 h-3 fill-lime-500 text-lime-500" /> @cosme Spec
                                </p>
                                <div className="flex items-end gap-2">
                                    <span className="text-2xl font-bold text-gray-800">{product.positive_rate}%</span>
                                    <span className="text-xs text-gray-400 mb-1">Positive</span>
                                </div>
                                <p className="text-[10px] text-gray-400 mt-1">冷静なスペック評価</p>
                            </div>
                        </div>

                        {/* 価格 & スペック */}
                        <div className="flex items-baseline gap-4 border-b border-gray-100 pb-6">
                            {product.price && (
                                <p className="text-3xl font-bold text-gray-900">{product.price}<span className="text-sm font-normal text-gray-500 ml-1">（税込）</span></p>
                            )}
                            {product.volume && (
                                <span className="text-sm text-gray-500">{product.volume}</span>
                            )}
                        </div>

                        {/* アクションボタン (Conversion) */}
                        <div className="space-y-3 pb-4">
                            <p className="text-xs text-gray-400 text-center mb-1">＼ 30代の賢い選択 ／</p>
                            {product.amazon_url && (
                                <a href={product.amazon_url} target="_blank" rel="noopener noreferrer"
                                    className="flex items-center justify-center gap-2 w-full py-4 bg-gradient-to-r from-amber-400 to-orange-400 text-white rounded-xl text-lg font-bold shadow-lg shadow-orange-100/50 hover:shadow-orange-200 hover:-translate-y-0.5 transition-all">
                                    <ShoppingBag className="w-5 h-5" /> Amazonで今すぐ見る <ExternalLink className="w-4 h-4 opacity-70" />
                                </a>
                            )}

                            <div className="flex gap-3">
                                {product.cosme_url && (
                                    <a href={product.cosme_url} target="_blank" rel="noopener noreferrer"
                                        className="flex-1 flex items-center justify-center gap-2 py-3 bg-white border border-gray-200 text-gray-600 rounded-xl text-sm font-medium hover:bg-gray-50 transition-colors">
                                        <Star className="w-4 h-4 text-lime-500" /> @cosmeで口コミ確認
                                    </a>
                                )}
                            </div>
                        </div>

                        {/* Short Description */}
                        {product.description && (
                            <p className="text-sm text-gray-500 leading-relaxed bg-gray-50 p-4 rounded-lg">
                                {product.description}
                            </p>
                        )}
                    </div>
                </div>

                {/* タブナビゲーション */}
                <div className="border-b border-gray-200 mb-8 sticky top-[72px] bg-[#fafafa]/95 backdrop-blur z-20 pt-2">
                    <div className="flex gap-8">
                        {[
                            { key: 'reviews', label: '① 動画レビュー (YouTube Heat)', icon: Play },
                            { key: 'ingredients', label: '② 成分・詳細 (Spec Check)', icon: Beaker, show: !!product.ingredients },
                            { key: 'overview', label: '③ 概要', icon: Info },
                        ].filter(t => t.show !== false).map(tab => (
                            <button
                                key={tab.key}
                                onClick={() => setActiveTab(tab.key as typeof activeTab)}
                                className={`pb-3 text-sm font-bold border-b-2 transition-colors flex items-center gap-2 ${activeTab === tab.key
                                    ? 'border-rose-500 text-rose-600'
                                    : 'border-transparent text-gray-400 hover:text-gray-600'
                                    }`}
                            >
                                <tab.icon className={`w-4 h-4 ${activeTab === tab.key ? 'text-rose-500' : 'text-gray-400'}`} />
                                {tab.label}
                            </button>
                        ))}
                    </div>
                </div>

                {/* 動画プレイヤー */}
                {playingVideo && (
                    <div className="mb-10 animate-fade-in-up">
                        <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden shadow-lg shadow-rose-100/50">
                            <div className="aspect-video relative">
                                <iframe
                                    src={`https://www.youtube.com/embed/${playingVideo.videoId}?start=${playingVideo.timestamp}&autoplay=1&rel=0`}
                                    title="YouTube video"
                                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                    allowFullScreen
                                    className="w-full h-full border-0"
                                ></iframe>
                            </div>
                        </div>
                        <button onClick={() => setPlayingVideo(null)} className="mt-2 text-sm text-gray-400 hover:text-gray-600 transition-colors flex items-center gap-1">
                            <X className="w-4 h-4" /> プレイヤーを閉じる
                        </button>
                    </div>
                )}

                {/* タブコンテンツ */}
                <div className="min-h-[400px]">
                    {activeTab === 'overview' && (
                        <div className="space-y-8 animate-fade-in-up">
                            {/* 特徴の詳細表示 */}
                            {featuresList.length > 0 && (
                                <div className="bg-white rounded-2xl border border-rose-100 p-8 shadow-sm">
                                    <h2 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                                        <div className="w-1 h-6 bg-rose-400 rounded-full"></div> 商品の特徴
                                    </h2>
                                    <ul className="space-y-4">
                                        {featuresList.map((f, i) => (
                                            <li key={i} className="flex items-start gap-3 text-sm text-gray-600">
                                                <span className="w-6 h-6 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">{i + 1}</span>
                                                <span className="leading-relaxed">{f}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {/* 使い方の詳細 */}
                            {product.how_to_use && (
                                <div className="bg-white rounded-2xl border border-rose-100 p-8 shadow-sm">
                                    <h2 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                                        <div className="w-1 h-6 bg-rose-400 rounded-full"></div> 使い方
                                    </h2>
                                    <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-line bg-rose-50/50 p-4 rounded-xl border border-rose-100/50">
                                        {product.how_to_use}
                                    </p>
                                </div>
                            )}
                        </div>
                    )}

                    {activeTab === 'ingredients' && product.ingredients && (
                        <div className="animate-fade-in-up">
                            <div className="bg-white rounded-2xl border border-lime-100 p-8 shadow-sm">
                                <h2 className="text-lg font-bold text-gray-800 mb-2 flex items-center gap-2">
                                    <Beaker className="w-5 h-5 text-lime-500" /> 全成分表示 (Spec Check)
                                </h2>
                                <p className="text-xs text-gray-400 mb-6">成分表から、あなたの肌に合うか冷静にチェックしましょう。</p>
                                <p className="text-sm text-gray-600 leading-loose font-mono text-justify break-all">
                                    {product.ingredients}
                                </p>
                            </div>
                        </div>
                    )}

                    {activeTab === 'reviews' && (
                        <div className="space-y-6 animate-fade-in-up">
                            <p className="text-sm text-gray-500 bg-gray-50 p-3 rounded-lg flex items-center gap-2">
                                <Info className="w-4 h-4 text-rose-400" /> YouTuberたちが実際に使って感じた「熱量」のあるレビューです。
                            </p>

                            {Object.values(groupedReviews).map((group) => (
                                <div key={group.videoId} className="review-card p-6 bg-white rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition-all group-card">
                                    <div className="flex items-start gap-4 mb-4">
                                        <div className="relative shrink-0 cursor-pointer group" onClick={() => setPlayingVideo({ videoId: group.videoId, timestamp: group.reviews[0].timestamp_seconds })}>
                                            <img src={group.thumbnail} alt="" className="w-40 h-24 object-cover rounded-lg bg-gray-100 shadow-sm group-hover:shadow-md transition-all" />
                                            <div className="absolute inset-0 bg-black/20 rounded-lg flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity backdrop-blur-[1px]">
                                                <Play className="w-10 h-10 text-white fill-white drop-shadow-md" />
                                            </div>
                                            <div className="absolute bottom-1 right-1 bg-black/60 text-white text-[10px] px-1.5 py-0.5 rounded">
                                                Play
                                            </div>
                                        </div>
                                        <div className="flex-1 min-w-0 pt-1">
                                            <div className="flex items-center gap-2 mb-1">
                                                <span className="text-[10px] font-bold text-white bg-rose-500 px-2 py-0.5 rounded-full">YouTube</span>
                                                <p className="text-xs font-bold text-gray-500">{group.channel}</p>
                                            </div>
                                            <p className="text-base font-bold text-gray-800 line-clamp-2 leading-snug mb-2 group-hover:text-rose-600 transition-colors">
                                                {group.title}
                                            </p>
                                            <a href={`https://www.youtube.com/watch?v=${group.videoId}`} target="_blank" rel="noopener noreferrer"
                                                className="inline-flex items-center gap-1 text-[11px] text-gray-400 hover:text-rose-500 transition-colors">
                                                YouTube元動画を開く <ExternalLink className="w-3 h-3" />
                                            </a>
                                        </div>
                                    </div>

                                    <div className="space-y-3 bg-gray-50/50 rounded-xl p-4">
                                        {group.reviews.map(review => (
                                            <div key={review.id}
                                                className="flex items-start gap-3 cursor-pointer hover:bg-white p-2 rounded-lg transition-all"
                                                onClick={() => setPlayingVideo({ videoId: review.video_id, timestamp: review.timestamp_seconds })}
                                            >
                                                <SentimentBadge sentiment={review.sentiment} />
                                                <div className="flex-1 min-w-0">
                                                    <p className="text-sm text-gray-700 leading-relaxed font-medium">
                                                        <span className="text-rose-400 font-bold mr-1">"</span>
                                                        {review.summary}
                                                        <span className="text-rose-400 font-bold ml-1">"</span>
                                                    </p>
                                                </div>
                                                <span className="text-[10px] text-rose-500 font-mono bg-rose-50 px-1.5 py-0.5 rounded border border-rose-100 shrink-0 mt-0.5">
                                                    {formatTimestamp(review.timestamp_seconds)}
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
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
