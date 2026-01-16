'use client';

import { useEffect, useState } from 'react';
import { Search, TrendingUp, Activity } from 'lucide-react';
import { 
  getMarkets, 
  formatPrice, 
  formatVolume, 
  formatTimestamp,
  type MarketSummary 
} from '@/lib/api';

export default function MarketsPage() {
  const [markets, setMarkets] = useState<MarketSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    async function loadMarkets() {
      try {
        const data = await getMarkets({ limit: 50 });
        setMarkets(data);
      } catch (err) {
        console.error('Failed to load markets:', err);
      } finally {
        setLoading(false);
      }
    }
    loadMarkets();
  }, []);

  const filteredMarkets = markets.filter(m => 
    m.question.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white">Markets</h1>
          <p className="mt-1 text-white/60">
            {markets.length} markets tracked
          </p>
        </div>
        
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40" />
          <input
            type="text"
            placeholder="Search markets..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 pr-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-white/40 focus:outline-none focus:border-green-500/50 w-64"
          />
        </div>
      </div>

      {/* Markets table */}
      <div className="bg-white/5 rounded-xl border border-white/10 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/10">
              <th className="text-left px-6 py-4 text-sm font-medium text-white/60">Market</th>
              <th className="text-right px-6 py-4 text-sm font-medium text-white/60">Yes Price</th>
              <th className="text-right px-6 py-4 text-sm font-medium text-white/60">Volume (24h)</th>
              <th className="text-right px-6 py-4 text-sm font-medium text-white/60">Signals</th>
              <th className="text-right px-6 py-4 text-sm font-medium text-white/60">Last Signal</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {loading ? (
              [...Array(10)].map((_, i) => (
                <tr key={i}>
                  <td colSpan={5} className="px-6 py-4">
                    <div className="h-6 bg-white/5 rounded animate-pulse" />
                  </td>
                </tr>
              ))
            ) : filteredMarkets.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-12 text-center text-white/40">
                  No markets found
                </td>
              </tr>
            ) : (
              filteredMarkets.map((market) => (
                <tr 
                  key={market.id} 
                  className="hover:bg-white/5 transition-colors cursor-pointer"
                  onClick={() => window.location.href = `/markets/${market.id}`}
                >
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-green-500/20 to-emerald-500/20 flex items-center justify-center">
                        <TrendingUp className="w-4 h-4 text-green-400" />
                      </div>
                      <span className="text-white font-medium truncate max-w-md">
                        {market.question}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <span className="text-green-400 font-medium">
                      {formatPrice(market.yes_price)}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right text-white/70">
                    {formatVolume(market.volume_24h)}
                  </td>
                  <td className="px-6 py-4 text-right">
                    {market.recent_signals > 0 ? (
                      <span className="inline-flex items-center gap-1 px-2 py-1 bg-amber-500/10 text-amber-400 rounded text-sm">
                        <Activity className="w-3 h-3" />
                        {market.recent_signals}
                      </span>
                    ) : (
                      <span className="text-white/30">-</span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-right text-white/50 text-sm">
                    {market.last_signal_at 
                      ? formatTimestamp(market.last_signal_at)
                      : '-'
                    }
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
