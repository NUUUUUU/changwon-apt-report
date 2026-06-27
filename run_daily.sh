#!/bin/bash
# 창원 아파트 리포트 — 매일 실행 (launchd가 호출): 분석→HTML→카톡→GitHub Pages 푸시
cd "/Users/leeseunghwan/Documents/claude/1st test/changwon-apt-report" || exit 1
mkdir -p logs
echo "===== $(date '+%Y-%m-%d %H:%M:%S') 시작 =====" >> logs/daily.log
./venv/bin/python run_p1.py >> logs/daily.log 2>&1

# GitHub Pages 갱신 (docs 커밋·푸시 — remote URL에 토큰 저장돼 있음)
git add docs >> logs/daily.log 2>&1
git -c user.email="lsh3328@gmail.com" -c user.name="이승환" commit -q -m "리포트 $(date '+%Y-%m-%d')" >> logs/daily.log 2>&1
git push origin main >> logs/daily.log 2>&1

echo "===== $(date '+%Y-%m-%d %H:%M:%S') 종료 (exit $?) =====" >> logs/daily.log
