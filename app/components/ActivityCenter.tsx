'use client';

import { useEffect, useState } from 'react';
import {
  Activity,
  CheckCircle2,
  Clock3,
  ShieldCheck,
  Wrench,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

type ActivityEvent = {
  id: number;
  event_type: string;
  message: string;
  details: Record<string, unknown> | null;
  created_at: number;
};

type ToolCall = {
  id: number;
  tool_name: string;
  status: string;
  input: Record<string, unknown> | null;
  output: Record<string, unknown> | null;
  started_at: number;
  completed_at: number | null;
};

type Recommendation = {
  id: number;
  type: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  symbol: string | null;
  action: string;
  confidence: number;
  reason: string;
  evidence: Record<string, unknown> | null;
  validation_status: string;
  created_at: number;
};

type ActivityRun = {
  id: number;
  question: string;
  status: string;
  mode: string | null;
  error: string | null;
  started_at: number;
  completed_at: number | null;
  events: ActivityEvent[];
  tool_calls: ToolCall[];
  recommendations: Recommendation[];
};

type ActivityResponse = {
  count: number;
  items: ActivityRun[];
};

function formatTime(timestamp: number | null): string {
  if (!timestamp) return '—';

  return new Date(timestamp * 1000).toLocaleString('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  });
}

function severityClass(severity: Recommendation['severity']): string {
  return `activity-severity activity-severity-${severity.toLowerCase()}`;
}

export default function ActivityCenter() {
  const [runs, setRuns] = useState<ActivityRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expandedRun, setExpandedRun] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadActivity() {
      try {
        setLoading(true);
        setError('');

        const response = await fetch('/api/v1/activity');

        if (!response.ok) {
          throw new Error(`Activity API returned ${response.status}`);
        }

        const data: ActivityResponse = await response.json();

        if (!cancelled) {
          setRuns(data.items ?? []);

          if (data.items?.length) {
            setExpandedRun(data.items[0].id);
          }
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : 'Unable to load activity history.',
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadActivity();

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="feature-page">
      <div className="feature-intro">
        <span className="feature-icon">
          <Clock3 size={18} />
        </span>

        <div>
          <h2>Activity and analysis history</h2>
          <p>
            Every important portfolio analysis is recorded with its tools,
            validation, recommendations, and AI explanation.
          </p>
        </div>
      </div>

      {loading && (
        <div className="feature-card">
          <div className="empty-provider">
            <Activity size={22} />
            <strong>Loading activity...</strong>
            <p>Retrieving the latest analysis history.</p>
          </div>
        </div>
      )}

      {!loading && error && (
        <div className="feature-card">
          <div className="empty-provider">
            <AlertTriangle size={22} />
            <strong>Unable to load activity</strong>
            <p>{error}</p>
          </div>
        </div>
      )}

      {!loading && !error && runs.length === 0 && (
        <div className="feature-card">
          <div className="empty-provider">
            <ShieldCheck size={22} />
            <strong>No analysis activity yet.</strong>
            <p>
              Run a portfolio analysis from the Analyst to create a traceable
              activity record.
            </p>
          </div>
        </div>
      )}

      {!loading && !error && runs.length > 0 && (
        <div className="activity-list">
          {runs.map((run) => {
            const isExpanded = expandedRun === run.id;

            return (
              <div className="feature-card activity-run" key={run.id}>
                <button
                  type="button"
                  className="activity-run-header"
                  onClick={() =>
                    setExpandedRun(isExpanded ? null : run.id)
                  }
                >
                  <div className="activity-run-summary">
                    <div className="activity-run-title-row">
                      <strong>Analysis #{run.id}</strong>

                      <span className="activity-status">
                        <CheckCircle2 size={14} />
                        {run.status}
                      </span>
                    </div>

                    <p>{run.question}</p>

                    <span className="activity-run-time">
                      {formatTime(run.started_at)}
                    </span>
                  </div>

                  {isExpanded ? (
                    <ChevronUp size={18} />
                  ) : (
                    <ChevronDown size={18} />
                  )}
                </button>

                {isExpanded && (
                  <div className="activity-run-details">
                    <div className="activity-meta-grid">
                      <div>
                        <span>Mode</span>
                        <strong>{run.mode ?? '—'}</strong>
                      </div>

                      <div>
                        <span>Events</span>
                        <strong>{run.events.length}</strong>
                      </div>

                      <div>
                        <span>Tool calls</span>
                        <strong>{run.tool_calls.length}</strong>
                      </div>

                      <div>
                        <span>Recommendations</span>
                        <strong>{run.recommendations.length}</strong>
                      </div>
                    </div>

                    <section className="activity-section">
                      <div className="activity-section-heading">
                        <Clock3 size={16} />
                        <h3>Audit timeline</h3>
                      </div>

                      <div className="activity-timeline">
                        {run.events.map((event) => (
                          <div className="activity-event" key={event.id}>
                            <div className="activity-event-marker" />

                            <div>
                              <strong>
                                {event.event_type.replaceAll('_', ' ')}
                              </strong>

                              <p>{event.message}</p>

                              <span>
                                {formatTime(event.created_at)}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </section>

                    <section className="activity-section">
                      <div className="activity-section-heading">
                        <Wrench size={16} />
                        <h3>Tool calls</h3>
                      </div>

                      <div className="activity-tool-list">
                        {run.tool_calls.map((tool) => (
                          <div className="activity-tool" key={tool.id}>
                            <div>
                              <strong>{tool.tool_name}</strong>
                              <span>{tool.status}</span>
                            </div>

                            <small>
                              {formatTime(tool.started_at)}
                            </small>
                          </div>
                        ))}
                      </div>
                    </section>

                    <section className="activity-section">
                      <div className="activity-section-heading">
                        <ShieldCheck size={16} />
                        <h3>Validated recommendations</h3>
                      </div>

                      {run.recommendations.length === 0 ? (
                        <p className="activity-muted">
                          No recommendations were generated for this run.
                        </p>
                      ) : (
                        <div className="activity-recommendations">
                          {run.recommendations.map((recommendation) => (
                            <div
                              className="activity-recommendation"
                              key={recommendation.id}
                            >
                              <div className="activity-recommendation-top">
                                <strong>
                                  {recommendation.type.replaceAll('_', ' ')}
                                </strong>

                                <span
                                  className={severityClass(
                                    recommendation.severity,
                                  )}
                                >
                                  {recommendation.severity}
                                </span>
                              </div>

                              <p>{recommendation.reason}</p>

                              <div className="activity-recommendation-meta">
                                <span>
                                  Symbol: {recommendation.symbol ?? '—'}
                                </span>

                                <span>
                                  Action: {recommendation.action}
                                </span>

                                <span>
                                  Validation:{' '}
                                  {recommendation.validation_status}
                                </span>

                                <span>
                                  Confidence:{' '}
                                  {Math.round(
                                    recommendation.confidence * 100,
                                  )}
                                  %
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </section>

                    {run.error && (
                      <div className="activity-error">
                        <AlertTriangle size={16} />
                        <span>{run.error}</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}