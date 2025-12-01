from datetime import datetime

def get_chinese_time_desc():
    now = datetime.now()
    hour = now.hour
    if 5 <= hour < 12:
        period = "早上"
    elif 12 <= hour < 14:
        period = "中午"
    elif 14 <= hour < 18:
        period = "下午"
    elif 18 <= hour < 22:
        period = "晚上"
    else:
        period = "深夜"
        
    return f"现在是 {period}。"

USER_SILENT_MSG = ""
SYSTEM_RECALL_MSG = "[回想起了以下内容：{}]"
DEFAULT_ERROR_RESPONSE = "似乎走神了..."
