'use client';

import React, { useState, useEffect, useCallback, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Search, Loader2, X, Star, ChevronRight, Package, Tag, ThumbsUp } from 'lucide-react';
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
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [brands, setBrands] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  // カテゴリとブランドを取得
  useEffect(() => {
    fetch(`${API_BASE}/categories`).then(r => r.json()).then(setCategories).catch(() => { });
    fetch(`${API_BASE}/brands`).then(r => r.json()).then(setBrands).catch(() => { });
  }, []);

  // 商品検索
  const fetchProducts = useCallback(async (q: string, cat: string, br: string) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (q) params.set('q', q);
      if (cat) params.set('category', cat);
      if (br) params.set('brand', br);
      const res = await fetch(`${API_BASE}/products?${params.toString()}`);
      const data = await res.json();
      setProducts(data);
    } catch (e) {
      console.error('Fetch error:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  // URL更新
  const updateURL = useCallback((q: string, cat: string, br: string) => {
    const params = new URLSearchParams();
    if (q) params.set('q', q);
    if (cat) params.set('category', cat);
    if (br) params.set('brand', br);
    router.replace(`/?${params.toString()}`, { scroll: false });
  }, [router]);

  // 初期ロード & フィルター変更時
  useEffect(() => {
    fetchProducts(query, selectedCategory, selectedBrand);
    updateURL(query, selectedCategory, selectedBrand);
  }, [selectedCategory, selectedBrand]);

  // 検索ハンドラ
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchProducts(query, selectedCategory, selectedBrand);
    updateURL(query, selectedCategory, selectedBrand);
  };

  // フィルタークリア
  const clearFilters = () => {
    setSelectedCategory('');
    setSelectedBrand('');
    setQuery('');
    fetchProducts('', '', '');
    updateURL('', '', '');
  };

  const hasActiveFilters = query || selectedCategory || selectedBrand;

  // 検索パラメータを組み立て（詳細ページの戻るリンク用）
  const buildBackParams = () => {
    const p = new URLSearchParams();
    if (query) p.set('q', query);
    if (selectedCategory) p.set('category', selectedCategory);
    if (selectedBrand) p.set('brand', selectedBrand);
    return p.toString();
  };

  return (
    <div className="min-h-screen bg-[#fafafa]">
      {/* ===== 上部固定ヘッダー + 検索バー ===== */}
      <header className="sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-[1400px] mx-auto px-4 sm:px-6">
          <div className="flex items-center h-16 gap-4">
            {/* ロゴ */}
            <Link href="/" className="shrink-0 flex items-center gap-1">
              <span className="text-lg sm:text-xl font-extrabold gradient-text">CosmeReview</span>
              <span className="text-xs sm:text-sm font-bold text-gray-400">AI</span>
            </Link>

            {/* 検索バー */}
            <form onSubmit={handleSearch} className="flex-1 max-w-2xl">
              <div className="flex items-center bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 focus-within:border-violet-400 focus-within:ring-2 focus-within:ring-violet-100 transition-all">
                <Search className="w-4 h-4 text-gray-400 mr-2 shrink-0" />
                <input
                  type="text"
                  placeholder="商品名、ブランド、YouTuber名で検索..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="flex-1 bg-transparent border-0 outline-none text-sm text-gray-800 placeholder:text-gray-400"
                />
                {query && (
                  <button
                    type="button"
                    onClick={() => { setQuery(''); fetchProducts('', selectedCategory, selectedBrand); updateURL('', selectedCategory, selectedBrand); }}
                    className="text-gray-300 hover:text-gray-500 mr-2 transition-colors"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                )}
                <button
                  id="search-button"
                  type="submit"
                  disabled={loading}
                  className="bg-violet-600 hover:bg-violet-700 text-white px-3 sm:px-4 py-1.5 rounded-md font-medium text-xs transition-all"
                >
                  {loading ? <Loader2 className="animate-spin w-3.5 h-3.5" /> : (
                    <>
                      <span className="hidden sm:inline">検索</span>
                      <Search className="sm:hidden w-3.5 h-3.5" />
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      </header>

      {/* ===== メインコンテンツ（サイドバー + 商品リスト） ===== */}
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 py-6">
        <div className="flex gap-6">
          {/* ===== 左サイドバー ===== */}
          <aside className="w-[220px] shrink-0 hidden lg:block">
            <div className="sticky top-24 space-y-6">
              {/* アクティブフィルター */}
              {hasActiveFilters && (
                <div>
                  <button
                    onClick={clearFilters}
                    className="text-xs text-violet-600 hover:text-violet-800 transition-colors flex items-center gap-1 mb-3"
                  >
                    <X className="w-3 h-3" /> すべての条件をクリア
                  </button>
                  <div className="flex flex-wrap gap-1.5">
                    {query && (
                      <span className="inline-flex items-center gap-1 bg-violet-50 text-violet-700 text-[11px] px-2 py-1 rounded-md border border-violet-200">
                        「{query}」
                        <X className="w-3 h-3 cursor-pointer hover:text-violet-900" onClick={() => { setQuery(''); fetchProducts('', selectedCategory, selectedBrand); updateURL('', selectedCategory, selectedBrand); }} />
                      </span>
                    )}
                    {selectedCategory && (
                      <span className="inline-flex items-center gap-1 bg-violet-50 text-violet-700 text-[11px] px-2 py-1 rounded-md border border-violet-200">
                        {selectedCategory}
                        <X className="w-3 h-3 cursor-pointer hover:text-violet-900" onClick={() => setSelectedCategory('')} />
                      </span>
                    )}
                    {selectedBrand && (
                      <span className="inline-flex items-center gap-1 bg-violet-50 text-violet-700 text-[11px] px-2 py-1 rounded-md border border-violet-200">
                        {selectedBrand}
                        <X className="w-3 h-3 cursor-pointer hover:text-violet-900" onClick={() => setSelectedBrand('')} />
                      </span>
                    )}
                  </div>
                </div>
              )}

              {/* カテゴリフィルター */}
              <div>
                <h3 className="sidebar-heading">
                  <Tag className="w-3.5 h-3.5" />
                  カテゴリから探す
                </h3>
                <ul className="space-y-0.5">
                  {categories.map(cat => (
                    <li key={cat}>
                      <button
                        onClick={() => setSelectedCategory(selectedCategory === cat ? '' : cat)}
                        className={`sidebar-item w-full text-left ${selectedCategory === cat ? 'active' : ''}`}
                      >
                        <ChevronRight className="w-3 h-3 shrink-0" />
                        <span className="truncate">{cat}</span>
                      </button>
                    </li>
                  ))}
                </ul>
              </div>

              {/* ブランドフィルター */}
              <div>
                <h3 className="sidebar-heading">
                  <Package className="w-3.5 h-3.5" />
                  ブランドから探す
                </h3>
                <ul className="space-y-0.5">
                  {brands.map(br => (
                    <li key={br}>
                      <button
                        onClick={() => setSelectedBrand(selectedBrand === br ? '' : br)}
                        className={`sidebar-item w-full text-left ${selectedBrand === br ? 'active' : ''}`}
                      >
                        <ChevronRight className="w-3 h-3 shrink-0" />
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
            {/* 検索結果ヘッダー */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold text-gray-700">
                  商品検索結果
                </h2>
                <span className="text-xs text-gray-400">
                  {loading ? '検索中...' : `${products.length} 件`}
                </span>
              </div>
            </div>

            {/* モバイル用フィルターバー */}
            <div className="lg:hidden mb-4 flex flex-wrap gap-2">
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="text-xs border border-gray-200 rounded-md px-3 py-2 bg-white text-gray-600"
              >
                <option value="">カテゴリ</option>
                {categories.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
              <select
                value={selectedBrand}
                onChange={(e) => setSelectedBrand(e.target.value)}
                className="text-xs border border-gray-200 rounded-md px-3 py-2 bg-white text-gray-600"
              >
                <option value="">ブランド</option>
                {brands.map(br => (
                  <option key={br} value={br}>{br}</option>
                ))}
              </select>
            </div>

            {/* ローディング */}
            {loading && products.length === 0 ? (
              <div className="text-center py-20">
                <Loader2 className="animate-spin h-8 w-8 mx-auto text-violet-300 mb-3" />
                <p className="text-gray-400 text-sm">検索中...</p>
              </div>
            ) : (
              /* 商品リスト（@cosme風縦型カード） */
              <div className="space-y-3">
                {products.map((product, i) => (
                  <Link
                    key={product.id}
                    href={`/products/${product.id}${buildBackParams() ? '?' + buildBackParams() : ''}`}
                    className="block animate-fade-in-up"
                    style={{ animationDelay: `${i * 30}ms`, opacity: 0 }}
                  >
                    <div className="product-list-card">
                      {/* 商品画像 */}
                      <div className="product-list-image">
                        {product.image_url && product.image_url !== '' ? (
                          <img
                            src={product.image_url}
                            alt={product.name}
                            className="w-full h-full object-contain p-3"
                          />
                        ) : product.thumbnail_url ? (
                          <img
                            src={product.thumbnail_url}
                            alt={product.name}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center bg-gray-50">
                            <span className="text-gray-200 text-[10px] tracking-widest">NO IMAGE</span>
                          </div>
                        )}
                      </div>

                      {/* 商品情報 */}
                      <div className="flex-1 min-w-0 py-3 pr-4">
                        {/* 商品名 + ブランド */}
                        <div className="flex items-start gap-2 mb-1.5">
                          <h3 className="text-sm font-bold text-gray-800 leading-snug line-clamp-2 hover:text-violet-700 transition-colors">
                            {product.name}
                          </h3>
                          {product.brand && (
                            <span className="shrink-0 text-[11px] text-gray-500">
                              / {product.brand}
                            </span>
                          )}
                        </div>

                        {/* 評価バー */}
                        <div className="flex items-center gap-3 mb-2">
                          {/* 好評率 */}
                          <div className="flex items-center gap-1">
                            {product.positive_rate > 0 ? (
                              <>
                                <div className="flex">
                                  {[1, 2, 3, 4, 5].map(n => (
                                    <Star
                                      key={n}
                                      className={`w-3 h-3 ${n <= Math.round(product.positive_rate / 20)
                                        ? 'text-amber-400 fill-amber-400'
                                        : 'text-gray-200'
                                        }`}
                                    />
                                  ))}
                                </div>
                                <span className="text-xs font-semibold text-gray-700">{(product.positive_rate / 20).toFixed(1)}</span>
                              </>
                            ) : (
                              <span className="text-[11px] text-gray-300">—</span>
                            )}
                          </div>
                          {/* レビュー件数 */}
                          <span className="text-[11px] text-gray-400">
                            クチコミ {product.review_count}件
                          </span>
                        </div>

                        {/* メタ情報行 */}
                        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-gray-500">
                          {product.category && (
                            <span className="inline-flex items-center gap-1">
                              <span className="text-gray-300">[</span>
                              {product.category}
                              <span className="text-gray-300">]</span>
                            </span>
                          )}
                          {product.price && (
                            <span className="font-semibold text-gray-700">
                              税込価格：{product.price}
                            </span>
                          )}
                          {product.volume && (
                            <span>{product.volume}</span>
                          )}
                        </div>

                        {/* 説明文 */}
                        {product.description && (
                          <p className="text-[11px] text-gray-400 mt-2 line-clamp-2 leading-relaxed">
                            {product.description}
                          </p>
                        )}
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            )}

            {!loading && products.length === 0 && (
              <div className="text-center py-20">
                <p className="text-base text-gray-300 font-light mb-1">該当する商品がありません</p>
                <p className="text-sm text-gray-200">別のキーワードやフィルターでお試しください</p>
              </div>
            )}
          </main>
        </div>
      </div>
    </div>
  );
}
