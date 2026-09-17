# 서울 기온 시계열 인사이트 분석

시계열 데이터를 선정해 스스로 질문을 던지고, 정제·분석·시각화·해석까지 완결하는 데이터 분석 학습 미션의 결과물입니다. 서울의 2023~2024년 일별 기온 데이터를 대상으로 진행했습니다.

## 현재 상태

- [x] 데이터 수집 (100+ 포인트, 출처/기간 명시)
- [x] 분석 질문 4개 설계
- [x] 데이터 정제 + 시계열 분석 기법 4가지 적용
- [x] 시각화 4개 (필수 2개 이상 충족)
- [x] 인사이트 4개 (관찰-해석-행동 구조로 작성, 3개 이상 충족)
- [x] REPORT.md 작성 (AI 사용 로그 포함)
- [x] 재현성 문서화 (`requirements.txt`, 실행 방법)
- [x] GitHub 저장소 정리 및 공개
- [x] **[보너스] 웹 대시보드 서비스화** — `main`에 병합 완료
- [x] **[보너스] 시계열 심화 분석** — STL 분해(추세/계절성) 포함

## 진행 방식

1. **문제 분석**: manyfast(매니패스트)에서 PRD(제품 개요: 목표/타겟/KPI/리스크)를 먼저 정리하고, 세부 요구사항(Requirements→Features→Specs) 분해는 PRO 플랜이 필요해 동일한 구조를 로컬 문서로 대체해 작성함
2. **데이터 선정**: 주가/기온/판매량 중 기온 데이터(Open-Meteo API, 서울)를 선택 — API 키 없이 바로 수집 가능하고 계절성이 뚜렷해 시계열 기법 효과를 확인하기 좋음
3. **수집 → 정제 → 분석 → 시각화 → 리포트**: `scripts/fetch_data.py`로 원본 수집, `scripts/analysis.py`로 정제·분석·시각화, 결과를 `REPORT.md`에 정리
4. **보너스**: `scripts/dashboard.py`(Streamlit)로 기간/집계 단위를 바꿔가며 탐색 가능한 대시보드 추가. 별도 브랜치(`feature/dashboard`)에서 작업 후 PR로 병합
5. **버전 관리**: 이후 모든 변경은 `main`에 직접 푸시하지 않고 **브랜치 생성 → PR → 사용자 직접 머지** 방식으로 진행

## 폴더 구조

```
seoul-temperature-analysis/
├── data/
│   ├── seoul_daily_temperature_2023_2024.csv   # 원본 수집 데이터
│   └── seoul_daily_temperature_processed.csv   # 정제·가공 후 데이터
├── images/
│   ├── 01_temp_trend_moving_average.png
│   ├── 02_monthly_average_seasonality.png
│   ├── 03_rolling_volatility.png
│   └── 04_stl_decomposition.png                # 보너스: 시계열 분해
├── scripts/
│   ├── fetch_data.py                           # 데이터 수집
│   ├── analysis.py                             # 정제·시계열 분석·시각화
│   └── dashboard.py                            # 보너스: Streamlit 대시보드
├── REPORT.md                                   # 분석 리포트 (질문/시각화/인사이트/결론)
├── DASHBOARD.md                                # 보너스 대시보드 실행 방법·시나리오
└── requirements.txt
```

## 빠른 시작

```bash
pip install -r requirements.txt

# 1) 데이터 수집
python3 scripts/fetch_data.py

# 2) 정제·분석·시각화 (images/ 생성, 인사이트 수치 출력)
python3 scripts/analysis.py

# 3) [보너스] 대시보드 실행
streamlit run scripts/dashboard.py
```

- Python 3.10 이상
- 데이터 출처: [Open-Meteo Historical Weather API](https://open-meteo.com/) (CC BY 4.0, API 키 불필요)

## 문서

- 분석 질문 · 시각화 · 인사이트 · 결론/한계 · AI 사용 로그 → [REPORT.md](REPORT.md)
- 대시보드 실행 방법 · 필터 변경 시나리오 → [DASHBOARD.md](DASHBOARD.md)
