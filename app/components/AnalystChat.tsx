'use client';

import { FormEvent, useEffect, useRef, useState } from 'react';
import {
  Bot,
  ExternalLink,
  Send,
  Sparkles,
  UserRound,
} from 'lucide-react';

import { Holding, Recommendation, inr } from '../lib/types';

type Message = {
  role: 'user' | 'assistant';
  text: string;
  mode?: string;
  citations?: {
    title: string;
    url: string;
  }[];
  limitations?: string[];
  recommendations?: Recommendation[];
};

const API = process.env.NEXT_PUBLIC_API_BASE_URL ?? '';

const suggestions = [
  'How concentrated is my portfolio?',
  'Which holdings contribute most to returns?',
  'What are my largest sector exposures?',
  'What is happening in Indian markets today?',
];

export default function AnalystChat({
  holdings,
  initialQuestion = '',
}: {
  holdings: Holding[];
  initialQuestion?: string;
}) {
  const [messages, setMessages] = useState<Message[]>(
    initialQuestion
      ? [
          {
            role: 'assistant',
            text: 'Ask for current market context. Answers about market news require GROQ_API_KEY on the backend and include web sources.',
          },
        ]
      : [
          {
            role: 'assistant',
            text: 'I can explain portfolio metrics from your confirmed holdings. For current market or news questions, I use grounded web search when Groq is configured. I will label unavailable data.',
          },
        ],
  );

  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const askedInitial = useRef(false);

  async function ask(value: string) {
    const text = value.trim();

    if (!text || loading) {
      return;
    }

    setQuestion('');
    setMessages((messages) => [
      ...messages,
      {
        role: 'user',
        text,
      },
    ]);

    setLoading(true);

    try {
      const response = await fetch(`${API}/api/v1/ai/answer`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          question: text,
          holdings: holdings.map((holding) => ({
            symbol: holding.symbol,
            quantity: holding.qty,
            average_price: holding.avg,
            current_price: holding.ltp,
            sector: holding.sector,
          })),
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || 'Analyst service returned an error',
        );
      }

      setMessages((messages) => [
        ...messages,
        {
          role: 'assistant',
          text: data.answer,
          mode: data.mode,
          citations: data.citations || [],
          limitations: data.limitations || [],
          recommendations: data.recommendations || [],
        },
      ]);
    } catch (error) {
      setMessages((messages) => [
        ...messages,
        {
          role: 'assistant',
          text: `I couldn't reach the analyst service. Start the FastAPI backend and try again. (${
            error instanceof Error ? error.message : 'Network error'
          })`,
          mode: 'offline',
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    void ask(question);
  }

  useEffect(() => {
    if (initialQuestion && !askedInitial.current) {
      askedInitial.current = true;
      void ask(initialQuestion);
    }
  }, [initialQuestion]);

  function renderRecommendationCard(
    recommendation: Recommendation,
  ) {
    return (
      <div
        className={`recommendation-card ${recommendation.severity.toLowerCase()}`}
        key={`${recommendation.type}-${recommendation.symbol}`}
      >
        <div className="recommendation-header">
          <strong>
            {recommendation.type.replaceAll('_', ' ')}
          </strong>

          <span>{recommendation.severity}</span>
        </div>

        {recommendation.symbol && (
          <div className="recommendation-symbol">
            {recommendation.symbol}
          </div>
        )}

        <p className="recommendation-reason">
          {recommendation.reason}
        </p>

        <div className="recommendation-action">
          <strong>Suggested review:</strong>{' '}
          {recommendation.action}
        </div>

        <div className="recommendation-confidence">
          Confidence:{' '}
          {(recommendation.confidence * 100).toFixed(0)}%
        </div>
      </div>
    );
  }

  return (
    <div className="feature-page">
      <div className="feature-intro">
        <span className="feature-icon">
          <Sparkles size={18} />
        </span>

        <div>
          <h2>AI Portfolio Analyst</h2>
          <p>
            Ask about your positions, risk, market moves or
            financial news.
          </p>
        </div>

        <span className="ai-status">
          <i /> EVIDENCE-FIRST
        </span>
      </div>

      <div className="chat-layout">
        <section className="feature-card chat-window">
          <div className="chat-feed">
            {messages.map((message, index) => (
              <article
                className={`chat-message ${message.role}`}
                key={index}
              >
                <span className="chat-avatar">
                  {message.role === 'assistant' ? (
                    <Bot size={15} />
                  ) : (
                    <UserRound size={15} />
                  )}
                </span>

                <div className="chat-bubble">
                  <small>
                    {message.role === 'assistant'
                      ? message.mode?.replaceAll('_', ' ') ||
                        'ANALYST'
                      : 'YOU'}
                  </small>

                  <p>{message.text}</p>

                  {message.recommendations &&
                    message.recommendations.length > 0 && (
                      <div className="recommendation-list">
                        {message.recommendations.map(
                          renderRecommendationCard,
                        )}
                      </div>
                    )}

                  {message.citations &&
                    message.citations.length > 0 && (
                      <div className="citation-list">
                        <strong>Sources</strong>

                        {message.citations.map((citation) => (
                          <a
                            href={citation.url}
                            target="_blank"
                            rel="noreferrer"
                            key={citation.url}
                          >
                            {citation.title}
                            <ExternalLink size={12} />
                          </a>
                        ))}
                      </div>
                    )}

                  {message.limitations?.map((limitation) => (
                    <div
                      className="chat-limit"
                      key={limitation}
                    >
                      Note: {limitation}
                    </div>
                  ))}
                </div>
              </article>
            ))}

            {loading && (
              <article className="chat-message assistant">
                <span className="chat-avatar">
                  <Bot size={15} />
                </span>

                <div className="chat-bubble">
                  <small>ANALYST</small>

                  <p className="typing">
                    Reviewing portfolio evidence and available
                    sources…
                  </p>
                </div>
              </article>
            )}
          </div>

          <form className="chat-form" onSubmit={submit}>
            <input
              value={question}
              onChange={(event) =>
                setQuestion(event.target.value)
              }
              placeholder="Ask about your portfolio or the market…"
              aria-label="Your question"
            />

            <button
              disabled={!question.trim() || loading}
              aria-label="Send question"
            >
              <Send size={16} />
            </button>
          </form>

          <div className="chat-disclaimer">
            With Groq enabled, portfolio questions send confirmed
            holdings and metrics to Groq; market/news searches send
            the query only. Review cited sources.
          </div>
        </section>

        <aside className="feature-card chat-suggestions">
          <h3>Try asking</h3>

          {suggestions.map((suggestion) => (
            <button
              key={suggestion}
              onClick={() => void ask(suggestion)}
            >
              {suggestion}
              <span>→</span>
            </button>
          ))}

          <div className="chat-data-note">
            <strong>Available context</strong>

            <p>
              {holdings.length} confirmed positions · user supplied
              prices · market history{' '}
              {holdings.length
                ? 'not connected'
                : 'unavailable'}
            </p>

            <p>
              Market search needs a backend Groq key. Keys stay on
              the server.
            </p>
          </div>
        </aside>
      </div>
    </div>
  );
}