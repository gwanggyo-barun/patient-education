# Copyright & Asset Protection — 광교바른내과 디자인 자산 보호 디테일

본 문서는 SKILL.md `## 🔐 Copyright & Asset Protection` 섹션의 실무 디테일이다. 코드 예시·파일명 규칙·자동화 스크립트 패턴을 모두 포함.

## 1. SVG 메타데이터 자동 삽입 코드

`shared/_build_helpers.py`에 추가할 함수:

```python
from datetime import datetime
from xml.etree import ElementTree as ET

def inject_copyright_metadata(svg_text: str, asset_id: str, version: str,
                                ai_assisted: bool = False) -> str:
    """SVG 텍스트에 광교바른내과 저작권 metadata 삽입.

    asset_id: 'GBIM-{kind}-{slug}-{fmt}' (예: 'GBIM-handouts-egd-fasting-A4')
    version: 'v01' / 'v02' / ...
    ai_assisted: AI 도구 (Claude/ChatGPT/SD 등) 사용 여부
    """
    today = datetime.now().strftime("%Y-%m-%d")
    ai_flag = "Yes" if ai_assisted else "No"
    metadata = f"""<metadata id="gbim-copyright">
  <![CDATA[
  © 2026 Gwanggyo Bareun Internal Medicine.
  Asset-ID: {asset_id}
  Version: {version}
  Created: {today}
  AI-Assisted: {ai_flag}
  License: Patient education only. Unauthorized redistribution prohibited.
  ]]>
</metadata>
"""
    # <svg ...> 다음 줄에 삽입
    return svg_text.replace("<svg", metadata + "\n<svg", 1) if "<metadata" not in svg_text else svg_text
```

## 2. Invisible Ownership Mark — HTML/CSS

`shared/clinic-slides.css` + `clinic-handout-a4.css`에 추가:

```css
.ownership-mark {
  position: absolute;
  bottom: 4px;
  left: 0;
  right: 0;
  text-align: center;
  font-size: 8px;
  font-family: 'Pretendard Variable', sans-serif;
  color: rgba(0, 0, 0, 0.30);
  letter-spacing: 0.02em;
  pointer-events: none;
  user-select: none;
  z-index: 0;
}

@media print {
  .ownership-mark {
    color: rgba(0, 0, 0, 0.30);  /* 인쇄에서도 표시 */
  }
}
```

각 deck/handout HTML body 끝에:

```html
<div class="ownership-mark">© 2026 광교바른내과 · 무단 수정/재배포 금지</div>
```

build.py에서 자동 삽입 (CSS class만 있으면 표시됨).

## 3. Master File 폴더 구조 (전체)

```
~/clinic-content-system/
├── 01_Master_SVG/
│   ├── decks/
│   │   ├── cardio/htn-2025-aha-acc/master_v03.svg
│   │   └── general/papers-20260524/baxdrostat-baxhtn/master_v03.svg
│   ├── handouts/
│   │   ├── gi/colonoscopy/master_v05.svg
│   │   └── endoscopy/glp1ra-pre-procedure/master_v02.svg
│   └── lab-reports/
│       └── general-checkup/master_v01.svg
├── 02_Export_Print/
│   └── GBIM_BaxHTN_Paper_A4_Print_v03.pdf
├── 03_Export_Web/
│   └── GBIM_BaxHTN_Paper_Web_1920_v03.webp
├── 04_Export_SNS/
│   └── GBIM_BaxHTN_Paper_SNS_1080_v03.png
├── 05_Export_EMR/
│   └── GBIM_BaxHTN_Paper_EMR_A4_v03.pdf
├── 06_Export_Kiosk/
│   └── GBIM_BaxHTN_Paper_Kiosk_1920_v03.png
├── 07_Prompts/
│   └── GBIM-handouts-egd-fasting_prompt_v03.json
└── 08_LICENSE/
    ├── LICENSE_KR.txt
    └── LICENSE_EN.txt
```

`.gitignore` 추가 항목:
```
07_Prompts/*.json
01_Master_SVG/**/*.editable.svg
```

## 4. 파일명 규칙 (강제)

`GBIM_{TopicSlug}_{Kind}_{Format}_v{NN}.{ext}`

