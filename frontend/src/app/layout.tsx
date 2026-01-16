import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Polygraph | Prediction Market Analytics',
  description: 'Real-time signal detection and analytics for Polymarket prediction markets',
  keywords: ['polymarket', 'prediction markets', 'analytics', 'trading signals'],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} antialiased`}>
        <div className="min-h-screen flex flex-col">
          {/* Header */}
          <header className="border-b border-white/10 bg-black/50 backdrop-blur-sm sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex items-center justify-between h-16">
                {/* Logo */}
                <a href="/" className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-gradient-to-br from-green-400 to-emerald-600 rounded-lg flex items-center justify-center">
                    <span className="text-white font-bold text-lg">P</span>
                  </div>
                  <span className="text-xl font-bold text-white">Polygraph</span>
                  <span className="text-xs text-white/40 ml-1">beta</span>
                </a>
                
                {/* Navigation */}
                <nav className="flex items-center gap-6">
                  <a 
                    href="/" 
                    className="text-sm text-white/70 hover:text-white transition-colors"
                  >
                    Dashboard
                  </a>
                  <a 
                    href="/markets" 
                    className="text-sm text-white/70 hover:text-white transition-colors"
                  >
                    Markets
                  </a>
                  <a 
                    href="/signals" 
                    className="text-sm text-white/70 hover:text-white transition-colors"
                  >
                    Signals
                  </a>
                </nav>
              </div>
            </div>
          </header>
          
          {/* Main content */}
          <main className="flex-1">
            {children}
          </main>
          
          {/* Footer */}
          <footer className="border-t border-white/10 py-6">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex items-center justify-between text-sm text-white/40">
                <p>Polygraph v0.1.0</p>
                <p>Not financial advice. Data from Polymarket.</p>
              </div>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
