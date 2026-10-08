'use client';

import { useEffect, useState } from 'react';

type OperationsMetrics = {
  api_requests: number;
  api_success_rate: number;
  api_average_latency_ms: number;
  api_errors: number;

  ai_requests: number;
  ai_success_rate: number;
  ai_errors: number;

  tool_calls: number;
  tool_success_rate: number;
  tool_average_latency_ms: number;

  alpha_vantage_requests_used: number;
  alpha_vantage_daily_limit: number;
};

const API = process.env.NEXT_PUBLIC_API_BASE_URL ?? '';

export default function OperationsCenter() {
  const [metrics, setMetrics] = useState<OperationsMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  async function loadMetrics() {
    setLoading(true);
    setError('');

    try {
      const response = await fetch(
        `${API}/api/v1/operations/metrics`,
        { cache: 'no-store' }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Could not load operations metrics.');
      }

      setMetrics(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Could not load operations metrics.'
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadMetrics();
  }, []);

  if (loading) {
    return (
      <div className="feature-page">
        <div className="feature-intro">
          <div>
            <span className="eyebrow">OPERATIONS</span>
            <h2>System observability</h2>
            <p>Loading internal system metrics…</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !metrics) {
    return (
      <div className="feature-page">
        <div className="feature-intro">
          <div>
            <span className="eyebrow">OPERATIONS</span>
            <h2>System observability</h2>
            <p>Unable to load operations metrics.</p>
          </div>
        </div>

        <section className="feature-card">
          <strong>Metrics unavailable</strong>
          <p className="data-note">{error || 'No metrics returned.'}</p>
          <button className="confirm-button" onClick={() => void loadMetrics()}>
            Retry
          </button>
        </section>
      </div>
    );
  }

  const alphaUsagePercent =
    metrics.alpha_vantage_daily_limit > 0
      ? (metrics.alpha_vantage_requests_used /
          metrics.alpha_vantage_daily_limit) *
        100
      : 0;

  return (
    <div className="feature-page">
      <div className="feature-intro">
        <div>
          <span className="eyebrow">OPERATIONS / OBSERVABILITY</span>
          <h2>System health</h2>
          <p>
            Internal monitoring for API requests, AI workflows, tool execution
            and provider usage.
          </p>
        </div>

        <span className="offline-label">LIVE METRICS</span>
      </div>

      <div className="detail-metrics">
        <div>
          <span>API Requests</span>
          <strong>{metrics.api_requests}</strong>
          <small>{metrics.api_success_rate.toFixed(1)}% success</small>
        </div>

        <div>
          <span>AI Requests</span>
          <strong>{metrics.ai_requests}</strong>
          <small>{metrics.ai_success_rate.toFixed(1)}% success</small>
        </div>

        <div>
          <span>Tool Calls</span>
          <strong>{metrics.tool_calls}</strong>
          <small>{metrics.tool_success_rate.toFixed(1)}% success</small>
        </div>

        <div>
          <span>API Errors</span>
          <strong>{metrics.api_errors}</strong>
          <small>{metrics.ai_errors} AI errors</small>
        </div>
      </div>

      <div className="operations-grid">
        <section className="feature-card">
          <div className="section-heading">
            <div>
              <h3>API performance</h3>
              <p>HTTP request volume, reliability and latency.</p>
            </div>
          </div>

          <div className="operations-stat-list">
            <div>
              <span>Requests</span>
              <strong>{metrics.api_requests}</strong>
            </div>

            <div>
              <span>Success rate</span>
              <strong>{metrics.api_success_rate.toFixed(1)}%</strong>
            </div>

            <div>
              <span>Average latency</span>
              <strong>{metrics.api_average_latency_ms.toFixed(2)} ms</strong>
            </div>

            <div>
              <span>Errors</span>
              <strong>{metrics.api_errors}</strong>
            </div>
          </div>
        </section>

        <section className="feature-card">
          <div className="section-heading">
            <div>
              <h3>AI workflows</h3>
              <p>Analysis runs recorded by the backend.</p>
            </div>
          </div>

          <div className="operations-stat-list">
            <div>
              <span>AI requests</span>
              <strong>{metrics.ai_requests}</strong>
            </div>

            <div>
              <span>Success rate</span>
              <strong>{metrics.ai_success_rate.toFixed(1)}%</strong>
            </div>

            <div>
              <span>Errors</span>
              <strong>{metrics.ai_errors}</strong>
            </div>
          </div>
        </section>

        <section className="feature-card">
          <div className="section-heading">
            <div>
              <h3>Tool execution</h3>
              <p>Internal tool-call reliability and timing.</p>
            </div>
          </div>

          <div className="operations-stat-list">
            <div>
              <span>Tool calls</span>
              <strong>{metrics.tool_calls}</strong>
            </div>

            <div>
              <span>Success rate</span>
              <strong>{metrics.tool_success_rate.toFixed(1)}%</strong>
            </div>

            <div>
              <span>Average latency</span>
              <strong>{metrics.tool_average_latency_ms.toFixed(2)} ms</strong>
            </div>
          </div>
        </section>

        <section className="feature-card">
          <div className="section-heading">
            <div>
              <h3>Alpha Vantage</h3>
              <p>Daily provider usage against the configured limit.</p>
            </div>
          </div>

          <div className="provider-usage">
            <div className="provider-usage-heading">
              <strong>
                {metrics.alpha_vantage_requests_used} / {metrics.alpha_vantage_daily_limit} requests
              </strong>
              <span>{alphaUsagePercent.toFixed(1)}% used</span>
            </div>

            <div className="provider-usage-track">
              <div
                className="provider-usage-fill"
                style={{ width: `${Math.min(alphaUsagePercent, 100)}%` }}
              />
            </div>

            <small>
              Requests used today under the configured daily budget.
            </small>
          </div>
        </section>
      </div>

      <p className="data-note wide-note">
        Metrics are collected from the local SQLite observability records.
        They describe system activity and are not financial performance
        measurements.
      </p>
    </div>
  );
}