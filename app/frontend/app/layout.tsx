import "./globals.css";
import type { Metadata, Viewport } from "next";

export const metadata: Metadata = {
  title: "hoichoi · Context-Aware Ad Intelligence",
  description:
    "Semantic scene segmentation, safe break scoring, and brand-safe placement for Bengali drama — never modifying the source video.",
  themeColor: "#07060c",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#07060c",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
