import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "ArXiv Semantic Search",
  description:
    "Discover research papers by meaning, not just keywords. Vector search over arXiv computer-science papers with sentence embeddings.",
  keywords: ["arXiv", "semantic search", "vector search", "embeddings", "research papers", "Qdrant", "FastAPI"],
  openGraph: {
    title: "ArXiv Semantic Search",
    description: "Discover research papers by meaning, not just keywords.",
    type: "website",
  },
};

export const viewport: Viewport = {
  themeColor: "#07090d",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col font-sans">{children}</body>
    </html>
  );
}
