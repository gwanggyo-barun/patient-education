#!/usr/bin/env python3
"""Local operations audit harness for clinic-content-system.

This script intentionally writes only under _local/ so it can run while other
agents are editing content. It audits infrastructure state and produces an
inventory/priority queue without modifying source HTML or build outputs.
"""
from __future__ import annotations

import argparse
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import types
from typing import Any
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REF = "origin/main"
DEFAULT_REPO = "gwanggyo-barun/patient-education"
BASE_URL_FALLBACK = "https://gwanggyo-barun.github.io/patient-education"

IMG_TAG_RE = re.compile(r"<img\b[^>]*>", re.I | re.S)
SRC_RE = re.compile(r"\bsrc\s*=\s*['\"]([^'\"]+)['\"]", re.I)
DATA_ASSET_RE = re.compile(r"\bdata-asset\s*=\s*['\"]([^'\"]+)['\"]", re.I)
SLIDE_RE = re.compile(r"<section\b[^>]*class=['\"][^'\"]*\bslide\b", re.I)
PAGE_RE = re.compile(r"<(?:div|section|main|article)\b[^>]*class=['\"][^'\"]*\bpage\b", re.I)
LEGACY_LAB_TITLE_RE = re.compile(r"^\[\d+\]\s+.+")


@dataclass
class AuditRow:
    kind: str
    slug: str
    slug_path: str
    title_public: str
    html_url: str
    pdf_url: str
    source_exists: bool = False
    local_state: str = "clean"
    last_modified: str = ""
    html_status: int | None = None
    pdf_status: int | None = None
    html_units: int = 0
    expected_pdf_pages: int = 0
    pdf_pages: int | None = None
    image_refs: int = 0
    data_assets: int = 0
    missing_images: list[str] = field(default_factory=list)
    unknown_data_assets: list[str] = field(default_factory=list)
    notion_meta: str = "ok"
    issues: list[str] = field(default_factory=list)
    priority: str = "P3"


def run(cmd: list[str], *, check: bool = True) -> str:
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    if check and proc.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} failed: {proc.stderr.strip()}")
    return proc.stdout


def git_show(ref: str, path: str) -> str | None:
    proc = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout


