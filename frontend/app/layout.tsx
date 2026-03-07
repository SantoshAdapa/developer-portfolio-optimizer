import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "@/styles/globals.css";
import { cn } from "@/lib/utils";
import { QueryProvider } from "@/lib/query-provider";
import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import { siteConfig } from "@/lib/constants";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-geist-sans",
});

export const metadata: Metadata = {
  title: {
    default: siteConfig.name,
    template: `%s | ${siteConfig.name}`,
  },
  description: siteConfig.description,
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body
        className={cn(
          inter.variable,
          "min-h-screen bg-background font-sans antialiased"
        )}
      >
        <QueryProvider>
          {/* Ambient background gradients */}
          <div className="fixed inset-0 -z-10 overflow-hidden">
            <div className="absolute -top-[40%] -left-[20%] h-[80%] w-[60%] rounded-full bg-blue-600/[0.07] blur-[120px]" />
            <div className="absolute -bottom-[40%] -right-[20%] h-[80%] w-[60%] rounded-full bg-violet-600/[0.07] blur-[120px]" />
            <div className="absolute top-[20%] right-[10%] h-[40%] w-[30%] rounded-full bg-indigo-600/[0.05] blur-[100px]" />
          </div>

          <div className="relative flex min-h-screen flex-col">
            <Navbar />
            <main className="flex-1 pt-16">{children}</main>
            <Footer />
          </div>
        </QueryProvider>
      </body>
    </html>
  );
}
