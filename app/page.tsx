'use client';

import { useEffect, useMemo, useState, type ComponentType } from 'react';

import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  Bell,
  Bot,
  BriefcaseBusiness,
  Calculator as CalculatorIcon,
  ChevronDown,
  CircleHelp,
  Clock3,
  Command,
  Eye,
  FileUp,
  Globe2,
  LayoutDashboard,
  Lightbulb,
  Menu,
  MoreHorizontal,
  Newspaper,
  Search,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Wallet,
  X,
} from 'lucide-react';

import {
  Area,
  AreaChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { Holding, getHoldingStats, inr } from './lib/types';

import ActivityCenter from './components/ActivityCenter';
import AnalystChat from './components/AnalystChat';
import Calculators from './components/Calculators';
import MarketCenter from './components/MarketCenter';
import NewsCenter from './components/NewsCenter';
import PortfolioExplorer from './components/PortfolioExplorer';
import RiskDashboard from './components/RiskDashboard';
import Watchlist from './components/Watchlist';
import OperationsCenter from './components/OperationsCenter';

type NavItem = { label: string; icon: ComponentType<{ size?: number }> };

const navigation: NavItem[] = [
  { label: 'Overview', icon: LayoutDashboard },
  { label: 'Portfolio', icon: BriefcaseBusiness },
  { label: 'Risk', icon: ShieldAlert },
  { label: 'Markets', icon: Globe2 },
  { label: 'News', icon: Newspaper },
  { label: 'Watchlist', icon: Eye },
  { label: 'Calculators', icon: CalculatorIcon },
  { label: 'AI Analyst', icon: Bot },
  { label: 'Activity', icon: Activity },
  { label: 'Operations', icon: Activity },
];

const API = process.env.NEXT_PUBLIC_API_BASE_URL ?? '';

const pageDescriptions: Record<string, string> = {
  Portfolio: 'Explore position returns, contributors, and sector allocation.',
  Risk: 'Review concentration and see which risk measures need more history.',
  Markets: 'Portfolio movers and source-grounded market context.',
  News: 'Search recent market coverage and inspect the original sources.',
  Watchlist: 'Save symbols to follow when verified quote data is connected.',
  Calculators: 'Model SIP, SWP, EMI, CAGR, inflation and retirement scenarios.',
  'AI Analyst':
    'Ask portfolio questions or search current market context with citations.',
  Activity: 'Review portfolio updates and account events.',
};

export default function Home() {
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [history, setHistory] = useState<{ d: string; v: number }[]>([]);
  const [pendingHoldings, setPendingHoldings] =
    useState<Holding[] | null>(null);
  const [period, setPeriod] = useState('3M');
  const [query, setQuery] = useState('');
  const [notice, setNotice] = useState('');
  const [active, setActive] = useState('Overview');
  const [mobileMenu, setMobileMenu] = useState(false);
  const [accountEmail] = useState('DEMO');
  const [portfolioLoading, setPortfolioLoading] = useState(true);
  const [quoteStatus, setQuoteStatus] = useState(
    'Alpha Vantage · on-demand quotes'
  );

  useEffect(() => {
    let live = true;

    fetch(`${API}/api/v1/portfolio/holdings`)
      .then(async (r) => {
        if (!r.ok) {
          throw new Error('Could not load the local demo portfolio.');
        }

        const data = await r.json();

        if (live) {
          const rows = (data.holdings || []).map((h: any) => ({
            symbol: h.symbol,
            name: h.name || h.symbol,
            sector: h.sector || 'Unclassified',
            qty: h.quantity,
            avg: h.average_price,
            ltp: h.current_price,
            day: h.day_change_percent || 0,
          }));

          if (rows.length) {
            setHoldings(rows);
          } else {
            const sample: Holding[] = [
              {
                symbol: 'INFY',
                name: 'Infosys',
                sector: 'Information Technology',
                qty: 12,
                avg: 1450,
                ltp: 1525,
                day: 0.8,
              },
              {
                symbol: 'TCS',
                name: 'Tata Consultancy Services',
                sector: 'Information Technology',
                qty: 5,
                avg: 3720,
                ltp: 3900,
                day: 0.4,
              },
              {
                symbol: 'RELIANCE',
                name: 'Reliance Industries',
                sector: 'Energy',
                qty: 8,
                avg: 2840,
                ltp: 2960,
                day: -0.25,
              },
              {
                symbol: 'HDFCBANK',
                name: 'HDFC Bank',
                sector: 'Banking',
                qty: 15,
                avg: 1680,
                ltp: 1710,
                day: 0.2,
              },
              {
                symbol: 'ICICIBANK',
                name: 'ICICI Bank',
                sector: 'Banking',
                qty: 12,
                avg: 1120,
                ltp: 1190,
                day: 1,
              },
              {
                symbol: 'ITC',
                name: 'ITC Limited',
                sector: 'FMCG',
                qty: 20,
                avg: 450,
                ltp: 435,
                day: -0.3,
              },
            ];

            setHoldings(sample);

            await fetch(`${API}/api/v1/portfolio/holdings`, {
              method: 'PUT',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                holdings: sample.map((h) => ({
                  symbol: h.symbol,
                  quantity: h.qty,
                  average_price: h.avg,
                  current_price: h.ltp,
                  sector: h.sector,
                  name: h.name,
                  day_change_percent: h.day,
                })),
              }),
            });
          }
        }
      })
      .catch(() => {
        if (live) {
          setNotice('Start the FastAPI backend to load local demo data.');
        }
      })
      .finally(() => {
        if (live) {
          setPortfolioLoading(false);
        }
      });

    return () => {
      live = false;
    };
  }, []);

  useEffect(() => {
    let live = true;

    fetch(`${API}/api/v1/market/historical?symbol=INFY&outputsize=compact`)
      .then(async (response) => {
        if (!response.ok) {
          throw new Error('Could not load historical portfolio data.');
        }

        const data = await response.json();

        if (live) {
          const rows = (data.data || [])
            .map((row: any) => ({
              d: row.date,
              v: row.close,
            }))
            .sort(
              (a: { d: string; v: number }, b: { d: string; v: number }) =>
                a.d.localeCompare(b.d)
            );

          setHistory(rows);
        }
      })
      .catch(() => {
        if (live) {
          setHistory([]);
        }
      });

    return () => {
      live = false;
    };
  }, []);

  async function persistPortfolio(next: Holding[]) {
    const response = await fetch(`${API}/api/v1/portfolio/holdings`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        holdings: next.map((h) => ({
          symbol: h.symbol,
          quantity: h.qty,
          average_price: h.avg,
          current_price: h.ltp,
          sector: h.sector,
          name: h.name,
          day_change_percent: h.day,
        })),
      }),
    });

    if (!response.ok) {
      throw new Error(
        'Portfolio could not be saved to the local demo database.'
      );
    }
  }

  async function confirmPortfolio() {
    if (!pendingHoldings) return;

    try {
      await persistPortfolio(pendingHoldings);
      setHoldings(pendingHoldings);
      setPendingHoldings(null);
      setNotice(
        'Portfolio saved locally. Alpha Vantage quotes are requested on demand.'
      );
    } catch (error) {
      setNotice(
        error instanceof Error
          ? error.message
          : 'Portfolio could not be saved.'
      );
    }
  }

  function signOut() {
    setNotice(
      'Local single-user demo mode. No authentication or account sign-in is configured.'
    );
  }

  const total = useMemo(
    () => holdings.reduce((s, h) => s + h.qty * h.ltp, 0),
    [holdings]
  );

  const invested = useMemo(
    () => holdings.reduce((s, h) => s + h.qty * h.avg, 0),
    [holdings]
  );

  const pnl = total - invested;
  const returnPct = invested ? (pnl / invested) * 100 : 0;

  const dayChange = holdings.reduce(
    (s, h) => s + h.qty * h.ltp * (h.day / (100 + h.day)),
    0
  );

  const dayPct = total ? (dayChange / (total - dayChange)) * 100 : 0;

  const sectors = useMemo(
    () =>
      Object.entries(
        holdings.reduce((a, h) => {
          a[h.sector] = (a[h.sector] || 0) + h.qty * h.ltp;
          return a;
        }, {} as Record<string, number>)
      )
        .map(([name, value]) => ({ name, value }))
        .sort((a, b) => b.value - a.value),
    [holdings]
  );

  const filtered = holdings.filter((h) =>
    `${h.symbol} ${h.name} ${h.sector}`
      .toLowerCase()
      .includes(query.toLowerCase())
  );

  async function applyQuote(
    symbol: string,
    quote: { last_price: number; change_percent: number }
  ) {
    const next = holdings.map((h) =>
      h.symbol === symbol
        ? { ...h, ltp: quote.last_price, day: quote.change_percent }
        : h
    );

    setHoldings(next);

    await persistPortfolio(next).catch(() =>
      setNotice('Quote loaded, but the local portfolio price could not be saved.')
    );

    setQuoteStatus(`Alpha Vantage quote loaded for ${symbol}`);
  }

  const colors = [
    '#407f69',
    '#8cae9f',
    '#bccdc3',
    '#d9c6a5',
    '#8c9ca1',
    '#dca78f',
  ];

  async function upload(file?: File) {
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.csv')) {
      setNotice('For this release, upload a CSV portfolio export.');
      return;
    }

    if (file.size > 5_000_000) {
      setNotice('The CSV file must be smaller than 5 MB.');
      return;
    }

    const form = new FormData();
    form.append('file', file);

    try {
      const response = await fetch(`${API}/api/v1/portfolio/preview-csv`, {
        method: 'POST',
        credentials: 'include',
        body: form,
      });

      const body = await response.json();

      if (!response.ok) {
        throw new Error(body.detail || 'Could not read the CSV.');
      }

      const parsed = body.holdings.map((h: any) => ({
        symbol: h.symbol,
        name: h.symbol,
        sector: h.sector || 'Unclassified',
        qty: h.quantity,
        avg: h.average_price,
        ltp: h.current_price,
        day: 0,
      }));

      setPendingHoldings(parsed);
      setNotice(
        'Review the extracted, user-supplied prices before saving.'
      );
    } catch (error) {
      setNotice(
        error instanceof Error
          ? error.message
          : 'Could not read the CSV. Include symbol, quantity, average price, and current price columns.'
      );
    }
  }

  return (
    <main className="app-shell">
      <aside className={`sidebar ${mobileMenu ? 'open' : ''}`}>
        <div className="brand">
          <div className="brand-mark">Z</div>
          <span>
            Zerodha <span className="brand-dot">AI</span> Intelligence
          </span>

          <button
            className="mobile-close icon-btn"
            onClick={() => setMobileMenu(false)}
            aria-label="Close menu"
          >
            <X size={18} />
          </button>
        </div>

        <div className="workspace-label">WORKSPACE</div>

        <nav>
          {navigation.map(({ label, icon: Icon }) => (
            <button
              key={label}
              className={`nav-item ${active === label ? 'selected' : ''}`}
              onClick={() => {
                setActive(label);
                setMobileMenu(false);
              }}
            >
              <Icon size={18} />
              <span>{label}</span>
              {label === 'AI Analyst' && (
                <span className="nav-count">AI</span>
              )}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="advisor-card">
            <div className="advisor-icon">
              <Lightbulb size={16} />
            </div>
            <div>
              <strong>Your analyst</strong>
              <p>Ask about your portfolio</p>
            </div>
            <span className="online-dot" />
          </div>

          <button
            className="nav-item muted"
            onClick={() =>
              setNotice('Help and support are not connected in this demo.')
            }
          >
            <CircleHelp size={18} />
            <span>Help & support</span>
          </button>

          <div className="profile">
            <div className="avatar">
              {accountEmail.slice(0, 1).toUpperCase()}
            </div>

            <div className="account-label">
              <strong title={accountEmail}>{accountEmail}</strong>
              <small>Local demo · no sign-in</small>
            </div>

            <button
              className="profile-signout"
              onClick={signOut}
              aria-label="Local demo mode"
              title="Local demo mode"
            >
              <MoreHorizontal size={19} />
            </button>
          </div>
        </div>
      </aside>

      <section className="main-area">
        <header className="topbar">
          <button
            className="mobile-menu icon-btn"
            onClick={() => setMobileMenu(true)}
            aria-label="Open menu"
          >
            <Menu size={20} />
          </button>

          <div className="breadcrumbs">
            Workspace <span>/</span> <b>{active}</b>
          </div>

          <div className="top-actions">
            <button
              className="search-trigger"
              onClick={() =>
                document.getElementById('holding-search')?.focus()
              }
            >
              <Search size={15} />
              <span>Search holdings</span>
              <kbd>
                <Command size={11} /> K
              </kbd>
            </button>

            <button
              className="icon-btn notification"
              aria-label="Notifications"
              onClick={() => setNotice('No new portfolio updates.')}
            >
              <Bell size={18} />
              <i />
            </button>

            <div className="top-avatar">
              {accountEmail.slice(0, 2).toUpperCase()}
            </div>
          </div>
        </header>

        <div className="content">
          <div className="page-heading">
            <div>
              <div className="eyebrow">
                <span className="eyebrow-dot" />
                {active === 'Overview'
                  ? 'LOCAL DEMO PORTFOLIO'
                  : 'PORTFOLIO INTELLIGENCE WORKSPACE'}
              </div>

              <h1>
                {active === 'Overview' ? 'Your portfolio, in focus.' : active}
              </h1>

              <p>
                {active === 'Overview'
                  ? 'A clear view of what you own, what changed, and what to review.'
                  : pageDescriptions[active] ||
                    'Explore your financial picture with clear sources and assumptions.'}
              </p>
            </div>

            <label className="upload-button">
              <FileUp size={16} /> Import portfolio
              <input
                type="file"
                accept=".csv"
                onChange={(e) => upload(e.target.files?.[0])}
              />
            </label>
          </div>

          {notice && (
            <div className="notice">
              <ShieldCheck size={16} />
              {notice}
              <button
                onClick={() => setNotice('')}
                aria-label="Dismiss"
              >
                <X size={15} />
              </button>
            </div>
          )}

          {active === 'Overview' && (
            <>
              <div className="data-banner">
                <span className="fresh-pip" />
                <span>Alpha Vantage</span>
                <span className="banner-sep">·</span>
                <span>{quoteStatus}</span>
                <span className="banner-sep">·</span>
                <Clock3 size={13} />
                <span>Quotes update on demand</span>
                <button title="About this data">
                  <CircleHelp size={14} />
                </button>
              </div>

              <div className="metric-grid">
                <article className="metric-card primary-metric">
                  <div className="metric-label">
                    CURRENT VALUE
                    <button aria-label="Current value information">
                      <CircleHelp size={14} />
                    </button>
                  </div>

                  <div className="metric-value">{inr(total)}</div>

                  <div className="metric-foot">
                    <span
                      className={
                        returnPct >= 0
                          ? 'positive-pill'
                          : 'negative-pill'
                      }
                    >
                      {returnPct >= 0 ? (
                        <ArrowUpRight size={13} />
                      ) : (
                        <ArrowDownRight size={13} />
                      )}
                      {returnPct >= 0 ? '+' : ''}
                      {returnPct.toFixed(2)}%
                    </span>
                    <span>since purchase</span>
                  </div>

                  <div className="metric-spark">
                    <svg
                      viewBox="0 0 160 46"
                      preserveAspectRatio="none"
                    >
                      <path
                        d="M0 36 C18 33 16 23 31 26 S48 35 61 22 82 18 91 24 107 8 122 14 140 2 160 5"
                        fill="none"
                        stroke="#8bb4a1"
                        strokeWidth="2"
                      />

                      <path
                        d="M0 36 C18 33 16 23 31 26 S48 35 61 22 82 18 91 24 107 8 122 14 140 2 160 5 L160 46 L0 46Z"
                        fill="url(#fade)"
                      />

                      <defs>
                        <linearGradient
                          id="fade"
                          x1="0"
                          x2="0"
                          y1="0"
                          y2="1"
                        >
                          <stop
                            stopColor="#dceae2"
                            stopOpacity=".8"
                          />
                          <stop
                            offset="1"
                            stopColor="#fff"
                            stopOpacity="0"
                          />
                        </linearGradient>
                      </defs>
                    </svg>
                  </div>
                </article>

                <article className="metric-card">
                  <div className="metric-label">
                    INVESTED AMOUNT
                    <button aria-label="Invested amount information">
                      <CircleHelp size={14} />
                    </button>
                  </div>

                  <div className="metric-value">{inr(invested)}</div>

                  <div className="metric-foot subdued">
                    Across {holdings.length} holdings
                  </div>
                </article>

                <article className="metric-card">
                  <div className="metric-label">
                    TOTAL RETURNS
                    <button aria-label="Total returns information">
                      <CircleHelp size={14} />
                    </button>
                  </div>

                  <div
                    className={`metric-value ${
                      pnl >= 0 ? 'positive' : 'negative'
                    }`}
                  >
                    {pnl >= 0 ? '+' : ''}
                    {inr(pnl)}
                  </div>

                  <div className="metric-foot">
                    <span
                      className={
                        pnl >= 0 ? 'positive-text' : 'negative'
                      }
                    >
                      {returnPct >= 0 ? (
                        <ArrowUpRight size={14} />
                      ) : (
                        <ArrowDownRight size={14} />
                      )}
                      {returnPct >= 0 ? '+' : ''}
                      {returnPct.toFixed(2)}%
                    </span>
                    <span>absolute return</span>
                  </div>
                </article>

                <article className="metric-card">
                  <div className="metric-label">
                    TODAY’S CHANGE
                    <span title="Calculated from per-holding daily changes in this illustrative snapshot">
                      <CircleHelp size={14} />
                    </span>
                  </div>

                  <div
                    className={`metric-value ${
                      dayChange >= 0 ? 'positive' : 'negative'
                    }`}
                  >
                    {dayChange >= 0 ? '+' : ''}
                    {inr(dayChange)}
                  </div>

                  <div className="metric-foot">
                    <span
                      className={
                        dayChange >= 0 ? 'positive-text' : 'negative'
                      }
                    >
                      {dayChange >= 0 ? (
                        <ArrowUpRight size={14} />
                      ) : (
                        <ArrowDownRight size={14} />
                      )}
                      {dayPct >= 0 ? '+' : ''}
                      {dayPct.toFixed(2)}%
                    </span>
                    <span>vs previous close</span>
                  </div>
                </article>
              </div>

              <div className="dashboard-grid">
                <section className="panel performance-panel">
                  <div className="panel-heading">
                    <div>
                      <h2>Portfolio performance</h2>
                      <p>Value over time</p>
                    </div>

                    <div className="chart-controls">
                      {['1M', '3M'].map((p) => (
                        <button
                          className={period === p ? 'active' : ''}
                          onClick={() => setPeriod(p)}
                          key={p}
                        >
                          {p}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="chart-legend">
                    <span className="legend-key" /> Your portfolio
                    <span className="legend-muted">
                      NIFTY 50 comparison unavailable
                    </span>
                  </div>

                  <div className="performance-chart">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart
                        data={period === '1M' ? history.slice(-22) : history}
                        margin={{
                          top: 12,
                          right: 4,
                          left: 0,
                          bottom: 0,
                        }}
                      >
                        <defs>
                          <linearGradient
                            id="portfolioFill"
                            x1="0"
                            y1="0"
                            x2="0"
                            y2="1"
                          >
                            <stop
                              offset="0%"
                              stopColor="#548b74"
                              stopOpacity={0.18}
                            />
                            <stop
                              offset="100%"
                              stopColor="#548b74"
                              stopOpacity={0}
                            />
                          </linearGradient>
                        </defs>

                        <CartesianGrid
                          vertical={false}
                          stroke="#edf0ed"
                        />

                        <XAxis
                          dataKey="d"
                          axisLine={false}
                          tickLine={false}
                          tick={{
                            fontSize: 11,
                            fill: '#929a94',
                          }}
                          dy={10}
                        />

                        <YAxis
                          domain={[
                            'dataMin - 12000',
                            'dataMax + 12000',
                          ]}
                          axisLine={false}
                          tickLine={false}
                          tick={{
                            fontSize: 11,
                            fill: '#929a94',
                          }}
                          tickFormatter={(v) =>
                            `₹${Math.round(v / 1000)}k`
                          }
                          width={48}
                        />

                        <Tooltip
                          formatter={(v: any) => [
                            inr(v),
                            'Portfolio value',
                          ]}
                          contentStyle={{
                            border: '1px solid #e8ece8',
                            borderRadius: 10,
                            fontSize: 12,
                            boxShadow:
                              '0 8px 24px #29382a12',
                          }}
                        />

                        <Area
                          type="monotone"
                          dataKey="v"
                          stroke="#548b74"
                          strokeWidth={2.3}
                          fill="url(#portfolioFill)"
                          activeDot={{
                            r: 4,
                            fill: '#548b74',
                            stroke: '#fff',
                            strokeWidth: 2,
                          }}
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>

                  <div className="chart-footnote">
                    <span>
                      <i />
                      Historical market data connected via Alpha Vantage
                    </span>

                    <button
                      onClick={() =>
                        setNotice(
                          'The chart currently uses verified INFY historical data. A full portfolio time series requires historical prices for every holding.'
                        )
                      }
                    >
                      Why no benchmark?
                    </button>
                  </div>
                </section>

                <section className="panel allocation-panel">
                  <div className="panel-heading">
                    <div>
                      <h2>Where it’s invested</h2>
                      <p>Allocation by sector</p>
                    </div>

                    <button
                      className="more-button"
                      aria-label="More allocation options"
                      onClick={() =>
                        setNotice(
                          'Allocation uses the current values and sectors supplied for these holdings.'
                        )
                      }
                    >
                      <MoreHorizontal size={20} />
                    </button>
                  </div>

                  <div className="allocation-body">
                    <div className="donut-wrap">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={sectors}
                            dataKey="value"
                            nameKey="name"
                            innerRadius={53}
                            outerRadius={72}
                            paddingAngle={3}
                            stroke="none"
                          >
                            {sectors.map((_, i) => (
                              <Cell
                                key={i}
                                fill={colors[i % colors.length]}
                              />
                            ))}
                          </Pie>

                          <Tooltip
                            formatter={(v: any) => [
                              inr(v),
                              'Value',
                            ]}
                          />
                        </PieChart>
                      </ResponsiveContainer>

                      <div className="donut-center">
                        <strong>{sectors.length}</strong>
                        <span>sectors</span>
                      </div>
                    </div>

                    <div className="sector-list">
                      {sectors.slice(0, 5).map((s, i) => (
                        <div className="sector-row" key={s.name}>
                          <i
                            style={{
                              background:
                                colors[i % colors.length],
                            }}
                          />
                          <span>{s.name}</span>
                          <b>
                            {(
                              (s.value / total) *
                              100
                            ).toFixed(1)}
                            %
                          </b>
                        </div>
                      ))}
                    </div>
                  </div>

                  <button
                    className="text-link"
                    onClick={() =>
                      setNotice(
                        'Sector allocation is calculated from current holding values. Missing sectors appear as Unclassified.'
                      )
                    }
                  >
                    View allocation breakdown <span>→</span>
                  </button>
                </section>
              </div>

              <div className="bottom-grid">
                <section className="panel holdings-panel">
                  <div className="panel-heading holdings-heading">
                    <div>
                      <h2>
                        Your holdings{' '}
                        <span className="count-badge">
                          {holdings.length}
                        </span>
                      </h2>
                      <p>Equities · NSE</p>
                    </div>

                    <div className="holdings-actions">
                      <div className="table-search">
                        <Search size={15} />
                        <input
                          id="holding-search"
                          placeholder="Find a holding"
                          value={query}
                          onChange={(e) =>
                            setQuery(e.target.value)
                          }
                        />
                      </div>

                      <button className="filter-button">
                        All holdings
                        <ChevronDown size={14} />
                      </button>
                    </div>
                  </div>

                  <div className="table-scroll">
                    <table>
                      <thead>
                        <tr>
                          <th>INSTRUMENT</th>
                          <th>QTY.</th>
                          <th>AVG. COST</th>
                          <th>
                            LTP{' '}
                            <span
                              className="demo-dot"
                              title={quoteStatus}
                            />
                          </th>
                          <th>RETURNS</th>
                          <th>TODAY</th>
                          <th />
                        </tr>
                      </thead>

                      <tbody>
                        {filtered.map((h) => {
                          const ret =
                            (h.ltp - h.avg) * h.qty;
                          const pct =
                            (h.ltp / h.avg - 1) * 100;

                          return (
                            <tr key={h.symbol}>
                              <td>
                                <div className="instrument">
                                  <span className="company-logo">
                                    {h.symbol.slice(0, 1)}
                                  </span>

                                  <div>
                                    <strong>{h.symbol}</strong>
                                    <small>{h.name}</small>
                                  </div>
                                </div>
                              </td>

                              <td>{h.qty}</td>
                              <td>{inr(h.avg)}</td>
                              <td>{inr(h.ltp)}</td>

                              <td>
                                <strong
                                  className={
                                    ret >= 0
                                      ? 'positive'
                                      : 'negative'
                                  }
                                >
                                  {ret >= 0 ? '+' : ''}
                                  {inr(ret)}
                                </strong>

                                <small
                                  className={
                                    ret >= 0
                                      ? 'positive'
                                      : 'negative'
                                  }
                                >
                                  {pct >= 0 ? '+' : ''}
                                  {pct.toFixed(2)}%
                                </small>
                              </td>

                              <td>
                                <span
                                  className={`day-change ${
                                    h.day >= 0
                                      ? 'up'
                                      : 'down'
                                  }`}
                                >
                                  {h.day >= 0 ? '+' : ''}
                                  {h.day.toFixed(2)}%
                                </span>
                              </td>

                              <td>
                                <button
                                  className="row-more"
                                  aria-label={`Options for ${h.symbol}`}
                                  onClick={() =>
                                    setNotice(
                                      `${h.symbol}: additional holding actions are not enabled in this demo.`
                                    )
                                  }
                                >
                                  <MoreHorizontal size={17} />
                                </button>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>

                    {filtered.length === 0 && (
                      <div className="empty-search">
                        {holdings.length
                          ? `No holdings match “${query}”`
                          : portfolioLoading
                          ? 'Loading your portfolio…'
                          : 'No holdings yet. Import your portfolio CSV to get started.'}
                      </div>
                    )}
                  </div>

                  <div className="table-footer">
                    <span>
                      Showing {filtered.length} of{' '}
                      {holdings.length} holdings
                    </span>

                    <button
                      onClick={() =>
                        setNotice(
                          'All saved account holdings are shown here.'
                        )
                      }
                    >
                      View all holdings <span>→</span>
                    </button>
                  </div>
                </section>

                <section className="panel insights-panel">
                  <div className="panel-heading">
                    <div>
                      <h2>Worth a closer look</h2>
                      <p>Observations from your portfolio</p>
                    </div>

                    <span className="ai-tag">
                      <Sparkles size={12} /> INSIGHTS
                    </span>
                  </div>

                  <article className="insight-card">
                    <div className="insight-icon amber">
                      <Activity size={16} />
                    </div>

                    <div>
                      <div className="insight-meta">
                        CONCENTRATION <span>·</span> REVIEW
                      </div>

                      <h3>
                        {sectors[0]?.name ||
                          'No sector data'}{' '}
                        is{' '}
                        {(
                          ((sectors[0]?.value || 0) /
                            Math.max(total, 1)) *
                          100
                        ).toFixed(0)}
                        % of this snapshot
                      </h3>

                      <p>
                        {holdings
                          .filter(
                            (h) =>
                              h.sector ===
                              sectors[0]?.name
                          )
                          .sort(
                            (a, b) =>
                              b.qty * b.ltp -
                              a.qty * a.ltp
                          )
                          .slice(0, 2)
                          .map((h) => h.symbol)
                          .join(' and ') ||
                          'Upload holdings with sector labels for a more useful breakdown.'}{' '}
                        are the largest names in this sector.
                      </p>

                      <button
                        onClick={() =>
                          setNotice(
                            'Based on sector tags in the imported holdings. This is an observation, not a recommendation.'
                          )
                        }
                      >
                        See the numbers <span>→</span>
                      </button>
                    </div>
                  </article>

                  <article className="insight-card second">
                    <div className="insight-icon green">
                      <ArrowUpRight size={16} />
                    </div>

                    <div>
                      <div className="insight-meta">
                        TOP CONTRIBUTOR <span>·</span> THIS
                        SNAPSHOT
                      </div>

                      <h3>
                        {[...holdings].sort(
                          (a, b) =>
                            (b.ltp - b.avg) * b.qty -
                            (a.ltp - a.avg) * a.qty
                        )[0]?.symbol ||
                          'Add holdings to see contributors'}{' '}
                        leads total returns
                      </h3>

                      <p>
                        Returns are calculated from average
                        cost and current value.
                      </p>

                      <button
                        onClick={() =>
                          setNotice(
                            'Contribution here means unrealized gain relative to the listed average cost.'
                          )
                        }
                      >
                        View contribution <span>→</span>
                      </button>
                    </div>
                  </article>

                  <div className="insight-disclaimer">
                    <ShieldCheck size={14} /> Informational
                    observations · No buy or sell advice
                  </div>
                </section>
              </div>

              <footer className="page-footer">
                <span>
                  © 2026 Zerodha AI Intelligence · Unofficial demo
                </span>

                <span>
                  Unofficial demo - not affiliated with Zerodha{' '}
                  <i>·</i> Not investment advice
                </span>

                <button
                  onClick={() =>
                    setNotice(
                      'Demo prices remain until you request an Alpha Vantage quote.'
                    )
                  }
                >
                  Data limitations
                </button>
              </footer>
            </>
          )}

          {active === 'Portfolio' && (
            <PortfolioExplorer holdings={holdings} />
          )}

          {active === 'Risk' && (
            <RiskDashboard holdings={holdings} />
          )}

          {active === 'Markets' && (
            <MarketCenter
              holdings={holdings}
              onQuote={applyQuote}
            />
          )}

          {active === 'News' && (
            <NewsCenter holdings={holdings} />
          )}

          {active === 'Watchlist' && <Watchlist />}

          {active === 'Calculators' && <Calculators />}

          {active === 'AI Analyst' && (
            <AnalystChat holdings={holdings} />
          )}

          {active === 'Activity' && <ActivityCenter />}

          {active === 'Operations' && <OperationsCenter />}
        </div>

        {pendingHoldings && (
          <div
            className="modal-backdrop"
            role="presentation"
          >
            <section
              className="review-modal"
              role="dialog"
              aria-modal="true"
              aria-labelledby="review-title"
            >
              <div className="modal-heading">
                <div>
                  <span className="eyebrow">
                    PORTFOLIO IMPORT
                  </span>

                  <h2 id="review-title">
                    Review your holdings
                  </h2>

                  <p>
                    {pendingHoldings.length} rows detected ·
                    Check the extracted values before analysis.
                  </p>
                </div>

                <button
                  className="icon-btn"
                  onClick={() => setPendingHoldings(null)}
                  aria-label="Close review"
                >
                  <X size={18} />
                </button>
              </div>

              <div className="review-table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>SYMBOL</th>
                      <th>SECTOR</th>
                      <th>QUANTITY</th>
                      <th>AVG. PRICE</th>
                      <th>CURRENT PRICE</th>
                    </tr>
                  </thead>

                  <tbody>
                    {pendingHoldings
                      .slice(0, 20)
                      .map((h, i) => (
                        <tr
                          key={`${h.symbol}-${i}`}
                        >
                          <td>{h.symbol}</td>
                          <td>{h.sector}</td>
                          <td>{h.qty}</td>
                          <td>{inr(h.avg)}</td>
                          <td>{inr(h.ltp)}</td>
                        </tr>
                      ))}
                  </tbody>
                </table>

                {pendingHoldings.length > 20 && (
                  <p className="review-limit">
                    Showing first 20 rows of{' '}
                    {pendingHoldings.length}.
                  </p>
                )}
              </div>

              <div className="modal-actions">
                <button
                  className="cancel-button"
                  onClick={() => setPendingHoldings(null)}
                >
                  Cancel
                </button>

                <button
                  className="confirm-button"
                  onClick={confirmPortfolio}
                >
                  Confirm &amp; Analyze
                </button>
              </div>

              <p className="review-disclaimer">
                Imported values are user supplied. Verify
                symbols, quantities and prices; no market
                lookup is performed.
              </p>
            </section>
          </div>
        )}
      </section>
    </main>
  );
}