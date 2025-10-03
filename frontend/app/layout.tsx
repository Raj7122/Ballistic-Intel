import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "@/lib/providers";

/**
 * Inter font - optimized for data-heavy interfaces
 * Used for headings and body text
 */
const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

/**
 * JetBrains Mono - monospace font for numeric data
 * Used for patent numbers, metrics, and code
 */
const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "CyberPatent Intelligence | Ballistic Ventures",
  description:
    "Early-stage cybersecurity deal flow intelligence. Track patents, funding rounds, and VC activity 12-18 months before PitchBook.",
  keywords: [
    "cybersecurity",
    "venture capital",
    "patent intelligence",
    "startup funding",
    "deal flow",
  ],
  authors: [{ name: "Ballistic Ventures" }],
  openGraph: {
    title: "CyberPatent Intelligence",
    description: "Early-stage cybersecurity deal flow intelligence",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="antialiased font-sans">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
