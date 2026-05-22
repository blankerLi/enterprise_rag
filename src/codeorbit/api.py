from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .models import Run
from .reporting import render_markdown_report
from .service import CodeOrbitService


class CreateRunRequest(BaseModel):
    repo_path: str
    task: str


app = FastAPI(title="MiMo CodeOrbit API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_service() -> CodeOrbitService:
    return CodeOrbitService()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/runs", response_model=Run)
def create_run(payload: CreateRunRequest) -> Run:
    return get_service().run_analysis(payload.repo_path, payload.task)


@app.get("/runs", response_model=list[Run])
def list_runs() -> list[Run]:
    return get_service().list_runs()


@app.get("/runs/{run_id}", response_model=Run)
def get_run(run_id: int) -> Run:
    try:
        return get_service().get_run(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/runs/{run_id}/application-copy")
def get_application_copy(run_id: int) -> dict[str, str]:
    run = get_run(run_id)
    return {"application_copy": run.result.application_copy if run.result else ""}


@app.get("/runs/{run_id}/report")
def get_report(run_id: int) -> dict[str, str]:
    run = get_run(run_id)
    return {"markdown": render_markdown_report(run)}
