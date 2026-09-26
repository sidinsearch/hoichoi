import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "hoichoi — Context-Aware Ad Intelligence",
  description: "Semantic ad-break placement for Bengali drama.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-ink text-sand">{children}</body>
    </html>
  );
}