- `TopicSlug`: PascalCase 또는 CamelCase (예: `EGD_Fasting`, `BaxHTN_Paper`)
- `Kind`: `Paper` / `Handout` / `LabReport` / `Deck`
- `Format`:
  - `A4` (handout·lab-report)
  - `16x9` (deck)
  - `Web_1920` (web export)
  - `SNS_1080` (SNS card)
  - `EMR_A4` (EMR embed)
  - `Kiosk_1920` (kiosk)
  - `Print` (PDF print)
- `v{NN}`: `v01`, `v02`, ... — 두 자리 숫자 zero-pad

❌ **금지 파일명 패턴**:
- `FINAL_final_v2.svg`
- `final-real-this-time.svg`
- `v3.1.5-thursday.pdf`
- 공백·한글 포함

## 5. LICENSE 전문

### LICENSE_KR.txt

```
광교바른내과 환자 교육 자료 라이선스 (2026)

이 자료의 저작권은 광교바른내과 정지환 원장에게 있습니다.

✅ 허용 사용
- 환자 교육 목적 사용
- 진료실 내부 배포·출력 (포스터·핸드아웃·키오스크)
- 환자 직접 전달 (카카오톡·이메일·문자·문서 인쇄물 포함)
- 의료진 교육·세미나 (출처 표기 시)

❌ 금지 사용
- 상업적 재판매·임대
- 2차 수정·재가공·파생물 제작
- 로고·출처·저작권 표시 제거
- 외부 기관·SNS 공식 계정 무단 배포
  (사전 서면 승인 필요)
- editable SVG·원본 파일 외부 전달
- AI 학습 데이터로 사용

⚠️ 위반 시
- 저작권법에 따른 법적 조치
- 디지털 자산 metadata로 출처 입증 가능
- git history·파일 hash 기록 보존

📞 문의·승인 요청
광교바른내과
주소: 경기도 용인시 수지구 광교중앙로 298, 4층 402-404호
웹: gwanggyo-barun.github.io
원장: 정지환

라이선스 버전: 1.0
발효일: 2026-05-25
```

### LICENSE_EN.txt

```
Gwanggyo Bareun Internal Medicine — Patient Education Materials License (2026)

Copyright © 2026 Gwanggyo Bareun Internal Medicine, Dr. Jihwan Chung.

✅ Permitted Uses
- Patient education purposes
- Internal clinic distribution and printing (posters, handouts, kiosk)
- Direct delivery to patients (KakaoTalk, email, SMS, printed materials)
- Medical education and seminars (with attribution)

❌ Prohibited Uses
- Commercial resale or rental
- Secondary modification, repurposing, derivative works
- Removal of logo, source, copyright marks
- Unauthorized distribution to external institutions, SNS official accounts
  (Prior written authorization required)
- External transfer of editable SVG or source files
- Use as AI training data

⚠️ Violation
- Subject to copyright law enforcement
- Digital asset metadata provides provenance proof
- Git history and file hashes are preserved

📞 Contact / Authorization Requests
Gwanggyo Bareun Internal Medicine
Address: Avenuefrance Gwanggyo 4F, 145 Gwanggyo-Jungang-ro,
         Yeongtong-gu, Suwon-si, Gyeonggi-do, South Korea
Web: gwanggyo-barun.github.io
Director: Dr. Jihwan Chung, MD

License version: 1.0
Effective date: 2026-05-25
```

## 6. Prompt Provenance JSON 스키마

`07_Prompts/{asset-id}_prompt_v{NN}.json`:

```json
{
  "asset_id": "GBIM-handouts-egd-fasting",
  "version": "v03",
  "created": "2026-05-25",
  "model": "ChatGPT GPT-4o (image generation)",
  "platform": "chat.openai.com / web",
  "original_prompt": "Clean flat modern medical illustration, aspect ratio strictly 4:3 (1600 x 1200 pixels), white background...",
  "negative_prompt": "no text, no labels, no captions, no logo",
  "aspect_ratio": "4:3",
  "export_resolution": "1600x1200",
  "iterations": 3,
  "iterations_kept": ["iter_02"],
  "final_path": "shared/assets/generated/egd-fasting-clock-20260513.png",
  "final_sha256": "abc123...",
  "operator": "Claude Code session ID + user 정지환",
  "notes": "1차에 글자가 들어가서 negative prompt 강화 후 재생성. iter_02 채택."
}
```

## 7. 자동화 스크립트 예시

