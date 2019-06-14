import socket
import os
from nmeaserver import formatter
import time
from datetime import datetime, date
import threading
import logging
import signal

logger = logging.getLogger(__name__)
signal.signal(signal.SIGINT, signal.SIG_DFL)

class SevenSeg(threading.Thread):
    Field = ''
    State = '0'
    Voltage = 0
    Time = None
    Connected = False
    
    #: Whether this NMEAServer is being shutdown.
    shutdown_flag = False
    sevenseg_ip = None
    sevenseg_port = None
    logs_path = None
    timeutil = None

    def __init__(self, ip, port, logs_path, timeutil, name="SevenSeg", daemon=True):
        self.sevenseg_ip = ip
        self.sevenseg_port = port
        self.logs_path = logs_path
        self.timeutil = timeutil
        self.Time = timeutil.aslocaltimestr(datetime.utcnow())
        threading.Thread.__init__(self, name=name)
        self.setDaemon(daemon)

    def run(self):
        logger.info("SevenSeglistener connecting to {}:{}".format( \
            self.buoy_ip, self.buoy_port))
        while not self.shutdown_flag:
            if not self.Connected:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    sock.connect((self.buoy_ip, self.buoy_port))
                    self.Connected = True
                    logger.info('Buoy TCP connected.')
                except BaseException:
                    time.sleep(2)
            else:
                try:
                    sock.send(formatter.format("RXSTA,A"))
                    response = sock.recv(1024)
                    message = formatter.parse(response)
                    name = message['sentence_type']
                    if name == 'SSS':
                        self.Field = message['data'][0]
                        # print 'Field:', self.Field
                        self.State = message['data'][1]
                        # print 'Buoy state:', self.State
                        self.Voltage = float(message['data'][2]) / 1000
                        # print 'Buoy voltage:', self.Voltage
                        self.Time = self.timeutil.rn_timestamp()
                        folder = 'Field_' + str(message['data'][0])
                    else:
                        name = 'SevenSeglog'
                        folder = 'ERRORS'

                    log_folder = self.logs_path + \
                        str(date.today()) + '/' + folder
                    log_file = log_folder + '/' + name + '.txt'
                    try:
                        with open(log_file, 'a') as f:
                            f.write(str(self.Time) + ' | ' + response)
                    except BaseException:
                        os.mkdir(log_folder)
                        with open(log_file, 'a') as f:
                            f.write(str(self.Time) + ' | ' + response)
                except BaseException:
                    logger.info('SevenSeg TCP disconnected')
                    sock.close()
                    self.Connected = False
        logger.info("SevenSeglistener done")

    def shutdown(self):
        self.shutdown_flag = True
        self.join(3)