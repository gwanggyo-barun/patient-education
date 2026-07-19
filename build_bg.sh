#!/bin/bash
# QW4 (2026-07-12): build.py 백그라운드 오프로드 — 세션/텔레그램 브리지가 무거운 빌드에 물리지 않게.
# 사용:  ./build_bg.sh                 # 전량(180) 백그라운드
#        ./build_bg.sh --kind decks    # 덱만
#        ./build_bg.sh --only graves-disease   # 한 타깃만(로컬 프리뷰)
# 로그는 build.<타임스탬프>.log 로. 진행은 tail -f 로 확인.
cd "$(dirname "$0")" || exit 1
LOG="build.$(date +%Y%m%d-%H%M%S).log"
nohup python3 build.py "$@" > "$LOG" 2>&1 &
PID=$!
echo "build.py 백그라운드 시작 (PID $PID, args: $*) → 로그: $LOG"
echo "진행:  tail -f $LOG"
echo "중단:  kill $PID"
