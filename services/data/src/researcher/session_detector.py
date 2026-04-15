"""时段检测器 - 判断当前交易时段"""
from datetime import datetime

def get_current_session() -> str:
    """获取当前交易时段"""
    now = datetime.now()
    hour = now.hour

    if 9 <= hour < 15:
        return "domestic_day"
    elif 21 <= hour < 24:
        return "domestic_night"
    else:
        return "overnight"