def git_exists(ref: str, path: str) -> bool:
    proc = subprocess.run(
        ["git", "cat-file", "-e", f"{ref}:{path}"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return proc.returncode == 0


def git_last_modified(ref: str, path: str) -> str:
    proc = subprocess.run(
        ["git", "log", "-1", "--format=%cs", ref, "--", path],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    return proc.stdout.strip()


def git_object(ref: str, path: str) -> str:
    proc = subprocess.run(
        ["git", "rev-parse", f"{ref}:{path}"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    return proc.stdout.strip() if proc.returncode == 0 else ""


def file_hash(path: Path) -> str:
    proc = subprocess.run(
        ["git", "hash-object", str(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    return proc.stdout.strip() if proc.returncode == 0 else ""


def dirty_paths() -> dict[str, str]:
    out = run(["git", "status", "--porcelain=v1"], check=False)
    paths: dict[str, str] = {}
    for line in out.splitlines():
        if len(line) < 4:
            continue
        status = line[:2].strip() or "modified"
        raw = line[3:]
        if " -> " in raw:
            raw = raw.split(" -> ", 1)[1]
        paths[raw] = status
    return paths


def load_manifest_from_ref(ref: str) -> dict[str, dict[str, Any]]:
    assets: dict[str, dict[str, Any]] = {}
    for path in ("shared/assets/healthicons.manifest.json", "shared/assets/manifest.json"):
        text = git_show(ref, path)
        if not text:
            continue
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            continue
        assets.update(data.get("assets", {}))
    return assets


def install_build_stubs() -> dict[str, types.ModuleType | None]:
    previous: dict[str, types.ModuleType | None] = {}

    def put(name: str, module: types.ModuleType) -> None:
        previous[name] = sys.modules.get(name)
        sys.modules[name] = module

    playwright = types.ModuleType("playwright")
    sync_api = types.ModuleType("playwright.sync_api")
    sync_api.sync_playwright = lambda *a, **k: None
    put("playwright", playwright)
    put("playwright.sync_api", sync_api)

    helpers = types.ModuleType("_build_helpers")
    for name in (
        "make_qr_svg",
        "inject_qr",
        "inject_qr_url_text",
        "qr_mini_url_text",
        "short_qr_url_text",
        "inject_noindex_meta",
        "render",
        "check_og_meta",
        "strip_qr_mini_block",
        "load_asset_manifest",
        "resolve_data_asset",
        "collect_data_asset_keys",
    ):
        setattr(helpers, name, lambda *a, **k: "")
    put("_build_helpers", helpers)

    validator = types.ModuleType("_validate_layout")
    validator.HANDOUT_VALIDATOR_JS = ""
    validator.DECK_VALIDATOR_JS = ""
    validator.CONTRAST_ADVISORY_JS = ""
    put("_validate_layout", validator)
    return previous


def restore_modules(previous: dict[str, types.ModuleType | None]) -> None:
    for name, module in previous.items():
        if module is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = module


def load_targets_from_ref(ref: str) -> tuple[str, list[dict[str, Any]]]:
    source = git_show(ref, "build.py")
    if source is None:
        raise RuntimeError(f"cannot read build.py from {ref}")
    old_token = os.environ.pop("NOTION_TOKEN", None)
    previous = install_build_stubs()
    ns: dict[str, Any] = {"__file__": str(ROOT / "build.py")}
    try:
        exec(compile(source, f"{ref}:build.py", "exec"), ns)
    finally:
        restore_modules(previous)
        if old_token is not None:
            os.environ["NOTION_TOKEN"] = old_token
    return ns.get("BASE_URL", BASE_URL_FALLBACK), list(ns["TARGETS"])


def public_title(target: dict[str, Any]) -> str:
    if target.get("kind") == "lab-reports":
        return "[lab-report redacted]"
    return str(target.get("title") or target.get("slug") or "")


def notion_meta_status(target: dict[str, Any]) -> str:
    if target.get("notion_sync", True) is False:
        return "disabled"
    if target.get("kind") == "lab-reports":
        if "/sample/" in str(target.get("slug_path") or ""):
            return "sample"
        if target.get("patient_name") and target.get("chart_no"):
            return "ok"
        if LEGACY_LAB_TITLE_RE.match(str(target.get("title") or "")):
            return "legacy-title"
        missing = [k for k in ("patient_name", "chart_no") if not target.get(k)]
    else:
        missing = [k for k in ("title", "category", "audience", "disease") if not target.get(k)]
    return "missing:" + ",".join(missing) if missing else "ok"


def source_path_for(target: dict[str, Any]) -> str:
    return f"{str(target['slug_path']).rstrip('/')}/index.html"


def pdf_url_for(base_url: str, target: dict[str, Any]) -> str:
    return f"{base_url}/output/{target['kind']}/{target['slug']}.pdf"


def analyze_html(ref: str, target: dict[str, Any], manifest: dict[str, dict[str, Any]]) -> dict[str, Any]:
    path = source_path_for(target)
    text = git_show(ref, path)
    if text is None:
        return {
            "source_exists": False,
            "html_units": 0,
            "expected_pdf_pages": 0,
            "image_refs": 0,
            "data_assets": 0,
            "missing_images": [path],
            "unknown_data_assets": [],
        }

    kind = target["kind"]
    html_units = len(SLIDE_RE.findall(text)) if kind == "decks" else len(PAGE_RE.findall(text))
    missing: list[str] = []
    unknown_assets: list[str] = []
    image_refs = 0
    data_assets = 0
    html_dir = Path(path).parent

    for tag in IMG_TAG_RE.findall(text):
        src_m = SRC_RE.search(tag)
        data_m = DATA_ASSET_RE.search(tag)
        if data_m:
            data_assets += 1
            key = data_m.group(1)
            entry = manifest.get(key)
            if not entry:
                unknown_assets.append(key)
            else:
                file_name = entry.get("file")
                if file_name and not git_exists(ref, f"shared/assets/{file_name}"):
                    missing.append(f"data-asset:{key}->shared/assets/{file_name}")
        if src_m:
            src = src_m.group(1)
            if src.startswith(("http://", "https://", "data:", "#")):
                continue
            image_refs += 1
            resolved = (html_dir / src).as_posix()
            parts: list[str] = []
            for part in resolved.split("/"):
                if part == "..":
                    if parts:
                        parts.pop()
                elif part != ".":
                    parts.append(part)
            normalized = "/".join(parts)
            if not git_exists(ref, normalized):
                missing.append(src)

    return {
        "source_exists": True,
        "html_units": html_units,
        "expected_pdf_pages": html_units,
        "image_refs": image_refs,
        "data_assets": data_assets,
        "missing_images": sorted(set(missing)),
        "unknown_data_assets": sorted(set(unknown_assets)),
    }


def status_for_url(url: str, timeout: int = 20) -> int:
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "clinic-ops-audit/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            return int(res.status)
    except urllib.error.HTTPError as exc:
        return int(exc.code)
    except Exception:
        req = urllib.request.Request(url, method="GET", headers={"User-Agent": "clinic-ops-audit/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as res:
                return int(res.status)
        except urllib.error.HTTPError as exc:
            return int(exc.code)
        except Exception:
            return 0


def pdf_page_count(url: str, timeout: int = 30) -> int | None:
    try:
        import fitz  # type: ignore
    except Exception:
        return None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "clinic-ops-audit/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as res:
            data = res.read()
        with fitz.open(stream=io.BytesIO(data), filetype="pdf") as doc:
            return int(doc.page_count)
    except Exception:
        return None


def check_live(rows: list[AuditRow], workers: int, include_pdf_pages: bool) -> None:
    def one(row: AuditRow) -> tuple[AuditRow, int, int, int | None]:
        html_status = status_for_url(row.html_url)
        pdf_status = status_for_url(row.pdf_url)
        pages = pdf_page_count(row.pdf_url) if include_pdf_pages and pdf_status == 200 else None
        return row, html_status, pdf_status, pages

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(one, row) for row in rows]
        for future in as_completed(futures):
            row, html_status, pdf_status, pages = future.result()
            row.html_status = html_status
            row.pdf_status = pdf_status
            row.pdf_pages = pages


def assign_priority(row: AuditRow) -> None:
    if not row.source_exists:
        row.issues.append("source_missing")
    if row.html_status not in (None, 200):
        row.issues.append(f"live_html_{row.html_status}")
    if row.pdf_status not in (None, 200):
        row.issues.append(f"live_pdf_{row.pdf_status}")
    if row.pdf_pages is not None and row.expected_pdf_pages and row.pdf_pages != row.expected_pdf_pages:
        row.issues.append(f"pdf_pages_{row.pdf_pages}_expected_{row.expected_pdf_pages}")
    if row.missing_images:
        row.issues.append(f"missing_images_{len(row.missing_images)}")
    if row.unknown_data_assets:
        row.issues.append(f"unknown_data_assets_{len(row.unknown_data_assets)}")
    if row.notion_meta.startswith("missing"):
        row.issues.append(row.notion_meta)
    if row.local_state != "clean":
        row.issues.append(f"local_{row.local_state}")

    p0 = {"source_missing"}
    if any(issue in p0 or issue.startswith(("live_html_", "live_pdf_", "pdf_pages_", "missing_images_")) for issue in row.issues):
        row.priority = "P0"
    elif any(issue.startswith(("unknown_data_assets_", "missing:", "local_")) for issue in row.issues):
        row.priority = "P1"
    elif row.html_status is None or row.pdf_status is None:
        row.priority = "P2"
    else:
        row.priority = "P3"


def build_inventory(ref: str, live: bool, pdf_pages: bool, workers: int) -> tuple[str, list[AuditRow], dict[str, Any]]:
    base_url, targets = load_targets_from_ref(ref)
    manifest = load_manifest_from_ref(ref)
    dirty = dirty_paths()
    rows: list[AuditRow] = []

    for target in targets:
        slug_path = str(target["slug_path"])
        source_path = source_path_for(target)
        html_url = f"{base_url}/{slug_path}"
        pdf_url = pdf_url_for(base_url, target)
        static = analyze_html(ref, target, manifest)

        local_state = "clean"
        local_file = ROOT / source_path
        if source_path in dirty:
            local_state = dirty[source_path]
        elif local_file.exists():
            origin_hash = git_object(ref, source_path)
            local_hash = file_hash(local_file)
            if origin_hash and local_hash and origin_hash != local_hash:
                local_state = "differs"

        row = AuditRow(
            kind=str(target["kind"]),
            slug=str(target["slug"]),
            slug_path=slug_path,
            title_public=public_title(target),
            html_url=html_url,
            pdf_url=pdf_url,
            source_exists=bool(static["source_exists"]),
            local_state=local_state,
            last_modified=git_last_modified(ref, source_path),
            html_units=int(static["html_units"]),
            expected_pdf_pages=int(static["expected_pdf_pages"]),
            image_refs=int(static["image_refs"]),
            data_assets=int(static["data_assets"]),
            missing_images=list(static["missing_images"]),
            unknown_data_assets=list(static["unknown_data_assets"]),
            notion_meta=notion_meta_status(target),
        )
        rows.append(row)

    if live:
        check_live(rows, workers=workers, include_pdf_pages=pdf_pages)
    for row in rows:
        assign_priority(row)

    summary = {
        "ref": ref,
        "base_url": base_url,
        "targets": len(rows),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "live_checked": live,
        "pdf_pages_checked": live and pdf_pages,
    }
    return base_url, rows, summary


def write_inventory(outdir: Path, rows: list[AuditRow], summary: dict[str, Any]) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    json_path = outdir / "audit_inventory.json"
    csv_path = outdir / "audit_queue.csv"
    md_path = outdir / "audit_queue.md"

    data = {
        "summary": summary,
        "rows": [
            {
                **row.__dict__,
                "missing_images": row.missing_images[:20],
                "unknown_data_assets": row.unknown_data_assets[:20],
            }
            for row in rows
        ],
    }
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    fieldnames = [
        "priority",
        "kind",
        "slug",
        "title_public",
        "slug_path",
        "html_status",
        "pdf_status",
        "html_units",
        "pdf_pages",
        "expected_pdf_pages",
        "image_refs",
        "data_assets",
        "missing_images_count",
        "unknown_data_assets_count",
        "notion_meta",
        "last_modified",
        "local_state",
        "issues",
        "html_url",
        "pdf_url",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in sorted(rows, key=lambda r: (r.priority, r.kind, r.slug_path)):
            writer.writerow(
                {
                    "priority": row.priority,
                    "kind": row.kind,
                    "slug": row.slug,
                    "title_public": row.title_public,
                    "slug_path": row.slug_path,
                    "html_status": row.html_status,
                    "pdf_status": row.pdf_status,
                    "html_units": row.html_units,
                    "pdf_pages": row.pdf_pages,
                    "expected_pdf_pages": row.expected_pdf_pages,
                    "image_refs": row.image_refs,
                    "data_assets": row.data_assets,
                    "missing_images_count": len(row.missing_images),
                    "unknown_data_assets_count": len(row.unknown_data_assets),
                    "notion_meta": row.notion_meta,
                    "last_modified": row.last_modified,
                    "local_state": row.local_state,
                    "issues": ";".join(row.issues),
                    "html_url": row.html_url,
                    "pdf_url": row.pdf_url,
                }
            )

    counts: dict[str, int] = {}
    kind_counts: dict[str, int] = {}
    for row in rows:
        counts[row.priority] = counts.get(row.priority, 0) + 1
        kind_counts[row.kind] = kind_counts.get(row.kind, 0) + 1

    lines = [
        "# Clinic Content Audit Queue",
        "",
        f"- Generated: {summary['generated_at']}",
        f"- Source ref: `{summary['ref']}`",
        f"- Targets: {summary['targets']}",
        f"- Live checked: {summary['live_checked']}",
        f"- PDF pages checked: {summary['pdf_pages_checked']}",
        f"- Priority counts: {', '.join(f'{k}={counts.get(k, 0)}' for k in ['P0', 'P1', 'P2', 'P3'])}",
        f"- Kind counts: {', '.join(f'{k}={v}' for k, v in sorted(kind_counts.items()))}",
        "",
        "## Queue",
        "",
        "| Priority | Kind | Slug | Live | PDF pages | Local | Notion | Issues |",
        "|---|---|---|---|---|---|---|---|",
    ]
    queued = [row for row in sorted(rows, key=lambda r: (r.priority, r.kind, r.slug_path)) if row.priority != "P3"]
    for row in queued[:120]:
        live = f"H{row.html_status}/P{row.pdf_status}"
        pages = "" if row.pdf_pages is None else f"{row.pdf_pages}/{row.expected_pdf_pages}"
        issues = ", ".join(row.issues[:6])
        lines.append(
            f"| {row.priority} | {row.kind} | `{row.slug_path}` | {live} | {pages} | "
            f"{row.local_state} | {row.notion_meta} | {issues} |"
        )
    if not queued:
        lines.append("| P3 | all | - | ok | ok | clean | ok | no queue items |")
    if len(queued) > 120:
        lines.append(f"\nOnly first 120 queued rows shown. See `{csv_path.name}` for all rows.")
    lines.extend(
        [
            "",
            "## Files",
            "",
            f"- CSV: `{csv_path.name}`",
            f"- JSON: `{json_path.name}`",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def gh_json(args: list[str]) -> Any | None:
    try:
        out = run(["gh", *args], check=True)
        return json.loads(out) if out.strip() else None
    except Exception:
        return None


def workflow_text(ref: str, path: str) -> str:
    return git_show(ref, path) or ""


def build_health_report(
    outdir: Path,
    ref: str,
    repo: str,
    rows: list[AuditRow],
    summary: dict[str, Any],
    *,
    skip_workspace_check: bool,
) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    md_path = outdir / "infrastructure_health.md"
    json_path = outdir / "infrastructure_health.json"

    runs = gh_json(
        [
            "run",
            "list",
            "--repo",
            repo,
            "--limit",
            "30",
            "--json",
            "databaseId,workflowName,displayTitle,status,conclusion,createdAt,updatedAt,event,headBranch,headSha,url",
        ]
    ) or []
    workflows = run(["gh", "workflow", "list", "--repo", repo, "--all"], check=False)
    pages = gh_json(["api", f"repos/{repo}/pages"]) or {}

    build_wf = workflow_text(ref, ".github/workflows/build-and-deploy.yml")
    test_wf = workflow_text(ref, ".github/workflows/test-content.yml")
    audit_wf = workflow_text(ref, ".github/workflows/notion-link-audit.yml")
    audit_tool = workflow_text(ref, "tools/notion_link_audit.py")
    notion_sync = workflow_text(ref, "shared/_notion_sync.py")

    latest_by_workflow: dict[str, dict[str, Any]] = {}
    for run_info in runs:
        latest_by_workflow.setdefault(run_info["workflowName"], run_info)

    findings: list[dict[str, str]] = []
    latest_build = latest_by_workflow.get("Build and Deploy")
    latest_tests = latest_by_workflow.get("Content Regression Tests")
    latest_audit = latest_by_workflow.get("Notion Link Audit")

    if not latest_build or latest_build.get("conclusion") != "success":
        findings.append({"severity": "P0", "area": "deploy", "detail": "latest Build and Deploy is not successful"})
    if not latest_tests or latest_tests.get("conclusion") != "success":
        findings.append({"severity": "P0", "area": "ci", "detail": "latest Content Regression Tests is not successful"})

    if "Build all PDFs" in build_wf and "NOTION_TOKEN" in build_wf and "Run Notion sync" in test_wf:
        if re.search(r"^def\s+sync_all\b", notion_sync, re.M):
            detail = "Notion writes can run in both Build and Deploy and Content Regression Tests"
            severity = "P1"
        else:
            detail = "Content Regression Tests has a stale optional Notion sync step; current _notion_sync.py has no sync_all, so it skips"
            severity = "P2"
        findings.append(
            {
                "severity": severity,
                "area": "notion-sync",
                "detail": detail,
            }
        )

    if '"page_title": record.page_title' in audit_tool and "docs/link-audit-*.json" in audit_wf:
        schedule = "schedule:" in audit_wf
        findings.append(
            {
                "severity": "P0" if schedule else "P1",
                "area": "notion-link-audit",
                "detail": "link-audit artifact can include page_title; lab-report titles are PHI-sensitive",
            }
        )

    if pages.get("html_url") != summary.get("base_url") + "/":
        findings.append(
            {
                "severity": "P2",
                "area": "pages",
                "detail": f"Pages API html_url differs: {pages.get('html_url')}",
            }
        )

    p0_rows = [r for r in rows if r.priority == "P0"]
    p1_rows = [r for r in rows if r.priority == "P1"]
    if p0_rows:
        findings.append({"severity": "P0", "area": "library", "detail": f"{len(p0_rows)} inventory rows need immediate attention"})
    if p1_rows:
        findings.append({"severity": "P1", "area": "library", "detail": f"{len(p1_rows)} inventory rows have warnings"})

    if not skip_workspace_check:
        status_short = run(["git", "status", "--short", "--branch"], check=False).splitlines()
        dirty_count = max(0, len(status_short) - 1)
        if "behind" in (status_short[0] if status_short else "") or dirty_count:
            findings.append(
                {
                    "severity": "P1",
                    "area": "workspace",
                    "detail": f"local workspace is not a safe publish base: {status_short[0] if status_short else 'unknown'}, changes={dirty_count}",
                }
            )

    payload = {
        "generated_at": summary["generated_at"],
        "repo": repo,
        "ref": ref,
        "pages": pages,
        "workflows": workflows,
        "latest_by_workflow": latest_by_workflow,
        "findings": findings,
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Infrastructure Health Report",
        "",
        f"- Generated: {summary['generated_at']}",
        f"- Repo: `{repo}`",
        f"- Source ref: `{ref}`",
        f"- Pages URL: {pages.get('html_url') or summary.get('base_url') + '/'}",
        "",
        "## Current State",
        "",
    ]
    for name in ("Build and Deploy", "Content Regression Tests", "Notion Link Audit"):
        run_info = latest_by_workflow.get(name)
        if not run_info:
            lines.append(f"- {name}: no recent run found")
            continue
        lines.append(
            f"- {name}: {run_info.get('conclusion')} at {run_info.get('updatedAt')} "
            f"({run_info.get('event')}, {run_info.get('headSha', '')[:7]})"
        )
    lines.extend(["", "## Findings", ""])
    if findings:
        for item in findings:
            lines.append(f"- {item['severity']} `{item['area']}`: {item['detail']}")
    else:
        lines.append("- No infrastructure findings.")
    lines.extend(["", "## Run Mix (last 30)", ""])
    by_pair: dict[tuple[str, str], int] = {}
    for run_info in runs:
        key = (run_info.get("workflowName") or "unknown", run_info.get("conclusion") or run_info.get("status") or "unknown")
        by_pair[key] = by_pair.get(key, 0) + 1
    for (workflow, conclusion), count in sorted(by_pair.items()):
        lines.append(f"- {workflow} / {conclusion}: {count}")
    lines.extend(["", "## Notes", ""])
    lines.append("- Content/layout failures are classified separately from deploy/runner failures.")
    lines.append("- lab-reports titles are redacted from inventory outputs by default.")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ref", default=DEFAULT_REF)
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--outdir", default="_local/ops-audit-latest")
    parser.add_argument("--skip-live", action="store_true")
    parser.add_argument("--skip-pdf-pages", action="store_true")
    parser.add_argument("--skip-workspace-check", action="store_true")
    parser.add_argument("--workers", type=int, default=12)
    args = parser.parse_args()

    outdir = (ROOT / args.outdir).resolve()
    _, rows, summary = build_inventory(
        ref=args.ref,
        live=not args.skip_live,
        pdf_pages=not args.skip_pdf_pages,
        workers=max(1, args.workers),
    )
    write_inventory(outdir, rows, summary)
    build_health_report(
        outdir,
        args.ref,
        args.repo,
        rows,
        summary,
        skip_workspace_check=args.skip_workspace_check,
    )

    p_counts: dict[str, int] = {}
    for row in rows:
        p_counts[row.priority] = p_counts.get(row.priority, 0) + 1
    print(f"wrote {outdir}")
    print("priority counts:", ", ".join(f"{k}={p_counts.get(k, 0)}" for k in ("P0", "P1", "P2", "P3")))
    return 0 if not p_counts.get("P0") else 1


if __name__ == "__main__":
    raise SystemExit(main())
