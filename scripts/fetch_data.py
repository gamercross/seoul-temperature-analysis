"""
서울 일별 기온 데이터 수집 스크립트
출처: Open-Meteo Historical Weather API (https://open-meteo.com/) - 무료, API 키 불필요, CC BY 4.0
좌표: 서울(위도 37.5665, 경도 126.978)
기간: 2023-01-01 ~ 2024-12-31 (731일)
"""
import requests
import pandas as pd

URL = "https://archive-api.open-meteo.com/v1/archive"
PARAMS = {
    "latitude": 37.5665,
    "longitude": 126.978,
    "start_date": "2023-01-01",
    "end_date": "2024-12-31",
    "daily": "temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum",
    "timezone": "Asia/Seoul",
}

def main():
    res = requests.get(URL, params=PARAMS, timeout=30)
    res.raise_for_status()
    daily = res.json()["daily"]
    df = pd.DataFrame(daily)
    df = df.rename(columns={
        "time": "date",
        "temperature_2m_max": "temp_max",
        "temperature_2m_min": "temp_min",
        "temperature_2m_mean": "temp_mean",
        "precipitation_sum": "precipitation",
    })
    df.to_csv("data/seoul_daily_temperature_2023_2024.csv", index=False, encoding="utf-8-sig")
    print(f"saved {len(df)} rows -> data/seoul_daily_temperature_2023_2024.csv")

if __name__ == "__main__":
    main()
