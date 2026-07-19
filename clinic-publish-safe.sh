#!/usr/bin/env bash
# clinic-publish-safe — 어느 머신에서든 "안전 발행 한 방" (작업 큐 ② 발행 파트, 2026-07-18).
#
# publish.sh 는 이미 강력하다(직렬화 락·게이트·orphan 자식커밋·kz-015 pre-push 훅). 이 래퍼는 그
# **앞단**을 강제해 사람이 매번 기억하던 규율을 코드로 만든다:
#   1) main 브랜치 강제(아니면 자동 checkout)
#   2) git pull --ff-only  — 발행 전 origin 동기(미니 auto-pull 이 이미 했어도 재확인, 다른 머신 대비)
#   3) 인덱스 클린 확인(publish.sh 요구: 정확 staging 위해 staged 비어야. 워킹트리 콘텐츠 변경은 OK)
#   4) 전량 재빌드 감지 — 매니페스트 shared_sha != 현재 _shared_sha(), 또는 인자 없음(=명시 전량).
#      전량은 162개 ~50분 "입장료"라 **--yes 없이는 자동 진행 안 함**(조용히 50분 안 태움).
#   5) publish.sh 실행(증분=`--only <slug...>` / 전량=무인자). kz-015 훅이 push 정합 최종 검사.
#
# 정책(사용자 승인): 증분 + 게이트 초록 → 자동 발행 / 전량 재빌드 → --yes 확인 요구.
# 한계: 두 머신 동시 발행은 .publish.lock(로컬락)이라 레이스. 실무상 한 머신서만 발행(사용자 확약).
#
# 사용:
#   ./clinic-publish-safe.sh --only pneumococcal-adult-2026     # 특정 타깃만(증분)
#   ./clinic-publish-safe.sh --only a b c                        # 여러 타깃
#   ./clinic-publish-safe.sh --yes                               # 전량 재빌드 발행(확인됨)
#   ./clinic-publish-safe.sh --full --yes                        # 명시 전량(무인자와 동일 결과)
#   ./clinic-publish-safe.sh --kind decks --yes                  # kind 전체(대형 — 확인 필요)
set -euo pipefail
cd "$(dirname "$0")"
REPO="$PWD"

ASSUME_YES=0
EXPLICIT_FULL=0   # --full: 선택자 없으면 전 타깃(build.py:600-601, is_full)
HAS_ONLY=0        # --only: 소수 타깃 부분빌드(진짜 증분)
HAS_KIND=0        # --kind: kind 전체 부분빌드(대형 — 확인 요구)
PUBLISH_ARGS=()
for a in "$@"; do
  case "$a" in
    --yes)           ASSUME_YES=1 ;;
    --full)          EXPLICIT_FULL=1; PUBLISH_ARGS+=("$a") ;;
    --only|--only=*) HAS_ONLY=1;      PUBLISH_ARGS+=("$a") ;;   # =형(--only=x)도 셀렉터로 인식
    --kind|--kind=*) HAS_KIND=1;      PUBLISH_ARGS+=("$a") ;;   # =형 누락 시 --yes 게이트 우회됨(F2)
    *)               PUBLISH_ARGS+=("$a") ;;
  esac
done

# --full + 셀렉터 = 모순 조합 거부. build.py 는 --only/--kind 가 있으면 --full 을 조용히
# 무시하고 **부분빌드**를 한다(build.py:600-601 — is_full 은 "선택 ids == 전체"로만 판정).
# "--full 인데 부분 실행"은 F1 계열 오도라 fail-closed.
if [ "$EXPLICIT_FULL" = 1 ] && { [ "$HAS_ONLY" = 1 ] || [ "$HAS_KIND" = 1 ]; }; then
  echo "✗ --full 과 --only/--kind 동시 지정 — build.py 는 셀렉터가 이겨 부분빌드가 된다(--full 무시됨)."
  echo "  전량이면 --full(또는 무인자)만, 부분이면 셀렉터만 지정해."
  exit 2
fi

# bash: 빈 배열을 set -u 하에서 안전 확장 + %q(공백 인자도 복붙 안전한 재실행 커맨드) 헬퍼
pa() { [ "${#PUBLISH_ARGS[@]}" -gt 0 ] && printf '%q ' "${PUBLISH_ARGS[@]}"; }

# ── 1) main 브랜치 강제 ─────────────────────────────────────────────
BR="$(git rev-parse --abbrev-ref HEAD)"
if [ "$BR" != "main" ]; then
  echo "→ 현재 브랜치 '$BR' — main 으로 checkout"
  git checkout main
