'use client';

import { useEffect, useState } from 'react';
import { Activity, TrendingUp, Zap, AlertTriangle } from 'lucide-react';
import { 
  getDashboardStats, 
  getMarkets, 
  getTopSignals,
  formatPrice,
  formatVolume,
  formatTimestamp,
  getSignalTypeLabel,
  type DashboardStats,
  type MarketSummary,
  type TopSignal,
} from '@/lib/api';

// =============================================================================
// Dashboard Page
// =============================================================================

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [markets, setMarkets] = useState<MarketSummary[]>([]);
  const [topSignals, setTopSignals] = useState<TopSignal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        setError(null);
        
        const [statsData, marketsData, signalsData] = await Promise.all([
          getDashboardStats(),
          getMarkets({ limit: 10 }),
          getTopSignals({ limit: 5, hours: 24 }),
        ]);
        
        setStats(statsData);
        setMarkets(marketsData);
        setTopSignals(signalsData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load data');
      } finally {
        setLoading(false);
      }
    }
    
    loadData();
    
    // Refresh every 60 seconds
    const interval = setInterval(loadData, 60000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <LoadingState />;
  }

  if (error) {
    return <ErrorState message={error} />;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Page header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white">Dashboard</h1>
        <p className="mt-1 text-white/60">
          Real-time signal detection for Polymarket prediction markets
        </p>
      </div>
      
      {/* Stats cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard
          title="Markets Tracked"
          value={stats?.total_markets_tracked ?? 0}
          icon={<Activity className="w-5 h-5" />}
          color="blue"
        />
        <StatCard
          title="Signals (24h)"
          value={stats?.signals_24h ?? 0}
          icon={<Zap className="w-5 h-5" />}
          color="amber"
        />
        <StatCard
          title="Top Signal Score"
          value={stats?.highest_score_signal?.score.toFixed(0) ?? '-'}
          icon={<AlertTriangle className="w-5 h-5" />}
          color="red"
        />
        <StatCard
          title="Active Markets"
          value={markets.filter(m => m.recent_signals > 0).length}
          icon={<TrendingUp className="w-5 h-5" />}
          color="green"
        />
      </div>
      
      {/* Main content grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Top signals */}
        <div className="lg:col-span-2">
          <div className="bg-white/5 rounded-xl border border-white/10 overflow-hidden">
            <div className="px-6 py-4 border-b border-white/10">
              <h2 className="text-lg font-semibold text-white">Top Signals (24h)</h2>
            </div>
            <div className="divide-y divide-white/5">
              {topSignals.length === 0 ? (
                <div className="px-6 py-12 text-center text-white/40">
                  No signals detected in the last 24 hours
                </div>
              ) : (
                topSignals.map((item) => (
                  <SignalRow key={item.signal.id} signal={item} />
                ))
              )}
            </div>
          </div>
        </div>
        
        {/* Active markets */}
        <div>
          <div className="bg-white/5 rounded-xl border border-white/10 overflow-hidden">
            <div className="px-6 py-4 border-b border-white/10">
              <h2 className="text-lg font-semibold text-white">Top Markets</h2>
            </div>
            <div className="divide-y divide-white/5">
              {markets.slice(0, 5).map((market) => (
                <MarketRow key={market.id} market={market} />
              ))}
            </div>
            <div className="px-6 py-3 border-t border-white/10">
              <a 
                href="/markets" 
                className="text-sm text-green-400 hover:text-green-300 transition-colors"
              >
                View all markets →
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Components
// =============================================================================

function StatCard({ 
  title, 
  value, 
  icon, 
  color 
}: { 
  title: string; 
  value: number | string; 
  icon: React.ReactNode;
  color: 'blue' | 'amber' | 'red' | 'green';
}) {
  const colorClasses = {
    blue: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    amber: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    red: 'bg-red-500/10 text-red-400 border-red-500/20',
    green: 'bg-green-500/10 text-green-400 border-green-500/20',
  };
  
  return (
    <div className={`rounded-xl border p-6 ${colorClasses[color]}`}>
      <div className="flex items-center gap-3 mb-3">
        {icon}
        <span className="text-sm font-medium text-white/70">{title}</span>
      </div>
      <div className="text-3xl font-bold text-white">{value}</div>
    </div>
  );
}

function SignalRow({ signal }: { signal: TopSignal }) {
  const scoreColor = signal.signal.score >= 70 
    ? 'text-red-400' 
    : signal.signal.score >= 50 
      ? 'text-amber-400' 
      : 'text-green-400';
  
  return (
    <div className="px-6 py-4 hover:bg-white/5 transition-colors">
      <div className="flex items-start gap-4">
        {/* Score badge */}
        <div className={`flex-shrink-0 w-12 h-12 rounded-lg bg-white/5 flex items-center justify-center ${scoreColor} font-bold`}>
          {signal.signal.score.toFixed(0)}
        </div>
        
        {/* Content */}
        <div className="flex-1 min-w-0">
          <p className="text-white font-medium truncate">
            {signal.market?.question ?? 'Unknown Market'}
          </p>
          <div className="flex items-center gap-3 mt-1 text-sm text-white/50">
            <span className="px-2 py-0.5 bg-white/10 rounded text-xs">
              {getSignalTypeLabel(signal.signal.signal_type)}
            </span>
            <span>{formatTimestamp(signal.signal.timestamp)}</span>
            {signal.market && (
              <span>@ {formatPrice(signal.market.yes_price)}</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function MarketRow({ market }: { market: MarketSummary }) {
  return (
    <a 
      href={`/markets/${market.id}`}
      className="block px-6 py-4 hover:bg-white/5 transition-colors"
    >
      <p className="text-white font-medium truncate mb-1">
        {market.question}
      </p>
      <div className="flex items-center gap-4 text-sm">
        <span className="text-green-400 font-medium">
          {formatPrice(market.yes_price)}
        </span>
        <span className="text-white/40">
          Vol: {formatVolume(market.volume_24h)}
        </span>
        {market.recent_signals > 0 && (
          <span className="text-amber-400">
            {market.recent_signals} signal{market.recent_signals !== 1 ? 's' : ''}
          </span>
        )}
      </div>
    </a>
  );
}

function LoadingState() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="animate-pulse">
        <div className="h-8 w-48 bg-white/10 rounded mb-2" />
        <div className="h-4 w-96 bg-white/5 rounded mb-8" />
        <div className="grid grid-cols-4 gap-4 mb-8">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-32 bg-white/5 rounded-xl" />
          ))}
        </div>
        <div className="grid grid-cols-3 gap-8">
          <div className="col-span-2 h-96 bg-white/5 rounded-xl" />
          <div className="h-96 bg-white/5 rounded-xl" />
        </div>
      </div>
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-8 text-center">
        <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-white mb-2">Failed to Load Data</h2>
        <p className="text-white/60 mb-4">{message}</p>
        <button 
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-white transition-colors"
        >
          Retry
        </button>
      </div>
    </div>
  );
}
