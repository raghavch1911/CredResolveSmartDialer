
import { useCallback, useEffect, useState } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowDownLeft,
  ArrowUpRight,
  Bot,
  CheckCircle2,
  ChevronRight,
  CircleDot,
  Gauge,
  LayoutDashboard,
  Phone,
  PhoneCall,
  Plus,
  RefreshCw,
  ShieldCheck,
  Users,
  UserRound,
  XCircle,
} from "lucide-react";
import "./App.css";

const API = "http://127.0.0.1:8000";

function MetricCard({ icon: Icon, label, value, note, color }) {
  return (
    <div className="metric-card">
      <div className={`metric-icon ${color}`}><Icon size={19} /></div>
      <p className="metric-label">{label}</p>
      <h2>{value}</h2>
      <span className="metric-note">{note}</span>
    </div>
  );
}

function App() {
  const [agents, setAgents] = useState([]);
  const [borrowers, setBorrowers] = useState([]);
  const [calls, setCalls] = useState([]);
  const [providers, setProviders] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const [agentName, setAgentName] = useState("");
  const [borrowerName, setBorrowerName] = useState("");
  const [phone, setPhone] = useState("");
  const [provider, setProvider] = useState("mock_a");
  const [answerRate, setAnswerRate] = useState("0.5");
  const [maxBatch, setMaxBatch] = useState("5");

  const request = async (path, options = {}) => {
    const response = await fetch(`${API}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(data.detail || `Request failed: ${response.status}`);
    }

    return data;
  };

  const refresh = useCallback(async () => {
    try {
      setError("");
      const [agentData, borrowerData, callData, providerData] =
        await Promise.all([
          request("/agents"),
          request("/borrowers"),
          request("/calls"),
          request("/providers/health"),
        ]);

      setAgents(agentData);
      setBorrowers(borrowerData);
      setCalls(callData);
      setProviders(providerData);
    } catch (err) {
      setError(
        `${err.message}. Make sure the FastAPI backend is running at ${API}.`
      );
    }
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 5000);
    return () => clearInterval(interval);
  }, [refresh]);

  const runAction = async (action, successMessage) => {
    setLoading(true);
    setError("");
    setNotice("");

    try {
      const result = await action();
      setNotice(successMessage);
      await refresh();
      return result;
    } catch (err) {
      setError(err.message);
      return null;
    } finally {
      setLoading(false);
    }
  };

  const addAgent = async (event) => {
    event.preventDefault();
    if (!agentName.trim()) return;

    const result = await runAction(
      () => request("/agents", {
        method: "POST",
        body: JSON.stringify({ name: agentName.trim() }),
      }),
      "Agent registered successfully."
    );

    if (result) setAgentName("");
  };

  const addBorrower = async (event) => {
    event.preventDefault();
    if (!borrowerName.trim() || !phone.trim()) return;

    const result = await runAction(
      () => request("/borrowers", {
        method: "POST",
        body: JSON.stringify({
          name: borrowerName.trim(),
          phone: phone.trim(),
        }),
      }),
      "Borrower added to the queue."
    );

    if (result) {
      setBorrowerName("");
      setPhone("");
    }
  };

  const initiateCall = () =>
    runAction(
      () => request(
        `/calls/initiate?provider=${encodeURIComponent(provider)}`,
        { method: "POST" }
      ),
      "Call initiation request processed."
    );

  const runPredictive = () =>
    runAction(
      () => request(
        `/dial/predictive?answer_rate=${encodeURIComponent(answerRate)}` +
        `&provider_healthy=true&provider=${encodeURIComponent(provider)}` +
        `&max_batch=${encodeURIComponent(maxBatch)}`,
        { method: "POST" }
      ),
      "Predictive dialing cycle completed."
    );

  const availableAgents = agents.filter(
    (agent) => agent.status === "AVAILABLE"
  ).length;

  const activeCalls = calls.filter((call) =>
    ["RESERVED", "INITIATED", "RINGING", "ANSWERED", "CONNECTED"].includes(
      call.status
    )
  ).length;

  const connectedCalls = calls.filter(
    (call) => ["ANSWERED", "CONNECTED"].includes(call.status)
  ).length;

  const queuedBorrowers = borrowers.filter(
    (borrower) => borrower.status === "QUEUED"
  ).length;

  const terminalCalls = calls.filter((call) =>
    ["COMPLETED", "FAILED", "CANCELLED"].includes(call.status)
  );

  const completedCalls = calls.filter(
    (call) => call.status === "COMPLETED"
  ).length;

  const failedCalls = calls.filter(
    (call) => call.status === "FAILED"
  ).length;

  const healthEntries = Object.entries(providers);
  const providersHealthy = healthEntries.every(
    ([, value]) => value.state !== "OPEN"
  );

  const formatTime = (value) => {
    if (!value) return "—";
    return value.includes("T")
      ? new Date(value).toLocaleTimeString()
      : value;
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><PhoneCall size={23} /></div>
          <div>
            <h2>CredResolve</h2>
            <span>SMARTDIALER</span>
          </div>
        </div>

        <div className="workspace-label">WORKSPACE</div>

        <nav className="nav-list">
          <a className="nav-item active" href="#overview">
            <LayoutDashboard size={18} /> Overview
          </a>
          <a className="nav-item" href="#agents">
            <Users size={18} /> Agents
          </a>
          <a className="nav-item" href="#borrowers">
            <UserRound size={18} /> Borrowers
          </a>
          <a className="nav-item" href="#calls">
            <Phone size={18} /> Call activity
          </a>
          <a className="nav-item" href="#pacing">
            <Gauge size={18} /> Dialing controls
          </a>
        </nav>

        <div className="sidebar-bottom">
          <div className="safety-card">
            <ShieldCheck size={21} />
            <strong>Safety first</strong>
            <p>Every call request is subject to backend capacity checks.</p>
          </div>
          <div className="connection-label">
            <span className="live-dot" />
            Local API
            <span className="connection-value">
              {error ? "Disconnected" : "Connected"}
            </span>
          </div>
          <span className="version">Prototype v0.2.0</span>
        </div>
      </aside>

      <main className="main-content" id="overview">
        <header className="topbar">
          <div>
            <div className="eyebrow">OPERATIONS / OVERVIEW</div>
            <h1>Dialer Overview</h1>
            <p>Monitor agent capacity, dialing activity and provider health.</p>
          </div>
          <button className="button secondary" onClick={refresh}>
            <RefreshCw size={16} /> Refresh
          </button>
        </header>

        {error && (
          <div className="alert error-alert">
            <AlertTriangle size={18} />
            <span>{error}</span>
            <button onClick={() => setError("")}><XCircle size={17} /></button>
          </div>
        )}

        {notice && (
          <div className="alert success-alert">
            <CheckCircle2 size={18} />
            <span>{notice}</span>
            <button onClick={() => setNotice("")}><XCircle size={17} /></button>
          </div>
        )}

        <section className="metrics-grid">
          <MetricCard
            icon={Users}
            label="Available agents"
            value={availableAgents}
            note={`${agents.length} total registered`}
            color="purple"
          />
          <MetricCard
            icon={Activity}
            label="Active calls"
            value={activeCalls}
            note={`${connectedCalls} answered or connected`}
            color="blue"
          />
          <MetricCard
            icon={UserRound}
            label="Borrowers queued"
            value={queuedBorrowers}
            note="Waiting for allocation"
            color="orange"
          />
          <MetricCard
            icon={ShieldCheck}
            label="Provider health"
            value={healthEntries.length === 0 ? "—" : providersHealthy ? "Healthy" : "Degraded"}
            note={`${failedCalls} failed calls recorded`}
            color={providersHealthy ? "green" : "red"}
          />
        </section>

        <div className="content-grid">
          <section className="panel" id="pacing">
            <div className="panel-heading">
              <div>
                <span className="section-kicker">DIALING ENGINE</span>
                <h2>Dialing controls</h2>
              </div>
              <span className="mode-pill"><CircleDot size={12} /> Safety gated</span>
            </div>

            <div className="control-block">
              <label htmlFor="provider">Telecom provider</label>
              <select
                id="provider"
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
              >
                <option value="mock_a">Mock Provider A · Reliable</option>
                <option value="mock_b">Mock Provider B · Unreliable</option>
              </select>
            </div>

            <button
              className="button primary full-width"
              disabled={loading}
              onClick={initiateCall}
            >
              <PhoneCall size={17} />
              Initiate one call
              <ChevronRight size={17} />
            </button>

            <div className="subsection-divider" />

            <div className="subsection-title">
              <Bot size={18} />
              <h3>Predictive pacing</h3>
            </div>
            <p className="muted">
              Request a dialing batch. The backend independently checks
              available agents and queued borrowers.
            </p>

            <div className="form-row">
              <div className="control-block">
                <label htmlFor="answerRate">Expected answer rate</label>
                <select
                  id="answerRate"
                  value={answerRate}
                  onChange={(e) => setAnswerRate(e.target.value)}
                >
                  <option value="0.2">20%</option>
                  <option value="0.35">35%</option>
                  <option value="0.5">50%</option>
                  <option value="0.7">70%</option>
                  <option value="0.9">90%</option>
                </select>
              </div>
              <div className="control-block">
                <label htmlFor="maxBatch">Maximum batch</label>
                <select
                  id="maxBatch"
                  value={maxBatch}
                  onChange={(e) => setMaxBatch(e.target.value)}
                >
                  <option value="1">1 call</option>
                  <option value="3">3 calls</option>
                  <option value="5">5 calls</option>
                  <option value="10">10 calls</option>
                  <option value="20">20 calls</option>
                </select>
              </div>
            </div>

            <button
              className="button secondary full-width"
              disabled={loading}
              onClick={runPredictive}
            >
              <Gauge size={17} />
              Run predictive cycle
              <ArrowUpRight size={16} />
            </button>
            {loading && <p className="muted small">Processing request…</p>}
          </section>

          <section className="panel" id="agents">
            <div className="panel-heading">
              <div>
                <span className="section-kicker">WORKFORCE</span>
                <h2>Agents</h2>
              </div>
              <span className="count-pill">{agents.length}</span>
            </div>

            <form className="inline-form" onSubmit={addAgent}>
              <input
                value={agentName}
                onChange={(e) => setAgentName(e.target.value)}
                placeholder="New agent name"
                aria-label="New agent name"
                required
              />
              <button className="button icon-button primary" title="Add agent">
                <Plus size={18} />
              </button>
            </form>

            <div className="data-list">
              {agents.length === 0 ? (
                <div className="empty-state">No agents registered yet.</div>
              ) : agents.slice().reverse().slice(0, 6).map((agent) => (
                <div className="list-row" key={agent.id}>
                  <div className="avatar">{agent.name.slice(0, 1).toUpperCase()}</div>
                  <div className="list-main">
                    <strong>{agent.name}</strong>
                    <span>Agent #{agent.id}</span>
                  </div>
                  <span className={`status-badge ${agent.status.toLowerCase()}`}>
                    {agent.status.replace("_", " ")}
                  </span>
                </div>
              ))}
            </div>
          </section>

          <section className="panel" id="borrowers">
            <div className="panel-heading">
              <div>
                <span className="section-kicker">CONTACT QUEUE</span>
                <h2>Borrowers</h2>
              </div>
              <span className="count-pill">{borrowers.length}</span>
            </div>

            <form className="stack-form" onSubmit={addBorrower}>
              <input
                value={borrowerName}
                onChange={(e) => setBorrowerName(e.target.value)}
                placeholder="Borrower name"
                aria-label="Borrower name"
                required
              />
              <div className="inline-form">
                <input
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="Phone number"
                  aria-label="Phone number"
                  required
                />
                <button className="button icon-button primary" title="Add borrower">
                  <Plus size={18} />
                </button>
              </div>
            </form>

            <div className="data-list">
              {borrowers.length === 0 ? (
                <div className="empty-state">No borrowers in the queue.</div>
              ) : borrowers.slice().reverse().slice(0, 5).map((borrower) => (
                <div className="list-row" key={borrower.id}>
                  <div className="avatar borrower-avatar">
                    {borrower.name.slice(0, 1).toUpperCase()}
                  </div>
                  <div className="list-main">
                    <strong>{borrower.name}</strong>
                    <span>{borrower.phone}</span>
                  </div>
                  <span className={`status-badge ${borrower.status.toLowerCase()}`}>
                    {borrower.status}
                  </span>
                </div>
              ))}
            </div>
          </section>

          <section className="panel" id="calls">
            <div className="panel-heading">
              <div>
                <span className="section-kicker">LIVE MONITOR</span>
                <h2>Recent calls</h2>
              </div>
              <span className="count-pill">{calls.length}</span>
            </div>

            <div className="call-summary">
              <div>
                <span>Completed</span>
                <strong>{completedCalls}</strong>
              </div>
              <div>
                <span>Failed</span>
                <strong>{failedCalls}</strong>
              </div>
              <div>
                <span>Active</span>
                <strong>{activeCalls}</strong>
              </div>
            </div>

            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Call</th>
                    <th>Provider</th>
                    <th>Status</th>
                    <th>Created</th>
                  </tr>
                </thead>
                <tbody>
                  {calls.length === 0 ? (
                    <tr>
                      <td colSpan="4" className="empty-cell">No calls yet.</td>
                    </tr>
                  ) : calls.slice(0, 8).map((call) => (
                    <tr key={call.id}>
                      <td>#{call.id}</td>
                      <td>{call.provider}</td>
                      <td>
                        <span className={`status-badge ${call.status.toLowerCase()}`}>
                          {call.status}
                        </span>
                      </td>
                      <td>{formatTime(call.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="footer-note">
              <ArrowDownLeft size={15} />
              Data refreshes automatically every 5 seconds.
            </div>
          </section>
        </div>

        <footer className="page-footer">
          <span>CredResolve SmartDialer · Local prototype</span>
          <span><ShieldCheck size={14} /> Safety controls enforced by backend</span>
        </footer>
      </main>
    </div>
  );
}

export default App;
