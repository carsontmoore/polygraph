'use client';

import { useEffect, useState } from 'react';
import { Zap, Filter } from 'lucide-react';
import { 
  getSignals, 
  formatPrice, 
  formatTimestamp,
  getSignalTypeLabel,
  type Signal 
} from '@/lib/api';

export default function SignalsPage() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(true);
  const [minScore, setMinScore] = useState(0);
  const [signalType, setSignalType] = useState<string>('');
  const [hours, setHours] = useState(24);

  useEffect(() => {
    async function loadSignals() {
      try {
        setLoading(true);
        const data = await getSignals({ 
          limit: 50, 
          min_score: minScore,
          signal_type: signalType || undefined,
          hours 
        });
        setSignals(data);
      } catch (err) {
        console.error('Failed to load signals:', err);
      } finally {
        setLoading(false);
      }
    }
    loadSignals();
  }, [minScore, signalType, hours]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white">Signals</h1>
          <p className="mt-1 text-white/60">
            Detected market anomalies and patterns
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 mb-6 p-4 bg-white/5 rounded-xl border border-white/10">
        <Filter className="w-4 h-4 text-white/40" />
        
        <select
          value={hours}
          onChange={(e) => setHours(Number(e.target.value))}
          className="bg-white/10 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-green-500/50"
        >
          <option value={6}>Last 6 hours</option>
          <option value={24}>Last 24 hours</option>
          <option value={48}>Last 48 hours</option>
          <option value={168}>Last 7 days</option>
        </select>

        <select
          value={signalType}
          onChange={(e) => setSignalType(e.target.value)}
          className="bg-white/10 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-green-500/50"
        >
          <option value="">All Types</option>
          <option value="volume_spike">Volume Spike</option>
          <option value="orderbook_imbalance">Order Imbalance</option>
          <option value="price_divergence">Price Divergence</option>
        </select>

        <select
          value={minScore}
          onChange={(e) => setMinScore(Number(e.target.value))}
          className="bg-white/10 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-green-500/50"
        >
          <option value={0}>All Scores</option>
          <option value={30}>Score 30+</option>
          <option value={50}>Score 50+</option>
          <option value={70}>Score 70+</option>
        </select>

        <span className="text-sm text-white/40 ml-auto">
          {signals.length} signals found
        </span>
      </div>

      {/* Signals list */}
      <div className="space-y-4">
        {loading ? (
          [...Array(5)].map((_, i) => (
            <div key={i} className="h-24 bg-white/5 rounded-xl animate-pulse" />
          ))
        ) : signals.length === 0 ? (
          <div className="bg-white/5 rounded-xl border border-white/10 p-12 text-center">
            <Zap className="w-12 h-12 text-white/20 mx-auto mb-4" />
            <p className="text-white/40">No signals match your filters</p>
          </div>
        ) : (
          signals.map((signal) => (
            <SignalCard key={signal.id} signal={signal} />
          ))
        )}
      </div>
    </div>
  );
}

function SignalCard({ signal }: { signal: Signal }) {
  const scoreColor = signal.score >= 70 
    ? 'bg-red-500/20 text-red-400 border-red-500/30' 
    : signal.score >= 50 
      ? 'bg-amber-500/20 text-amber-400 border-amber-500/30' 
      : 'bg-green-500/20 text-green-400 border-green-500/30';

  return (
    <div className="bg-white/5 rounded-xl border border-white/10 p-6 hover:bg-white/[0.07] transition-colors">
      <div className="flex items-start gap-6">
        {/* Score */}
        <div className={`flex-shrink-0 w-16 h-16 rounded-xl flex flex-col items-center justify-center border ${scoreColor}`}>
          <span className="text-2xl font-bold">{signal.score.toFixed(0)}</span>
          <span className="text-[10px] uppercase tracking-wider opacity-60">Score</span>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h3 className="text-white font-semibold truncate">
                {signal.market_question}
              </h3>
              <div className="flex items-center gap-3 mt-2">
                <span className="px-2 py-1 bg-white/10 rounded text-xs text-white/70">
                  {getSignalTypeLabel(signal.signal_type)}
                </span>
                <span className="text-sm text-white/50">
                  {formatTimestamp(signal.timestamp)}
                </span>
                <span className="text-sm text-white/50">
                  Price: {formatPrice(signal.price_at_signal)}
                </span>
              </div>
            </div>
            
            <a
              href={`/markets/${signal.market_id}`}
              className="px-3 py-1.5 bg-white/10 hover:bg-white/20 rounded-lg text-sm text-white transition-colors"
            >
              View Market
            </a>
          </div>

          {/* Details */}
          {signal.details && Object.keys(signal.details).length > 0 && (
            <div className="mt-4 p-3 bg-black/20 rounded-lg">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                {signal.signal_type === 'volume_spike' && (
                  <>
                    <div>
                      <span className="text-white/40">Z-Score</span>
                      <p className="text-white font-medium">
                        {(signal.details.z_score as number)?.toFixed(2) ?? '-'}
                      </p>
                    </div>
                    <div>
                      <span className="text-white/40">Current Vol</span>
                      <p className="text-white font-medium">
                        ${(signal.details.current_volume as number)?.toLocaleString() ?? '-'}
                      </p>
                    </div>
                    <div>
                      <span className="text-white/40">Mean Vol</span>
                      <p className="text-white font-medium">
                        ${(signal.details.mean_volume as number)?.toLocaleString() ?? '-'}
                      </p>
                    </div>
                  </>
                )}
                {signal.signal_type === 'orderbook_imbalance' && (
                  <>
                    <div>
                      <span className="text-white/40">Direction</span>
                      <p className="text-white font-medium capitalize">
                        {(signal.details.direction as string) ?? '-'}
                      </p>
                    </div>
                    <div>
                      <span className="text-white/40">Ratio</span>
                      <p className="text-white font-medium">
                        {(signal.details.ratio as number)?.toFixed(1) ?? '-'}x
                      </p>
                    </div>
                    <div>
                      <span className="text-white/40">Bid Depth</span>
                      <p className="text-white font-medium">
                        ${(signal.details.bid_depth as number)?.toLocaleString() ?? '-'}
                      </p>
                    </div>
                    <div>
                      <span className="text-white/40">Ask Depth</span>
                      <p className="text-white font-medium">
                        ${(signal.details.ask_depth as number)?.toLocaleString() ?? '-'}
                      </p>
                    </div>
                  </>
                )}
                {signal.signal_type === 'price_divergence' && (
                  <>
                    <div>
                      <span className="text-white/40">Type</span>
                      <p className="text-white font-medium">
                        {(signal.details.divergence_type as string)?.replace(/_/g, ' ') ?? '-'}
                      </p>
                    </div>
                    <div>
                      <span className="text-white/40">Price Change</span>
                      <p className="text-white font-medium">
                        {((signal.details.price_change_pct as number) * 100)?.toFixed(1) ?? '-'}%
                      </p>
                    </div>
                  </>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
