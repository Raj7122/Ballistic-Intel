import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import { headers } from "next/headers";
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

/**
 * Root Layout - Enhanced with CSP Nonce (Task 1.5)
 * 
 * The nonce is generated per-request in middleware.ts and passed via headers.
 * This nonce is used for inline scripts and will be required for any third-party
 * scripts loaded via next/script.
 * 
 * Security: Prevents XSS by only allowing scripts with the correct nonce.
 */
export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  // Get nonce from middleware
  const headersList = await headers();
  const nonce = headersList.get('x-nonce') || undefined;
  
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <head>
        {/* 
          Any inline scripts or third-party scripts should use the nonce.
          Example: <Script nonce={nonce} src="..." />
          
          For now, we have no inline scripts. Next.js will automatically
          apply the nonce to its own scripts when CSP is detected.
        */}
      </head>
      <body className="antialiased font-sans" suppressHydrationWarning>
        <Providers>{children}</Providers>
        
        {/* 
          Development-only: Log CSP nonce for debugging
          Remove or disable in production 
        */}
        {process.env.NODE_ENV === 'development' && nonce && (
          <script
            nonce={nonce}
            dangerouslySetInnerHTML={{
              __html: `console.log('[CSP] Nonce:', '${nonce}');`,
            }}
          />
        )}
      </body>
    </html>
  );
}
