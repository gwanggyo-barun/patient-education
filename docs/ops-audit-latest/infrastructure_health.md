# Infrastructure Health Report

- Generated: 2026-06-14T05:52:10.897188+00:00
- Repo: `gwanggyo-barun/patient-education`
- Source ref: `origin/main`
- Pages URL: https://gwanggyo-barun.github.io/patient-education/

## Current State

- Build and Deploy: success at 2026-06-14T04:51:41Z (push, d1969d4)
- Content Regression Tests: success at 2026-06-14T04:47:09Z (push, d1969d4)
- Notion Link Audit: no recent run found

## Findings

- P2 `notion-sync`: Content Regression Tests has a stale optional Notion sync step; current _notion_sync.py has no sync_all, so it skips
- P1 `notion-link-audit`: link-audit artifact can include page_title; lab-report titles are PHI-sensitive

## Run Mix (last 30)

- Build and Deploy / cancelled: 4
- Build and Deploy / success: 11
- Content Regression Tests / cancelled: 3
- Content Regression Tests / failure: 7
- Content Regression Tests / success: 5

## Notes

- Content/layout failures are classified separately from deploy/runner failures.
- lab-reports titles are redacted from inventory outputs by default.
