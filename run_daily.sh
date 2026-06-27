#!/bin/bash
# 창원 아파트 리포트 — 매일 실행 스크립트 (launchd가 호출)
cd "/Users/leeseunghwan/Documents/claude/1st test/changwon-apt-report" || exit 1
mkdir -p logs
echo "===== $(date '+%Y-%m-%d %H:%M:%S') 실행 시작 =====" >> logs/daily.log
./venv/bin/python run_p1.py >> logs/daily.log 2>&1
echo "===== $(date '+%Y-%m-%d %H:%M:%S') 실행 종료 (exit $?) =====" >> logs/daily.log
