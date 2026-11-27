"""Render a private, static BRIDGE operations dashboard from one monitor report.

The HTML is a GitHub Actions artifact, NOT a public site asset. Because the\nrepository is public, artifacts must be treated as accessible to readers. It contains only
sanitized aggregate status, seven-day reliability and links to GitHub Actions.
No credentials, collector raw diagnostics, subject rows or DB evidence.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
from pathlib import Path

ALLOWED_STATUS = frozenset({"healthy", "degraded", "failure", "not_observed", "not_started"})
STATUS_KO = {
    "healthy": "정상", "degraded": "복구·주의", "failure": "장애",
    "not_observed": "기록 없음", "not_started": "검증 시작 전",
}
WORKFLOWS = (
    ("정규 수집", "bridge-daily.yml", "05:15"),
    ("근거 기반 복구", "bridge-recover-publish.yml", "06:45"),
    ("재수집 판단", "bridge-daily-fallback.yml", "07:15"),
    ("실서비스 검증", "bridge-live-verify.yml", "08:30"),
    ("종합 모니터", "bridge-7day-reliability.yml", "09:30"),
)


def clean(value) -> str:
    return html.escape(str(value if value is not None else "확인 불가"), quote=True)


def status(value) -> str:
    return str(value) if value in ALLOWED_STATUS else "not_observed"


def day_cell(row: dict) -> str:
    d = clean(row.get("date", "—"))
    state = status(row.get("status"))
    note = {
        "healthy": "정규 운영 완료", "degraded": "최종 발행 확인 / 정규운영 이상",
        "failure": "발행 또는 검증 실패", "not_observed": "검증 기록 미확보",
        "not_started": "검증 시작 전",
    }[state]
    return (f'<div class="day state-{state}"><div class="day-date">{d}</div>'
            f'<strong>{STATUS_KO[state]}</strong><span>{note}</span></div>')


def render_dashboard(report: dict) -> str:
    card = report.get("scorecard") or {}
    checks = report.get("checks") or {}
    live = checks.get("live") or {}
    observed = int(card.get("observed_days") or 0)
    delivered = int(card.get("delivered_days") or 0)
    clean_days = int(card.get("clean_days") or 0)
    current = status(card.get("status"))
    days = card.get("days") or []
    domain_rows = [("기업 · CPR", 100), ("광고모델 · ENT", 100),
                   ("정부·공공 · GOV", 100), ("대학교 · UNI", 100)]
    # Show expected panel quota separately; do not imply it is measured.
    expected = ''.join(
        f'<div class="coverage-item"><b>{clean(name)}</b><span>기대값 {num}건</span></div>'
        for name, num in domain_rows
    )
    day_html = ''.join(day_cell(row) for row in days if isinstance(row, dict))
    links = ''.join(
        f'<a href="https://github.com/thefruitgrove/bridgebrand/actions/workflows/{file}" '
        f'target="_blank" rel="noopener noreferrer"><span>{label}</span><small>{time} KST</small></a>'
        for label, file, time in WORKFLOWS
    )
    # Stage names and outcomes are allowlisted; never render raw API errors.
    stage_names = {"정규 수집", "근거 복구", "재수집 판단", "실서비스 확인"}
    allowed_outcomes = {
        "success": "성공", "failure": "실패", "cancelled": "취소",
        "skipped": "건너뜀", "running": "실행 중",
        "not_observed": "기록 없음", "timed_out": "시간 초과",
        "neutral": "중립", "action_required": "조치 필요",
    }
    from tools.bridge_stage_diagnostics import STEPS
    safe_stages = set(STEPS.values())
    stages_markup = []
    for item in report.get("stages") or []:
        label = item.get("label")
        if label not in stage_names:
            continue
        outcome = item.get("status")
        stage = item.get("failedStage")
        stage_label = stage if stage in safe_stages else "단계 확인 불가"
        summary = f'{allowed_outcomes.get(outcome, "확인 불가")} · 실패 {int(item.get("failureCount") or 0)}회'
        if outcome == "failure":
            summary += " · 실패 단계: " + stage_label
        run_id = item.get("runId")
        if type(run_id) is int and run_id > 0:
            href = f"https://github.com/thefruitgrove/bridgebrand/actions/runs/{run_id}"
            details = '<a href="' + href + '" target="_blank" rel="noopener noreferrer">실행 기록 열기</a>'
        else:
            details = '<span class="muted">실행 기록 없음</span>'
        stages_markup.append(
            '<div class="line"><span>' + clean(label) + '</span><span>' +
            clean(summary) + ' &nbsp; ' + details + '</span></div>'
        )
    stage_html = ''.join(stages_markup) or '<p class="muted">작업 단계 기록이 아직 없습니다.</p>'
    # Only bounded, known source labels and numeric aggregates are rendered.
    from tools.bridge_source_metrics import SOURCE_LABELS
    metrics_data = report.get("sourceMetrics") or {}
    source_rows = []
    safe_states = {
        "success": "최근 성공", "failed": "최근 실패",
        "failure": "최근 실패", "error": "최근 실패",
        "unknown": "결과 미확인", "not_observed": "기록 없음",
    }
    for entry in metrics_data.get("sources") or []:
        source_id = entry.get("sourceId")
        if source_id not in SOURCE_LABELS:
            continue
        observations = int(entry.get("observedDays") or 0)
        successful_days = int(entry.get("successfulDays") or 0)
        runs = int(entry.get("runs") or 0)
        failures = int(entry.get("failedRuns") or 0)
        rate = entry.get("successRatePct")
        runtime = entry.get("averageDurationMinutes")
        rate_text = str(rate) + "%" if type(rate) in (float, int) else "미측정"
        runtime_text = str(runtime) + "분" if type(runtime) in (float, int) else "미측정"
        last = entry.get("lastRunStatus")
        state_text = safe_states.get(last, "확인 불가")
        source_rows.append(
            '<tr><th scope="row">' + clean(SOURCE_LABELS[source_id]) +
            '</th><td>' + str(observations) + '일 / ' + str(successful_days) +
            '일</td><td>' + str(runs) + '회</td><td>' + str(failures) +
            '회</td><td>' + clean(rate_text) + '</td><td>' +
            clean(runtime_text) + '</td><td>' + clean(state_text) + '</td></tr>'
        )
    source_table = ''.join(source_rows)
    if not source_table:
        source_table = '<tr><td colspan="7">자료원별 작업 기록을 확인할 수 없습니다.</td></tr>'
    source_period = (clean(metrics_data.get("windowStart")) + ' ~ ' +
                     clean(metrics_data.get("windowEnd")))
    source_warning = (
        '자료원 통계 조회 불가 · 발행 검증 판정과 별개로 확인이 필요합니다.'
        if metrics_data.get("status") == "unavailable" else
        '수집 실행 기록 없음 · 성공 또는 실패를 추정하지 않습니다.'
        if metrics_data.get("metricsAvailable") is False else ''
    )
    db_ok = bool(checks.get("db_ok"))
    live_ok = bool(checks.get("live_ok"))
    source_date = clean(checks.get("repositoryDate"))
    live_date = clean(live.get("live_date"))
    verified_rows = live.get("record_count")
    errors = len(report.get("errors") or []) + len(checks.get("errors") or [])
    seven_clean = card.get("seven_day_clean") is True
    seven_delivered = card.get("seven_day_delivery") is True
    checked = clean(report.get("checkedAt"))
    today = clean(card.get("today", report.get("observationDate")))
    def state_line(ok):
        return '<span class="ok">정상 확인</span>' if ok else '<span class="bad">미확인 / 실패</span>'
    def metric(title, value, sub):
        return f'<article class="metric"><small>{title}</small><strong>{value}</strong><span>{sub}</span></article>'
    metrics = ''.join((
        metric("현재 운영 판정", STATUS_KO[current], "실측 기반 상태 분류"),
        metric("검증된 날짜", str(observed) + "일", "7일 관측 창"),
        metric("실제 발행 확보", str(delivered) + "일", "정상 + 복구 성공"),
        metric("무장애 정규 운영", str(clean_days) + "일", "복구 없이 정상"),
    ))
    return """<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow,noarchive"><meta name="referrer" content="no-referrer">
