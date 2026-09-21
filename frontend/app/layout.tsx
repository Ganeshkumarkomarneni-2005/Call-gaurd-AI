import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'CallGuard AI',
  description: 'AI-powered intelligent call screening and fraud detection',
  icons: { icon: '/favicon.ico' },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="font-sans antialiased text-slate-900 bg-slate-50">{children}</body>
    </html>
  );
}
