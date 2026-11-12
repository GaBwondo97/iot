def calculate_aqi_from_pm25(pm25: float) -> float:
    # Simplified EPA approximation
    if pm25 <= 12.0: return pm25 * (50/12)
    elif pm25 <= 35.4: return 50 + (pm25 - 12) * (49/23.4)
    else: return 100 + (pm25 - 35.4) * (50/20)