<title>BRIDGE / 운영 관리 콘솔</title>
<style>
:root{font-family:system-ui,-apple-system,'Noto Sans KR',sans-serif;color:#19243b;background:#f5f7fb}
*{box-sizing:border-box}body{margin:0}a{color:inherit;text-decoration:none}
.wrap{width:min(1160px,calc(100% - 36px));margin:auto}
header{background:#101c37;color:white;padding:30px 0 32px}
header .top{display:flex;justify-content:space-between;align-items:center;gap:15px;flex-wrap:wrap}
.logo{font-size:18px;font-weight:900;letter-spacing:.12em}.logo em{font-style:normal;color:#92b8ff}
.eyebrow{font-size:11px;letter-spacing:.15em;font-weight:750;color:#bdccea}
h1{font-size:clamp(25px,4vw,38px);margin:18px 0 7px;letter-spacing:-.045em}
header p{color:#bdccea;margin:0;line-height:1.7}
.privacy{font-size:12px;border:1px solid #4b638f;border-radius:99px;padding:7px 13px}
main{padding:27px 0 55px}.sectionhead{display:flex;align-items:baseline;justify-content:space-between;gap:10px;flex-wrap:wrap;margin:25px 0 13px}
h2{font-size:20px;margin:0;letter-spacing:-.03em}.muted{color:#66758e;font-size:13px}
.metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:13px}
.metric,.panel{background:white;border:1px solid #e2e8f1;border-radius:15px;box-shadow:0 4px 15px #17244308}
.metric{padding:21px;display:flex;flex-direction:column;gap:10px}
.metric small{font-size:12px;color:#6a7990}.metric strong{font-size:28px;letter-spacing:-.05em}
.metric span{font-size:12px;color:#61728c}.panel{padding:21px}
.twocol{display:grid;grid-template-columns:1.25fr .75fr;gap:15px}
.line{display:flex;justify-content:space-between;align-items:center;gap:12px;border-top:1px solid #ecf0f5;padding:12px 0;font-size:14px}
.line:first-child{border:0}.ok{color:#087b51;font-weight:750}.bad{color:#b43143;font-weight:750}
.days{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:9px}
.day{border:1px solid #e4eaf1;border-radius:12px;min-height:119px;padding:13px 10px;display:flex;flex-direction:column;gap:10px;background:#f8fafc}
.day-date{font-size:12px;color:#65738c}.day strong{font-size:15px}.day span{font-size:11px;color:#60718c;line-height:1.4}
.state-healthy{background:#edf9f4;border-color:#b1e3d1}
.state-degraded{background:#fff8e8;border-color:#ecd594}
.state-failure{background:#fff0f0;border-color:#f0baba}
.flagrow{display:flex;gap:10px;flex-wrap:wrap}.flag{padding:9px 12px;border-radius:99px;font-size:12px;font-weight:750}
.flag.on{background:#eaf8f3;color:#047953}.flag.off{background:#eef1f6;color:#526278}
.coverage{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}.coverage-item{background:#f6f8fc;border:1px solid #e5ebf4;padding:14px;border-radius:10px;display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap;font-size:12px}.coverage-item span{color:#63738c}
.links{display:grid;gap:8px}.links a{border:1px solid #e4eaf2;border-radius:9px;padding:11px 14px;display:flex;justify-content:space-between;align-items:center;font-size:13px}
.links a:hover{border-color:#6594db;background:#f6faff}.links small{color:#63738c}
.table-scroll{overflow-x:auto}table.source-table{border-collapse:collapse;width:100%;min-width:760px;font-size:12px;text-align:left}
.source-table th,.source-table td{padding:12px 9px;border-bottom:1px solid #e6eaf1}
.source-table thead th{background:#f4f7fc;color:#54657c}
.source-table tbody th{font-weight:700}
.notice{font-size:13px;line-height:1.8;color:#5b6b82;margin-top:19px}
footer{border-top:1px solid #dde5ef;padding:22px 0 35px;font-size:12px;color:#64748b}
@media(max-width:850px){.metrics{grid-template-columns:repeat(2,minmax(0,1fr))}.twocol{grid-template-columns:1fr}.days{grid-template-columns:repeat(4,minmax(0,1fr))}}
@media(max-width:520px){.days{grid-template-columns:repeat(2,minmax(0,1fr))}.coverage{grid-template-columns:repeat(2,minmax(0,1fr))}.metric{padding:15px}.metric strong{font-size:23px}}
</style></head><body>
<header><div class="wrap"><div class="top"><div class="logo">BRIDGE<em>.</em> OPERATIONS</div><span class="privacy">운영 점검 보고서 · 민감정보 미포함</span></div>
<div class="eyebrow" style="margin-top:25px">RELIABILITY &amp; PUBLICATION INTEGRITY</div>
<h1>브랜드지수 운영 관리 콘솔</h1><p>정규 수집부터 근거 검증, 원자적 발행, Cloudflare 실서비스 확인까지.</p></div></header>
<main class="wrap">
<div class="sectionhead"><h2>운영 개요</h2><span class="muted">기준일 """ + today + """ · 점검 """ + checked + """</span></div>
<div class="metrics">""" + metrics + """</div>
<div class="sectionhead"><h2>7일 연속 운영 기록</h2><span class="muted">검증된 날짜만 성공으로 계산</span></div>
<div class="panel"><div class="days">""" + (day_html or '<p class="muted">실운영 검증 시작 전입니다.</p>') + """</div>
<div class="flagrow" style="margin-top:17px"><span class="flag """ + ("on" if seven_delivered else "off") + """">7일 연속 발행 """ + ("충족" if seven_delivered else "미충족") + """</span>
<span class="flag """ + ("on" if seven_clean else "off") + """">7일 연속 무장애 """ + ("충족" if seven_clean else "미충족") + """</span></div></div>
<div class="sectionhead"><h2>현재 데이터 검증</h2><span class="muted">GitHub 공개 JSON · 운영 DB · Cloudflare</span></div>
<div class="twocol"><section class="panel">
<div class="line"><span>GitHub 공개 데이터 날짜</span><b>""" + source_date + """</b></div>
<div class="line"><span>실제 홈페이지 데이터 날짜</span><b>""" + live_date + """</b></div>
<div class="line"><span>실제 홈페이지 검증</span>""" + state_line(live_ok) + """</div>
<div class="line"><span>DB 원장·점수·공개 데이터 일치</span>""" + state_line(db_ok) + """</div>
<div class="line"><span>실서비스의 레코드 수</span><b>""" + clean(verified_rows) + """건</b></div>
<div class="line"><span>모니터 진단 오류 항목 수</span><b>""" + str(errors) + """개</b></div>
</section><section class="panel"><strong>주요 자동화 단계 바로가기</strong><div class="links" style="margin-top:13px">""" + links + """</div></section></div>
<div class="sectionhead"><h2>작업별 진단·실패 단계</h2><span class="muted">GitHub Actions의 완료 상태 및 사전 정의된 단계만 표시</span></div>
<div class="panel">""" + stage_html + """</div>
<div class="sectionhead"><h2>자료원별 수집 안정성</h2><span class="muted">최근 30일 관측 가능 기간 · 성공률은 시도 기준, 일수는 관측 기준</span></div>
<section class="panel"><p class="muted">관측 기간: """ + source_period + """ · 재시도 성공은 이전 실패 기록을 지우지 않습니다.</p>
<p class="muted">""" + clean(source_warning) + """</p>
<div class="table-scroll"><table class="source-table"><thead><tr><th scope="col">자료원</th><th scope="col">관측일 / 성공일</th><th scope="col">시도</th><th scope="col">실패</th><th scope="col">시도 성공률</th><th scope="col">평균 소요</th><th scope="col">최신 실행</th></tr></thead>
<tbody>""" + source_table + """</tbody></table></div>
<p class="muted">이 표는 DB의 수집 실행기록만 반영합니다. 데이터 품질이나 각 출처의 실제 신뢰도 점수가 아니며, 기록이 없는 날은 자동으로 실패 또는 성공으로 계산하지 않습니다.</p></section>
<div class="sectionhead"><h2>4개 분야 T100 평가 범위</h2><span class="muted">아래 숫자는 계약상 기대값이며 해당 날짜의 실측 건수가 아닙니다</span></div>
<div class="coverage">""" + expected + """</div>
<p class="notice"><b>운영 판정 안내</b> · '정상'은 정규 수집 및 발행 검증 통과, '복구·주의'는 발행이 확보되었으나 정규 작업에 이상이 있었음을 뜻합니다. '기록 없음'은 실패 또는 성공의 증거가 확보되지 않았다는 뜻입니다. 이 문서는 점검 시점의 정적 보고서이며 실시간 화면이 아닙니다.</p>
</main><footer><div class="wrap">BRIDGE STABILITY 1.0 · ACCESS: GITHUB ACTIONS ARTIFACT · 자동 생성 자료 · GitHub 저장소 접근권한 범위에 따라 열람 가능</div></footer>
</body></html>"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("bridge-reliability.json"))
    parser.add_argument("--output", type=Path, default=Path("bridge-ops-dashboard.html"))
    args = parser.parse_args()
    report = json.loads(args.input.read_text(encoding="utf-8"))
    result = render_dashboard(report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(result, encoding="utf-8")
    print(f"PRIVATE_DASHBOARD_CREATED: {args.output} bytes={len(result.encode('utf-8'))}")


if __name__ == "__main__":
    main()
