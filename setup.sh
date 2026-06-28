#!/bin/bash
# 창원 아파트 리포트 — 초기 설정 (venv + 의존성 + .env 템플릿)
cd "$(dirname "$0")" || exit 1

echo "[1/3] Python 가상환경(venv) 생성..."
PY="$(command -v python3.13 || command -v python3)"
"$PY" -m venv venv

echo "[2/3] 의존성 설치..."
./venv/bin/pip install -q -U pip
./venv/bin/pip install -q -r requirements.txt

echo "[3/3] .env 준비..."
if [ -f .env ]; then
  echo "    .env 이미 있음 (유지)"
else
  cp .env.example .env
  echo "    .env 생성됨 → API 키를 채워주세요"
fi

echo ""
echo "✅ 설정 완료!"
echo "   다음 단계:"
echo "   1) .env 에 API 키 입력 (README의 '사전 준비' 참고)"
echo "   2) config.yaml 에서 직장 좌표·필터·지역 조정"
echo "   3) ./venv/bin/python run_p1.py   (리포트 생성·발송)"
