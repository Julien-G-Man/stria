import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import WakeupPing from '@/components/WakeupPing';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
});

export const metadata: Metadata = {
  title: 'Stria',
  description: 'AI-powered RDT reader for community health workers',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.variable}>
        <WakeupPing />
        {children}
      </body>
    </html>
  );
}
