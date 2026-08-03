import type { Metadata } from "next";
import { headers } from "next/headers";
import "./globals.css";

export async function generateMetadata(): Promise<Metadata> {
  const incomingHeaders = await headers();
  const host = incomingHeaders.get("host") || "chronicle.local";
  const protocol = host.includes("localhost") || host.startsWith("127.0.0.1") ? "http" : "https";
  const baseUrl = `${protocol}://${host}`;

  return {
    metadataBase: new URL(baseUrl),
    title: "Chronicle — keep the moments, notice your growth",
    description:
      "A personal journal for meaningful moments, intentional goals, and thoughtful AI reflections.",
    openGraph: {
      title: "Chronicle — keep the moments, notice your growth",
      description: "Capture what matters and see how you are moving forward.",
      type: "website",
      images: [{ url: `${baseUrl}/og.png`, alt: "Chronicle personal journal preview" }],
    },
    twitter: {
      card: "summary_large_image",
      title: "Chronicle — keep the moments, notice your growth",
      description: "A personal journal for meaningful moments, goals, and thoughtful AI reflections.",
      images: [`${baseUrl}/og.png`],
    },
  };
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
