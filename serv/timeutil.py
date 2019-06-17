import pytz
import logging
from datetime import datetime
import time

logger = logging.getLogger(__name__)
class TimeUtil:
    local_tz = None

    def __init__(self, timezone):
        self.local_tz = timezone

    def utc_to_local(self, utc_dt):
        local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(self.local_tz)
        return self.local_tz.normalize(local_dt)

    def aslocaltimestr(self, utc_dt):
        return self.utc_to_local(utc_dt).strftime('%Y-%m-%d %H:%M:%S.%f %Z%z')

    def rn_timestamp(self):
        return str(self.aslocaltimestr(datetime.utcnow()))

    def nmea_timestamp(self):
        return str(datetime.now().strftime("%m%d%y,%H%M%S"))
    
    def log_timestamp(self, hbdate, hbtime):
        try:
            timestamp = time.strptime(str(hbdate)+","+str(hbtime), "%m%d%y,%H%M%S")
            return time.strftime("%m/%d/%y %H:%M:%S", timestamp)
        except BaseException:
            logger.exception("Error in log_timestamp. ")
            return str(hbdate)+" "+str(hbtime)
