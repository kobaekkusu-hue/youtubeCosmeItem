import type { Metadata } from "next";
import { Inter, Noto_Sans_JP } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

const notoSansJP = Noto_Sans_JP({
  variable: "--font-noto-sans-jp",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "CosmeReview AI — YouTube動画コスメレビュー検索",
  description: "YouTube動画からコスメのリアルな評価を瞬時に検索。AIがレビュー動画を分析し、商品ごとの評判をまとめます。",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja">
      <body
        className={`${inter.variable} ${notoSansJP.variable} antialiased`}
        style={{ fontFamily: "'Inter', 'Noto Sans JP', sans-serif" }}
      >
        {children}
      </body>
    </html>
  );
}
