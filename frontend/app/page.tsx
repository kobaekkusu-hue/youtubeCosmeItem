'use client';

import React, { useState, useEffect, useCallback, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Search, Loader2, X, Star, ChevronRight, Package, Tag, ThumbsUp, Play } from 'lucide-react';
import Link from 'next/link';

const API_BASE = '/api';

interface Product {
  id: string;
  name: string;
  brand?: string;
  category?: string;
  image_url?: string;
  description?: string;
  price?: string;
  volume?: string;
  review_count: number;
  positive_rate: number;
  thumbnail_url?: string;
}

// Suspense 境界内のメインコンテンツ
function Home() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#fafafa] flex items-center justify-center"><Loader2 className="animate-spin h-8 w-8 text-violet-400" /></div>}>
      <HomeContent />
    </Suspense>
  );
}
export default Home;

function HomeContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [query, setQuery] = useState(searchParams.get('q') || '');
  const [selectedCategory, setSelectedCategory] = useState(searchParams.get('category') || '');
  const [selectedBrand, setSelectedBrand] = useState(searchParams.get('brand') || '');
  const [selectedChannel, setSelectedChannel] = useState(searchParams.get('channel') || '');
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [brands, setBrands] = useState<string[]>([]);
  const [channels, setChannels] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  // カテゴリ、ブランド、チャンネルを取得
  useEffect(() => {
    fetch(`${API_BASE}/categories`)
      .then(r => r.ok ? r.json() : [])
      .then(data => Array.isArray(data) ? setCategories(data) : setCategories([]))
      .catch(() => setCategories([]));
    fetch(`${API_BASE}/brands`)
      .then(r => r.ok ? r.json() : [])
      .then(data => Array.isArray(data) ? setBrands(data) : setBrands([]))
      .catch(() => setBrands([]));
    fetch(`${API_BASE}/channels`)
      .then(r => r.ok ? r.json() : [])
      .then(data => Array.isArray(data) ? setChannels(data) : setChannels([]))
      .catch(() => setChannels([]));
  }, []);

  // 商品検索
  const fetchProducts = useCallback(async (q: string, cat: string, br: string, ch: string) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (q) params.set('q', q);
      if (cat) params.set('category', cat);
      if (br) params.set('brand', br);
      if (ch) params.set('channel', ch);
      const res = await fetch(`${API_BASE}/products?${params.toString()}`);
      const data = await res.json();
      if (Array.isArray(data)) {
        setProducts(data);
      } else {
        setProducts([]);
        console.error('API Error:', data);
      }
    } catch (e) {
      console.error('Fetch error:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  // URL更新
  const updateURL = useCallback((q: string, cat: string, br: string, ch: string) => {
    const params = new URLSearchParams();
    if (q) params.set('q', q);
    if (cat) params.set('category', cat);
    if (br) params.set('brand', br);
    if (ch) params.set('channel', ch);
    router.replace(`/?${params.toString()}`, { scroll: false });
  }, [router]);

  // 初期ロード & フィルター変更時
  useEffect(() => {
    fetchProducts(query, selectedCategory, selectedBrand, selectedChannel);
    updateURL(query, selectedCategory, selectedBrand, selectedChannel);
  }, [selectedCategory, selectedBrand, selectedChannel]);

  // 検索ハンドラ
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchProducts(query, selectedCategory, selectedBrand, selectedChannel);
    updateURL(query, selectedCategory, selectedBrand, selectedChannel);
  };

  // フィルタークリア
  const clearFilters = () => {
    setSelectedCategory('');
    setSelectedBrand('');
    setSelectedChannel('');
    setQuery('');
    fetchProducts('', '', '', '');
    updateURL('', '', '', '');
  };

  const hasActiveFilters = query || selectedCategory || selectedBrand || selectedChannel;

  // 検索パラメータを組み立て（詳細ページの戻るリンク用）
  const buildBackParams = () => {
    const p = new URLSearchParams();
    if (query) p.set('q', query);
    if (selectedCategory) p.set('category', selectedCategory);
    if (selectedBrand) p.set('brand', selectedBrand);
    if (selectedChannel) p.set('channel', selectedChannel);
    return p.toString();
  };

  return (
    <div className="min-h-screen bg-[#fafafa]">
      {/* ===== 上部固定ヘッダー + 検索バー ===== */}
      <header className="sticky top-0 z-50 bg-white/90 backdrop-blur-md border-b border-rose-100 shadow-sm transition-all">
        <div className="max-w-[1400px] mx-auto px-4 sm:px-6">
          <div className="flex items-center h-16 gap-6">
            {/* ロゴ */}
            <Link href="/" className="shrink-0 flex flex-col justify-center">
              <div className="flex items-center gap-1">
                <span className="text-xl font-extrabold gradient-text tracking-tight">CosmeReview</span>
                <span className="text-xs font-bold text-gray-400">AI</span>
              </div>
              <span className="text-[10px] text-rose-400 font-medium tracking-wide -mt-0.5">YouTube × @cosme 徹底検証</span>
            </Link>

            {/* 検索バー */}
            <form onSubmit={handleSearch} className="flex-1 max-w-2xl hidden sm:block">
              <div className="flex items-center bg-gray-50 border border-rose-100 rounded-full px-4 py-2 focus-within:border-rose-300 focus-within:ring-2 focus-within:ring-rose-100 transition-all shadow-sm hover:shadow-md">
                <Search className="w-4 h-4 text-rose-300 mr-2 shrink-0" />
                <input
                  type="text"
                  placeholder="動画で気になったコスメを検索..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="flex-1 bg-transparent border-0 outline-none text-sm text-gray-700 placeholder:text-gray-400"
                />
                {query && (
                  <button
                    type="button"
                    onClick={() => { setQuery(''); fetchProducts('', selectedCategory, selectedBrand, selectedChannel); updateURL('', selectedCategory, selectedBrand, selectedChannel); }}
                    className="text-gray-300 hover:text-gray-500 mr-2 transition-colors"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                )}
                <button
                  id="search-button"
                  type="submit"
                  disabled={loading}
                  className="bg-rose-500 hover:bg-rose-600 text-white px-5 py-1.5 rounded-full font-medium text-xs transition-all shadow-rose-200 shadow-lg translate-y-[0px] active:translate-y-[1px]"
                >
                  {loading ? <Loader2 className="animate-spin w-3.5 h-3.5" /> : '検索'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </header>

      {/* ===== メインコンテンツ（サイドバー + 商品リスト） ===== */}
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 py-8">
        {/* モバイル用検索バー (ヘッダーから分離) */}
        <div className="sm:hidden mb-6">
          <form onSubmit={handleSearch}>
            <div className="flex items-center bg-white border border-rose-100 rounded-full px-4 py-3 shadow-sm">
              <Search className="w-5 h-5 text-rose-300 mr-2 shrink-0" />
              <input
                type="text"
                placeholder="商品名、ブランドで検索..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="flex-1 bg-transparent border-0 outline-none text-base text-gray-700 placeholder:text-gray-400"
              />
              <button
                type="submit"
                disabled={loading}
                className="bg-rose-500 text-white p-1.5 rounded-full"
              >
                <Search className="w-4 h-4" />
              </button>
            </div>
          </form>
        </div>

        {/* ヒーローメッセージ (モバイルのみ) */}
        <div className="sm:hidden mb-6 text-center">
          <h1 className="text-lg font-bold text-gray-800 mb-1">
            <span className="text-rose-500">動画</span>の熱量 × <span className="text-lime-600">@cosme</span>の冷静さ
          </h1>
          <p className="text-xs text-gray-500">30代の賢いコスメ選びをサポート</p>
        </div>


        <div className="flex gap-8">
          {/* ===== 左サイドバー ===== */}
          <aside className="w-[240px] shrink-0 hidden lg:block">
            <div className="sticky top-28 space-y-8">
              {/* アクティブフィルター */}
              {hasActiveFilters && (
                <div className="animate-fade-in-up">
                  <button
                    onClick={clearFilters}
                    className="text-xs text-rose-500 hover:text-rose-700 transition-colors flex items-center gap-1 mb-3 font-medium"
                  >
                    <X className="w-3 h-3" /> すべての条件をクリア
                  </button>
                  <div className="flex flex-wrap gap-2">
                    {query && (
                      <span className="inline-flex items-center gap-1 bg-white text-rose-600 text-[11px] px-2.5 py-1 rounded-full border border-rose-200 shadow-sm">
                        「{query}」
                        <X className="w-3 h-3 cursor-pointer hover:text-rose-800" onClick={() => { setQuery(''); fetchProducts('', selectedCategory, selectedBrand, selectedChannel); updateURL('', selectedCategory, selectedBrand, selectedChannel); }} />
                      </span>
                    )}
                    {selectedChannel && (
                      <span className="inline-flex items-center gap-1 bg-white text-rose-600 text-[11px] px-2.5 py-1 rounded-full border border-rose-200 shadow-sm">
                        {selectedChannel}
                        <X className="w-3 h-3 cursor-pointer hover:text-rose-800" onClick={() => setSelectedChannel('')} />
                      </span>
                    )}
                    {selectedCategory && (
                      <span className="inline-flex items-center gap-1 bg-white text-rose-600 text-[11px] px-2.5 py-1 rounded-full border border-rose-200 shadow-sm">
                        {selectedCategory}
                        <X className="w-3 h-3 cursor-pointer hover:text-rose-800" onClick={() => setSelectedCategory('')} />
                      </span>
                    )}
                    {selectedBrand && (
                      <span className="inline-flex items-center gap-1 bg-white text-rose-600 text-[11px] px-2.5 py-1 rounded-full border border-rose-200 shadow-sm">
                        {selectedBrand}
                        <X className="w-3 h-3 cursor-pointer hover:text-rose-800" onClick={() => setSelectedBrand('')} />
                      </span>
                    )}
                  </div>
                </div>
              )}

              {/* チャンネルフィルター */}
              <div>
                <h3 className="sidebar-heading">
                  <Play className="w-3.5 h-3.5 fill-rose-600 text-rose-600" />
                  YouTuberから探す
                </h3>
                <ul className="space-y-1 mt-2">
                  {channels.map(ch => (
                    <li key={ch}>
                      <button
                        onClick={() => setSelectedChannel(selectedChannel === ch ? '' : ch)}
                        className={`sidebar-item w-full text-left ${selectedChannel === ch ? 'active' : ''}`}
                      >
                        <ChevronRight className={`w-3 h-3 shrink-0 ${selectedChannel === ch ? 'text-rose-500' : 'text-gray-300'}`} />
                        <span className="truncate">{ch}</span>
                      </button>
                    </li>
                  ))}
                </ul>
              </div>

              {/* カテゴリフィルター */}
              <div>
                <h3 className="sidebar-heading">
                  <Tag className="w-3.5 h-3.5 text-rose-600" />
                  カテゴリから探す
                </h3>
                <ul className="space-y-1 mt-2">
                  {categories.map(cat => (
                    <li key={cat}>
                      <button
                        onClick={() => setSelectedCategory(selectedCategory === cat ? '' : cat)}
                        className={`sidebar-item w-full text-left ${selectedCategory === cat ? 'active' : ''}`}
                      >
                        <ChevronRight className={`w-3 h-3 shrink-0 ${selectedCategory === cat ? 'text-rose-500' : 'text-gray-300'}`} />
                        <span className="truncate">{cat}</span>
                      </button>
                    </li>
                  ))}
                </ul>
              </div>

              {/* ブランドフィルター */}
              <div>
                <h3 className="sidebar-heading">
                  <Package className="w-3.5 h-3.5 text-rose-600" />
                  ブランドから探す
                </h3>
                <ul className="space-y-1 mt-2">
                  {brands.map(br => (
                    <li key={br}>
                      <button
                        onClick={() => setSelectedBrand(selectedBrand === br ? '' : br)}
                        className={`sidebar-item w-full text-left ${selectedBrand === br ? 'active' : ''}`}
                      >
                        <ChevronRight className={`w-3 h-3 shrink-0 ${selectedBrand === br ? 'text-rose-500' : 'text-gray-300'}`} />
                        <span className="truncate">{br}</span>
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </aside>

          {/* ===== 商品リスト ===== */}
          <main className="flex-1 min-w-0">
            {/* 検索結果ヘッダー (PC) */}
            <div className="hidden lg:flex items-center justify-between mb-6">
              <div className="flex items-end gap-3">
                <h1 className="text-xl font-bold text-gray-800">
                  <span className="text-rose-500">動画</span>で見つけたコスメを<br /><span className="text-lime-600">@cosme</span>で賢く検証
                </h1>
              </div>
              <div className="text-right">
                <span className="text-xs text-gray-400">検索結果</span>
                <p className="text-2xl font-bold text-rose-600 leading-none">{products.length}<span className="text-sm font-normal text-gray-500 ml-1">件</span></p>
              </div>
            </div>

            {/* モバイル用フィルターバー */}
            <div className="lg:hidden mb-6 flex overflow-x-auto pb-2 gap-2 scrollbar-hide">
              <select
                value={selectedChannel}
                onChange={(e) => setSelectedChannel(e.target.value)}
                className="text-xs border border-rose-100 rounded-full px-4 py-2 bg-white text-gray-600 shadow-sm whitespace-nowrap"
              >
                <option value="">YouTuber</option>
                {channels.map(ch => (
                  <option key={ch} value={ch}>{ch}</option>
                ))}
              </select>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="text-xs border border-rose-100 rounded-full px-4 py-2 bg-white text-gray-600 shadow-sm whitespace-nowrap"
              >
                <option value="">カテゴリ</option>
                {categories.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
              <select
                value={selectedBrand}
                onChange={(e) => setSelectedBrand(e.target.value)}
                className="text-xs border border-rose-100 rounded-full px-4 py-2 bg-white text-gray-600 shadow-sm whitespace-nowrap"
              >
                <option value="">ブランド</option>
                {brands.map(br => (
                  <option key={br} value={br}>{br}</option>
                ))}
              </select>
            </div>

            {/* ローディング */}
            {loading && products.length === 0 ? (
              <div className="text-center py-32">
                <Loader2 className="animate-spin h-10 w-10 mx-auto text-rose-300 mb-4" />
                <p className="text-gray-400 text-sm font-medium">トレンドコスメを検索中...</p>
              </div>
            ) : (
              /* 商品リスト（カード） */
              <div className="space-y-4">
                {products.map((product, i) => (
                  <Link
                    key={product.id}
                    href={`/products/${product.id}${buildBackParams() ? '?' + buildBackParams() : ''}`}
                    className="block group"
                  >
                    <div className="product-list-card animate-fade-in-up" style={{ animationDelay: `${i * 50}ms` }}>
                      {/* 商品画像 */}
                      <div className="product-list-image relative">
                        {/* 左上のYouTubeバッジ */}
                        <div className="absolute top-2 left-2 z-10 bg-white/90 backdrop-blur px-1.5 py-0.5 rounded-md border border-rose-100 shadow-sm flex items-center gap-1">
                          <Play className="w-3 h-3 text-rose-500 fill-rose-500" />
                          <span className="text-[10px] font-bold text-rose-600">話題</span>
                        </div>

                        {product.image_url && product.image_url !== '' ? (
                          <img
                            src={product.image_url}
                            alt={product.name}
                            className="w-full h-full object-contain p-2 group-hover:scale-105 transition-transform duration-300"
                          />
                        ) : product.thumbnail_url ? (
                          <img
                            src={product.thumbnail_url}
                            alt={product.name}
                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center bg-gray-50 text-gray-300">
                            <Package className="w-8 h-8 opacity-20" />
                          </div>
                        )}
                      </div>

                      {/* 商品情報 */}
                      <div className="flex-1 min-w-0 py-4 px-5 flex flex-col justify-between">
                        <div>
                          {/* ブランド & カテゴリタグ */}
                          <div className="flex items-center gap-2 mb-1">
                            {product.brand && (
                              <span className="text-xs font-bold text-gray-500">{product.brand}</span>
                            )}
                            <span className="text-gray-300 text-[10px]">|</span>
                            {product.category && (
                              <span className="text-[10px] text-gray-400">{product.category}</span>
                            )}
                          </div>

                          {/* 商品名 */}
                          <h3 className="text-base font-bold text-gray-800 leading-relaxed mb-2 group-hover:text-rose-600 transition-colors">
                            {product.name}
                          </h3>

                          {/* スペックタグ (ダミー) */}
                          <div className="flex flex-wrap gap-1.5 mb-3">
                            {product.category?.includes('ファンデ') && <span className="bg-rose-50 text-rose-600 text-[10px] px-2 py-0.5 rounded-full">#くずれにくい</span>}
                            {product.category?.includes('リップ') && <span className="bg-rose-50 text-rose-600 text-[10px] px-2 py-0.5 rounded-full">#粘膜リップ</span>}
                            {product.category?.includes('スキンケア') && <span className="bg-rose-50 text-rose-600 text-[10px] px-2 py-0.5 rounded-full">#毛穴ケア</span>}
                            <span className="bg-gray-100 text-gray-500 text-[10px] px-2 py-0.5 rounded-full">#30代おすすめ</span>
                          </div>
                        </div>

                        {/* 評価・価格エリア */}
                        <div className="flex items-end justify-between border-t border-gray-100 pt-3 mt-1">
                          <div className="flex items-center gap-4">
                            {/* @cosme 評価 */}
                            <div className="flex flex-col">
                              <span className="text-[10px] text-gray-400 flex items-center gap-1"><span className="w-2 h-2 bg-lime-500 rounded-full"></span>@cosme</span>
                              <div className="flex items-center gap-1">
                                <div className="flex">
                                  {[1, 2, 3, 4, 5].map(n => (
                                    <Star key={n} className={`w-3 h-3 ${n <= (product.positive_rate > 80 ? 5 : 4) ? 'text-lime-500 fill-lime-500' : 'text-gray-200'}`} />
                                  ))}
                                </div>
                                <span className="text-sm font-bold text-gray-700">{product.positive_rate > 0 ? (product.positive_rate / 20).toFixed(1) : '-'}</span>
                              </div>
                            </div>
                            {/* YouTube レビュー */}
                            <div className="flex flex-col pl-4 border-l border-gray-100">
                              <span className="text-[10px] text-gray-400 flex items-center gap-1"><Play className="w-2 h-2 text-rose-500 fill-rose-500" />動画レビュー</span>
                              <span className="text-sm font-bold text-gray-700">{product.review_count}件</span>
                            </div>
                          </div>

                          {product.price && (
                            <div className="text-right">
                              <p className="text-sm font-bold text-gray-800">{product.price}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            )}

            {!loading && products.length === 0 && (
              <div className="text-center py-20 bg-white rounded-xl border border-dashed border-gray-200">
                <p className="text-gray-400 mb-2">条件に一致する商品は見つかりませんでした</p>
                <button onClick={clearFilters} className="text-rose-500 font-medium hover:underline text-sm">
                  すべての条件をクリアして再検索
                </button>
              </div>
            )}
          </main>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-100 py-8 mt-12">
        <div className="max-w-[1400px] mx-auto px-6 text-center text-gray-400 text-xs">
          <p>&copy; 2026 CosmeReview AI - 30代のための賢いコスメ選び</p>
        </div>
      </footer>
    </div>
  );
}
