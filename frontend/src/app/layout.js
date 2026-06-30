import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import BootstrapClient from "./BootstrapClient";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata = {
  title: "Paper Agent",
  description: "AI-driven Research Gap Analyzer and Literature Matrix Specialist",
};

import { AuthContextProvider } from "@/contexts/AuthContext";
import { ThemeContextProvider } from "@/contexts/ThemeContext";
import { NotificationContextProvider } from "@/contexts/NotificationContext";
import AppLayoutWrapper from "@/components/app-layout-wrapper/AppLayoutWrapper";

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable}`} data-scroll-behavior="smooth" suppressHydrationWarning>
      <body>
        <BootstrapClient />
        <ThemeContextProvider>
          <AuthContextProvider>
            <NotificationContextProvider>
              <AppLayoutWrapper>
                {children}
              </AppLayoutWrapper>
            </NotificationContextProvider>
          </AuthContextProvider>
        </ThemeContextProvider>
      </body>
    </html>
  );
}
