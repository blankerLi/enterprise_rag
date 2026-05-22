# MiMo CodeOrbit

MiMo CodeOrbit is a repository-level AI coding assistant MVP for applying to the Xiaomi MiMo Orbit token creator program. It scans a real codebase, builds a compact context package, asks a MiMo-compatible chat model for implementation guidance, and presents a structured plan, risk review, suggested diff, tests, and application copy.

## Features

- CLI commands for scanning repositories, running analysis, and exporting Markdown reports.
- FastAPI local API backed by SQLite.
- React + Vite web workspace for run history, analysis detail, and generated application copy.
- MiMo API client isolated behind environment variables:
  - `MIMO_API_KEY`
  - `MIMO_BASE_URL`
  - `MIMO_MODEL`

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

```powershell
$env:MIMO_API_KEY="your-key"
$env:MIMO_BASE_URL="https://api.example.com/v1"
$env:MIMO_MODEL="mimo-model-name"
mimo-codeorbit scan .
mimo-codeorbit run . --task "帮我给这个项目增加登录失败重试限制"
mimo-codeorbit report 1
```

Run the API:

```powershell
uvicorn codeorbit.api:app --reload
```

Run the frontend:

```powershell
cd frontend
npm install
npm run dev
```

## Offline Demo Mode

Set `CODEORBIT_DEMO_MODE=1` to generate deterministic local analysis without calling MiMo. This is useful before API credentials are approved.

```powershell
$env:CODEORBIT_DEMO_MODE="1"
mimo-codeorbit run . --task "生成申请材料"
```
