import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  AlertTriangle,
  Braces,
  CheckCircle2,
  Clipboard,
  Code2,
  FileText,
  History,
  Loader2,
  Play,
  RefreshCw,
  Search,
} from 'lucide-react';
import './styles.css';

const API_BASE = import.meta.env.VITE_CODEORBIT_API || 'http://127.0.0.1:8000';

function App() {
  const [runs, setRuns] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [selectedRun, setSelectedRun] = useState(null);
  const [repoPath, setRepoPath] = useState('');
  const [task, setTask] = useState('帮我给这个项目增加登录失败重试限制');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    refreshRuns();
  }, []);

  useEffect(() => {
    if (selectedId) {
      fetchRun(selectedId);
    }
  }, [selectedId]);

  const activeRun = selectedRun || runs[0];
  const applicationCopy = activeRun?.result?.application_copy || '';
  const languages = useMemo(() => activeRun?.snapshot?.languages || {}, [activeRun]);

  async function refreshRuns() {
    try {
      const response = await fetch(`${API_BASE}/runs`);
      const data = await response.json();
      setRuns(data);
      if (!selectedId && data.length) {
        setSelectedId(data[0].id);
      }
    } catch (err) {
      setError(`无法连接 API：${err.message}`);
    }
  }

  async function fetchRun(id) {
    const response = await fetch(`${API_BASE}/runs/${id}`);
    const data = await response.json();
    setSelectedRun(data);
  }

  async function createRun(event) {
    event.preventDefault();
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${API_BASE}/runs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_path: repoPath, task }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || '创建任务失败');
      }
      setSelectedId(data.id);
      setSelectedRun(data);
      await refreshRuns();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function copyApplicationText() {
    await navigator.clipboard.writeText(applicationCopy);
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <Code2 size={28} />
          <div>
            <h1>MiMo CodeOrbit</h1>
            <p>仓库级 AI 编程助手</p>
          </div>
        </div>

        <form className="run-form" onSubmit={createRun}>
          <label>
            仓库路径
            <input
              value={repoPath}
              onChange={(event) => setRepoPath(event.target.value)}
              placeholder="E:\\path\\to\\repo"
              required
            />
          </label>
          <label>
            需求任务
            <textarea value={task} onChange={(event) => setTask(event.target.value)} rows={5} required />
          </label>
          <button type="submit" disabled={loading}>
            {loading ? <Loader2 className="spin" size={18} /> : <Play size={18} />}
            开始分析
          </button>
        </form>

        <div className="history-head">
          <span><History size={17} /> 历史任务</span>
          <button className="icon-button" onClick={refreshRuns} title="刷新任务">
            <RefreshCw size={16} />
          </button>
        </div>
        <div className="run-list">
          {runs.map((run) => (
            <button
              key={run.id}
              className={`run-item ${activeRun?.id === run.id ? 'active' : ''}`}
              onClick={() => setSelectedId(run.id)}
            >
              <span>#{run.id} {run.task}</span>
              <Status status={run.status} />
            </button>
          ))}
        </div>
      </aside>

      <section className="workspace">
        {error && (
          <div className="alert">
            <AlertTriangle size={18} />
            {error}
          </div>
        )}

        {!activeRun ? (
          <div className="empty-state">
            <Search size={36} />
            <h2>输入仓库路径和需求后开始第一次分析</h2>
          </div>
        ) : (
          <>
            <header className="run-header">
              <div>
                <p>Run #{activeRun.id}</p>
                <h2>{activeRun.task}</h2>
                <span>{activeRun.repo_path}</span>
              </div>
              <Status status={activeRun.status} large />
            </header>

            <div className="metric-row">
              <Metric icon={<Braces size={18} />} label="语言" value={Object.keys(languages).join(', ') || '未识别'} />
              <Metric icon={<FileText size={18} />} label="关键文件" value={activeRun.snapshot?.key_files?.length ?? 0} />
              <Metric icon={<CheckCircle2 size={18} />} label="测试建议" value={activeRun.result?.test_plan?.length ?? 0} />
            </div>

            <section className="content-grid">
              <Panel title="需求澄清">
                <p>{activeRun.result?.clarification || activeRun.error || '等待分析结果'}</p>
              </Panel>
              <Panel title="相关文件">
                <FileList files={activeRun.result?.relevant_files || activeRun.snapshot?.key_files || []} />
              </Panel>
              <Panel title="实现计划">
                <Numbered items={activeRun.result?.implementation_plan || []} />
              </Panel>
              <Panel title="风险点">
                <List items={activeRun.result?.risks || []} />
              </Panel>
              <Panel title="测试方案">
                <List items={activeRun.result?.test_plan || activeRun.snapshot?.test_commands || []} />
              </Panel>
              <Panel title="申请文案" action={<button className="compact-button" onClick={copyApplicationText}><Clipboard size={15} />复制</button>}>
                <p>{applicationCopy || '分析完成后自动生成小米 MiMo Orbit 申请文案。'}</p>
              </Panel>
            </section>

            <section className="diff-panel">
              <div className="panel-title">候选 Diff</div>
              <pre>{activeRun.result?.suggested_diff || 'No diff generated yet.'}</pre>
            </section>
          </>
        )}
      </section>
    </main>
  );
}

function Status({ status, large = false }) {
  return <span className={`status ${status} ${large ? 'large' : ''}`}>{status}</span>;
}

function Metric({ icon, label, value }) {
  return (
    <div className="metric">
      {icon}
      <div>
        <p>{label}</p>
        <strong>{value}</strong>
      </div>
    </div>
  );
}

function Panel({ title, action, children }) {
  return (
    <article className="panel">
      <div className="panel-title">
        <span>{title}</span>
        {action}
      </div>
      {children}
    </article>
  );
}

function FileList({ files }) {
  if (!files.length) return <p className="muted">暂无文件</p>;
  return <div className="file-list">{files.map((file) => <code key={file}>{file}</code>)}</div>;
}

function Numbered({ items }) {
  if (!items.length) return <p className="muted">暂无计划</p>;
  return <ol>{items.map((item) => <li key={item}>{item}</li>)}</ol>;
}

function List({ items }) {
  if (!items.length) return <p className="muted">暂无内容</p>;
  return <ul>{items.map((item) => <li key={item}>{item}</li>)}</ul>;
}

createRoot(document.getElementById('root')).render(<App />);
