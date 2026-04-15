"""报告模板"""

def generate_segment_report(segment: str, data: dict) -> dict:
    """生成时段报告"""
    return {
        "segment": segment,
        "data": data
    }

def generate_daily_report(data: dict) -> dict:
    """生成每日报告"""
    return {
        "type": "daily",
        "data": data
    }
