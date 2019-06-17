import socket
import os
from nmeaserver import formatter
import time
import threading
from datetime import datetime, date
import logging
import signal

logger = logging.getLogger(__name__)
signal.signal(signal.SIGINT, signal.SIG_DFL)

# global pinger object 'ping' holds pinger state


class Pinger(threading.Thread):
    Field = 'None'
    Active = 0
    Sync = 'I'
    Voltage = 0
    Time = None
    Connected = False

    #: Whether this NMEAServer is being shutdown.
    shutdown_flag = False
    pinger_ip = None
    pinger_port = None
    logs_path = None
    timeutil = None

    def __init__(self, ip, port, logs_path, timeutil, name="Pinger", daemon=True):
        self.pinger_ip = ip
        self.pinger_port = port
        self.logs_path = logs_path
        self.timeutil = timeutil
        self.Time = timeutil.aslocaltimestr(datetime.utcnow())
        threading.Thread.__init__(self, name=name)
        self.setDaemon(daemon)

    # connect to pinger via TCP
    def run(self):
        logger.info("Pinglistener connecting to {}:{}".format( \
            self.pinger_ip, self.pinger_port))

        sock = None
        while not self.shutdown_flag:
            # try to connect to the pinger box
            if not self.Connected:
                try:
                    # create a new socket and try to connect
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(3)
                    sock.connect((self.pinger_ip, self.pinger_port))
                    logger.info('Pinger TCP connected')
                    self.Connected = True
                except BaseException:
                    # if it doesn't work, try again in two seconds
                    time.sleep(2)
            # once we are connected to the pingers:
            else:
                try:
                    response = sock.recv(1024)
                    message = formatter.parse(response)
                    # update the field docs with buoy and pinger info.
                    name = message['sentence_type']
                    if name == 'PNS':
                        self.Field = message['data'][0]
                        # print 'Field:', self.Field
                        self.Active = message['data'][1]
                        # print 'Active pinger:', self.Active
                        self.Sync = message['data'][2]
                        # print 'Pinger Sync Mode:', self.Sync
                        self.Voltage = float(message['data'][3]) / 1000
                        # print 'Pinger voltage:', self.Voltage
                        self.Time = self.timeutil.aslocaltimestr(
                            datetime.utcnow())
                        # print 'Time:', str(self.Time)
                        folder = 'Field_' + str(message['data'][0])

                    else:
                        name = 'PINGlog'
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
                    logger.exception("Exc:")
                    logger.error('Pinger TCP disconnected')
                    time.sleep(2)
                    sock.close()
                    self.Connected = False

    def shutdown(self):
        self.shutdown_flag = True
        self.join(3)