### Mac Hazel rule (Print export watch)
- Watch folder: `~/clinic-content-system/02_Export_Print/`
- Trigger: New file matching `GBIM_*.pdf`
- Action 1: Move to NAS via rsync (`rsync -av "$1" /Volumes/NAS/gbim/02_Export_Print/`)
- Action 2: Tag with `gbim-exported`

### tools/sync_to_nas.sh
```bash
#!/usr/bin/env bash
NAS="/Volumes/NAS/gbim"
[ ! -d "$NAS" ] && echo "NAS not mounted" && exit 1
for d in 01_Master_SVG 02_Export_Print 03_Export_Web 04_Export_SNS 05_Export_EMR 06_Export_Kiosk 07_Prompts 08_LICENSE; do
  rsync -av --delete-after "$HOME/clinic-content-system/$d/" "$NAS/$d/"
done
echo "✓ NAS sync completed: $(date)"
```

### tools/Watch-Export.ps1 (Windows)
```powershell
$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = "$env:USERPROFILE\clinic-content-system\02_Export_Print"
$watcher.Filter = "GBIM_*.pdf"
Register-ObjectEvent $watcher "Created" -Action {
  $src = $Event.SourceEventArgs.FullPath
  Copy-Item $src "\\NAS\gbim\02_Export_Print\" -Force
  Write-Host "Backed up $src"
}
```

### tools/pack_for_share.sh
```bash
#!/usr/bin/env bash
# Usage: ./pack_for_share.sh GBIM-handouts-egd-fasting v03
ASSET=$1
VER=$2
OUT="shared_${ASSET}_${VER}.zip"
cd ~/clinic-content-system
zip -r "$OUT" \
  "02_Export_Print/${ASSET}*${VER}*" \
  "03_Export_Web/${ASSET}*${VER}*" \
  "08_LICENSE/LICENSE_KR.txt" \
  "08_LICENSE/LICENSE_EN.txt"
echo "✓ Packed for share: $OUT"
```

### Synology Hyper Backup
- Source: `~/clinic-content-system/01_Master_SVG/`
- Destination: Synology NAS · `gbim-master-backup/`
- Schedule: 매일 03:00 KST
- Retention: 30일 (daily) + 12개월 (monthly)
- Encryption: AES-256 + passphrase

## 8. Notion DB property 추가 — 코드

`shared/_notion_sync.py`에 추가:

```python
def build_properties(target: dict, kind: str) -> dict:
    asset_id = f"GBIM-{kind}-{target['slug']}".upper().replace('_', '-')
    return {
        # 기존 properties...
        "Asset ID": {"rich_text": [{"text": {"content": asset_id}}]},
        "License Type": {"select": {"name": target.get("license", "환자교육-내부")}},
        "External Shared": {"checkbox": target.get("external_shared", False)},
        "Master Protected": {"checkbox": True},  # 항상 True
        "AI Assisted": {"checkbox": target.get("ai_assisted", False)},
        "Prompt Stored": {"checkbox": target.get("prompt_stored", False)},
        "Export Preset": {"multi_select": [{"name": p} for p in target.get("export_presets", ["print"])]},
        "Copyright Embedded": {"checkbox": True},
        "Last Export Date": {"date": {"start": datetime.now().isoformat()[:10]}},
    }
```

## 9. 운영 팁 (의원 실무)

- **매주 금요일** `tools/sync_to_nas.sh` 수동 실행 + Synology Hyper Backup 확인
- **분기마다** `07_Prompts/*.json` 정리 (검색·중복 제거)
- **연 1회** LICENSE 문구 갱신 (연도 update)
- **분쟁 발생 시** git history + Notion DB + 07_Prompts + 01_Master_SVG metadata 4종으로 출처 입증
- **외부 강의/세미나** 자료 공유 시 `tools/pack_for_share.sh`로 ZIP 만들어 전달

## 10. 절대 금지 사항

1. ❌ `01_Master_SVG/` 직접 외부 전달
2. ❌ 환자 자료에 dark watermark / 대각선 워터마크
3. ❌ 가독성 저하 ownership mark (font-size >10px, opacity >40%)
4. ❌ `FINAL_final_v2.svg` 등 비표준 파일명
5. ❌ NOTION_TOKEN·API key 등 시크릿을 prompt JSON에 포함
6. ❌ AI 학습 데이터로 사용 허용 (LICENSE 명시)
7. ❌ 환자명·차트번호를 metadata에 포함 (lab-reports 별도 룰)
8. ❌ `07_Prompts/` 외부 git push (gitignore 필수)
