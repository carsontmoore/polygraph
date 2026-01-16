/**
 * API client for Polygraph backend.
 * 
 * Handles all communication with the FastAPI backend.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// =============================================================================
// Types
// =============================================================================

export interface MarketSummary {
  id: string;
  question: string;
  slug: string;
  yes_price: number;
  volume_24h: number;
  recent_signals: number;
  last_signal_at: string | null;
}

export interface MarketDetail {
  market: {
    id: string;
    question: string;
    slug: string;
    outcomes: string[];
    yes_price: number;
    no_price: number;
    volume_24h: number;
    liquidity: number;
    end_date: string | null;
    is_active: boolean;
    updated_at: string;
  };
  price_history: PricePoint[];
  recent_signals: SignalSummary[];
}

export interface PricePoint {
  timestamp: string;
  yes_price: number;
  no_price: number;
  volume: number;
}

export interface Signal {
  id: number;
  market_id: string;
  market_question: string;
  signal_type: 'volume_spike' | 'orderbook_imbalance' | 'price_divergence';
  timestamp: string;
  score: number;
  details: Record<string, unknown>;
  price_at_signal: number;
}

export interface SignalSummary {
  id: number;
  signal_type: string;
  timestamp: string;
  score: number;
  details: Record<string, unknown>;
}

export interface DashboardStats {
  total_markets_tracked: number;
  signals_24h: number;
  highest_score_signal: Signal | null;
  most_active_market: MarketSummary | null;
}

export interface TopSignal {
  signal: SignalSummary & { price_at_signal: number };
  market: {
    id: string;
    question: string;
    yes_price: number;
  } | null;
}

// =============================================================================
// API Functions
// =============================================================================

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}/api${endpoint}`;
  
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }
  
  return response.json();
}

// Markets
export async function getMarkets(params?: {
  limit?: number;
  offset?: number;
  active_only?: boolean;
}): Promise<MarketSummary[]> {
  const searchParams = new URLSearchParams();
  if (params?.limit) searchParams.set('limit', params.limit.toString());
  if (params?.offset) searchParams.set('offset', params.offset.toString());
  if (params?.active_only !== undefined) searchParams.set('active_only', params.active_only.toString());
  
  const query = searchParams.toString();
  return fetchAPI<MarketSummary[]>(`/markets${query ? `?${query}` : ''}`);
}

export async function getMarket(marketId: string): Promise<MarketDetail> {
  return fetchAPI<MarketDetail>(`/markets/${encodeURIComponent(marketId)}`);
}

// Signals
export async function getSignals(params?: {
  limit?: number;
  offset?: number;
  min_score?: number;
  signal_type?: string;
  market_id?: string;
  hours?: number;
}): Promise<Signal[]> {
  const searchParams = new URLSearchParams();
  if (params?.limit) searchParams.set('limit', params.limit.toString());
  if (params?.offset) searchParams.set('offset', params.offset.toString());
  if (params?.min_score) searchParams.set('min_score', params.min_score.toString());
  if (params?.signal_type) searchParams.set('signal_type', params.signal_type);
  if (params?.market_id) searchParams.set('market_id', params.market_id);
  if (params?.hours) searchParams.set('hours', params.hours.toString());
  
  const query = searchParams.toString();
  return fetchAPI<Signal[]>(`/signals${query ? `?${query}` : ''}`);
}

export async function getTopSignals(params?: {
  limit?: number;
  hours?: number;
}): Promise<TopSignal[]> {
  const searchParams = new URLSearchParams();
  if (params?.limit) searchParams.set('limit', params.limit.toString());
  if (params?.hours) searchParams.set('hours', params.hours.toString());
  
  const query = searchParams.toString();
  return fetchAPI<TopSignal[]>(`/signals/top${query ? `?${query}` : ''}`);
}

// Dashboard
export async function getDashboardStats(): Promise<DashboardStats> {
  return fetchAPI<DashboardStats>('/stats');
}

// Health
export async function checkHealth(): Promise<{ status: string; timestamp: string; version: string }> {
  return fetchAPI('/health');
}

// =============================================================================
// Utility Functions
// =============================================================================

export function formatPrice(price: number): string {
  return `${(price * 100).toFixed(1)}%`;
}

export function formatVolume(volume: number): string {
  if (volume >= 1_000_000) {
    return `$${(volume / 1_000_000).toFixed(1)}M`;
  }
  if (volume >= 1_000) {
    return `$${(volume / 1_000).toFixed(1)}K`;
  }
  return `$${volume.toFixed(0)}`;
}

export function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);
  
  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  
  return date.toLocaleDateString();
}

export function getSignalColor(score: number): string {
  if (score >= 70) return 'text-red-500';
  if (score >= 50) return 'text-amber-500';
  return 'text-green-500';
}

export function getSignalBgColor(score: number): string {
  if (score >= 70) return 'bg-red-500/10';
  if (score >= 50) return 'bg-amber-500/10';
  return 'bg-green-500/10';
}

export function getSignalTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    'volume_spike': 'Volume Spike',
    'orderbook_imbalance': 'Order Imbalance',
    'price_divergence': 'Price Divergence',
  };
  return labels[type] || type;
}
