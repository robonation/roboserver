import pytz
from datetime import datetime, date

class TimeUtil:
    local_tz = None
    
    def __init__(self, timezone):
        self.local_tz = timezone
        
    def utc_to_local(self, utc_dt):
        local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(self.local_tz)
        return self.local_tz.normalize(local_dt)
    
    def aslocaltimestr(self, utc_dt):
        return self.utc_to_local(utc_dt).strftime('%Y-%m-%d %H:%M:%S.%f %Z%z')
    
    def now_to_local_string(self):
        return str(self.aslocaltimestr(datetime.utcnow()))