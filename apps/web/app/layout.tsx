import type { Metadata } from "next";
import localFont from "next/font/local";
import GoogleMapsProvider from "./components/GoogleMapsProvider";
import "./globals.css";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
});

export const metadata: Metadata = {
  title: "Genlogs - Freight Analytics",
  description:
    "Logistics analytics platform for tracking freight movement between cities",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${geistSans.variable} ${geistMono.variable}`}>
        <GoogleMapsProvider>
          <header className="header">
            <div className="header-content">
              <h1>
                <span>Gen</span>logs
              </h1>
              <span className="header-subtitle">
                Freight Analytics Platform
              </span>
            </div>
          </header>
          {children}
        </GoogleMapsProvider>
      </body>
    </html>
  );
}