fi

# ── 2) 발행 전 동기: ff-only pull(로컬 커밋이 앞서있거나 분기면 실패 → 사람이 해결) ──
echo "→ git pull --ff-only origin main"
if ! git pull --ff-only origin main; then
  echo "✗ pull --ff-only 실패 — 로컬이 origin 과 분기했거나 미커밋 변경과 충돌."
  echo "  해결(예: git stash / 커밋 / git pull --rebase) 후 다시 실행."
  exit 1
fi

# ── 3) 인덱스 클린(staged 비어야 publish.sh 가 정확히 staging) ──
if ! git diff --cached --quiet; then
  echo "✗ staged(인덱스) 변경 존재 — publish.sh 가 발행 파일만 정확히 stage 하려면 인덱스가 비어야 함."
  echo "  'git reset' 로 인덱스만 비운 뒤 재실행(워킹트리 콘텐츠 변경은 publish.sh 가 스테이징함)."
  exit 1
fi

# ── 4) shared-변경 정합 + 전량/대형 재빌드 감지 ─────────────────────
#   build.py: 무인자·--full = 전 타깃(is_full) / --only·--kind = 부분빌드.
#   부분빌드는 shared/·build.py 가 바뀌면 다운스트림에서 SHARED_CHANGED(exit2)로 끊긴다
#   (_publish_gates.py:820-827). 그래서 셀렉터+shared변경은 애초에 발행 불가 → 여기서 명확히 거부.
#   확인 요구 대상: 전량(무인자/--full)·대형(--kind, kind 전체)·shared 변경.
SHARED_MISMATCH=0
# shared_sha 일치=exit0, 불일치/오류=exit3. if-조건이라 set -e 에 안 걸림.
if python3 - <<'PY'
import sys, json
sys.path.insert(0, "shared")
try:
    import _publish_gates as G
    man = json.load(open(".publish-manifest.json"))
    sys.exit(0 if man.get("shared_sha") == G._shared_sha() else 3)
except Exception:
    sys.exit(3)
PY
then :; else SHARED_MISMATCH=1; fi

# shared 변경 + 부분셀렉터(--only/--kind) → 부분빌드는 다운스트림에서 막힌다.
# 실패할 커맨드를 안내하지 말고(F1), 전량으로 유도한다.
if [ "$SHARED_MISMATCH" = 1 ] && { [ "$HAS_ONLY" = 1 ] || [ "$HAS_KIND" = 1 ]; }; then
  echo ""
  echo "✗ shared/·build.py 변경 감지 → 부분빌드(--only/--kind) 발행 불가"
  echo "  (부분빌드는 게이트에서 SHARED_CHANGED 로 중단됨). 전량 재빌드가 필요해:"
  echo "        ./clinic-publish-safe.sh --yes        # 무인자 = 전 타깃(~50분)"
  exit 2
fi

FULL_REBUILD=0
[ "${#PUBLISH_ARGS[@]}" -eq 0 ] && FULL_REBUILD=1   # 무인자 = 전량
[ "$EXPLICIT_FULL" = 1 ]        && FULL_REBUILD=1   # --full = 명시 전량
[ "$HAS_KIND" = 1 ]             && FULL_REBUILD=1   # --kind = kind 전체(대형)
[ "$SHARED_MISMATCH" = 1 ]      && FULL_REBUILD=1   # shared 변경(위에서 부분셀렉터는 이미 거부)

if [ "$FULL_REBUILD" = 1 ] && [ "$ASSUME_YES" != 1 ]; then
  echo ""
  echo "⚠️  전량/대형 재빌드야 (무인자·--full·--kind 또는 shared/·build.py 변경 = 최대 162개 렌더 ~50분)."
  echo "    콘텐츠가 안 바뀌었으면 시각적 동일이지만 시간 든다. 확인되면 --yes 추가:"
  echo "        ./clinic-publish-safe.sh $(pa)--yes"
  exit 2
fi

# ── 5) 실제 발행(publish.sh = 빌드+게이트+orphan+매니페스트+push, kz-015 훅이 정합 검사) ──
#   메시지는 실제 실행 커맨드를 그대로 반영(F1: '전량' 찍고 증분 실행하는 오도 제거).
if [ "${#PUBLISH_ARGS[@]}" -gt 0 ]; then
  echo "→ 발행: ./publish.sh $(pa)"
  ./publish.sh "${PUBLISH_ARGS[@]}"
else
  echo "→ 전량 발행: ./publish.sh   (~50분)"
  ./publish.sh
fi
echo "✅ clinic-publish-safe 완료"
