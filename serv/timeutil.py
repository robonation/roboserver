import pytz
import logging
from datetime import datetime
import time

logger = logging.getLogger(__name__)
class TimeUtil:
    local_tz = None

    def __init__(self, timezone):
        self.local_tz = timezone if timezone is not None else pytz.utc

    def rn_timestamp(self):
        
        return str(datetime.now(self.local_tz).strftime('%Y-%m-%d %H:%M:%S.%f %Z%z'))

    def nmea_timestamp(self):
        return str(datetime.now().strftime("%m%d%y,%H%M%S"))
    
    def log_timestamp(self, hbdate, hbtime):
        try:
            timestamp = time.strptime(str(hbdate)+","+str(hbtime), "%d%m%y,%H%M%S")
            return time.strftime("%m/%d/%y %H:%M:%S", timestamp)
        except BaseException:
            logger.exception("Error in log_timestamp. ")
            return str(hbdate)+" "+str(hbtime)
