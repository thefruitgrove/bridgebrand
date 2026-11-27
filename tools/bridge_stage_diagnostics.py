"""Read-only GitHub Actions step diagnostics for the BRIDGE daily operator view.

Only allowlisted workflow/step names, statuses, durations and GitHub links.
Never return raw logs, environment variables, SQL rows, provider errors, or
arbitrary untrusted step output.
"""
from __future__ import annotations

import datetime as dt
import json
import urllib.request
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
PIPELINES = (
    ("BRIDGE Daily Pipeline", "정규 수집"),
    ("BRIDGE Recover Existing Observations", "근거 복구"),
    ("BRIDGE Daily Fallback — verify before dispatch", "재수집 판단"),
    ("BRIDGE Live Deployment Verification", "실서비스 확인"),
)
STEPS = {
    "Synchronize active target registry": "대상 관리",
    "Build UNI official baseline and daily observation layer": "공식 기준·대학",
    "Collect registered targets' verified daily evidence (required)": "뉴스 수집",
    "Refresh institutional channel ownership links": "정부 채널 검증",
    "Collect verified GOV public-communication signals": "정부 채널 수집",
    "Refresh DART entity map": "DART 대상 매핑",
    "Collect regulatory evidence": "DART 공시 수집",
    "Normalize and import official baselines": "공식 근거 적재",
    "Hard gate — verify today's mandatory collectors before scoring": "수집 검증",
    "Compute shadow scores and rankings": "점수·순위",
    "Audit CPR universe to T100 bottleneck": "기업 평가 감사",
    "Verify V5 entity-axis-date lineage": "근거 연결 감사",
    "Publish CPR, ENT, GOV and UNI T100 beta snapshot": "DB 발행",
    "Export published snapshot": "JSON 생성",
    "Verify 400 authoritative database ranks, scores and trust grades": "400건 정합성",
    "Post-publication collector health gate": "발행 후 검증",
    "Rebuild static site": "홈페이지 생성",
    "Commit reproducible public export": "GitHub 게시",
    "Trigger Cloudflare deployment hook": "Cloudflare 배포 요청",
    "Decide whether any recovery is necessary": "복구 진단",
    "Compute only if stored evidence is complete and metrics missing": "복구 점수",
    "Audit historical lineage before any publication": "복구 근거 감사",
    "Publish existing audited metrics without recollection": "복구 발행",
    "Export existing publication and check consistency": "복구 JSON 검증",
    "Commit only if still based on current production source": "복구 GitHub 게시",
    "Request deployment only for actual repaired publication": "복구 Cloudflare 요청",
    "Verify public deployed snapshot and THIS WEEK": "실서비스 데이터 검증",
}
VALID_EVENTS = frozenset({"schedule", "workflow_dispatch"})
VALID_OUTCOMES = frozenset({"success", "failure", "cancelled", "skipped", "timed_out", "action_required", "neutral"})


def date_of(run):
    try:
        t = dt.datetime.fromisoformat(str(run["created_at"]).replace("Z", "+00:00"))
        return t.astimezone(KST).date() if t.tzinfo else None
    except (KeyError, TypeError, ValueError, OverflowError):
        return None


def summarize_runs(runs: list[dict], today: dt.date) -> list[dict]:
    """Latest valid run per pipeline. Missing run remains unknown, never success."""
    summaries = []
    for name, label in PIPELINES:
        matching = [r for r in runs
                    if r.get("name") == name
                    and r.get("head_branch") == "main"
                    and r.get("event") in VALID_EVENTS
                    and date_of(r) == today]
        matching.sort(key=lambda r: str(r.get("created_at") or ""), reverse=True)
        latest = matching[0] if matching else None
        outcome = (latest or {}).get("conclusion")
        if outcome not in VALID_OUTCOMES:
            outcome = "running" if latest and latest.get("status") in {"queued", "in_progress"} else "not_observed"
        ident = (latest or {}).get("id")
        summaries.append({
            "key": name, "label": label,
            "status": outcome,
            "runId": ident if type(ident) is int and ident > 0 else None,
            "attempts": len(matching),
            "failureCount": sum(r.get("conclusion") == "failure" and r.get("status") == "completed" for r in matching),
            "failedStage": None,
        })
    return summaries


def failed_stage(jobs: list[dict]) -> str | None:
    """Use only predetermined step-name labels; never expose log contents."""
    for job in jobs:
        for step in job.get("steps") or []:
            if step.get("conclusion") == "failure" and step.get("name") in STEPS:
                return STEPS[step["name"]]
    return None


def inspect_failures(repo: str, token: str, summaries: list[dict]) -> list[dict]:
    """Read-only jobs API for failures; no more than one jobs request/pipeline."""
    if not token:
        return summaries
    for entry in summaries:
        ident = entry.get("runId")
        if not ident or entry["status"] != "failure":
            continue
        url = f"https://api.github.com/repos/{repo}/actions/runs/{ident}/jobs?per_page=100"
        request = urllib.request.Request(url, headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "BRIDGE-StageMonitor/1.0",
        })
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                jobs = json.load(response).get("jobs", [])
            entry["failedStage"] = failed_stage(jobs)
        except (OSError, ValueError, TypeError):
            # Not enough evidence to assign an exact stage.
            entry["failedStage"] = None
    return summaries
