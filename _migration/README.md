# 진료 교육자료 일괄 재작성 (Migration)

레거시 Notion 첨부 PDF/PPTX 약 42개 → `clinic-content-system` 표준 (HTML+PDF) 일괄 재작성.

## 사용법

```bash
export NOTION_TOKEN="secret_..."   # Patient Education Auto-publish integration

# Phase 0: 인벤토리
python scripts/01_scan_db.py
# → inventory.csv 생성

# Phase 1: 원본 다운로드
python scripts/02_download_all.py
# → raw/{page_id_short}_{slug}.{pdf|pptx}

# Phase 2~: WIP
```

## 디렉토리

```
_migration/
├── inventory.csv          (Phase 0 산출물)
├── raw/                   (Phase 1 다운로드)
├── extracted/             (Phase 3a 텍스트 추출)
├── drafts/                (Phase 3b LLM 초안 HTML)
├── review_queue.md        (검수 대기열)
└── scripts/
    ├── 01_scan_db.py
    ├── 02_download_all.py
    └── ...
```
