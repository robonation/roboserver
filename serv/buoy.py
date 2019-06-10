import socket
import os
from nmeaserver import formatter
import time
from datetime import datetime, date

# global buoy object 'buoy' holds light buoy state


class Buoy():
    Field = 'None'
    State = '0'
    Voltage = 0
    Time = None
    Connected = False
    
    #: Whether this NMEAServer is being shutdown.
    shutdown_flag = False

    buoy_ip = None
    buoy_port = None
    logs_path = None
    timeutil = None

    def __init__(self, ip, port, logs_path, timeutil):
        self.buoy_ip = ip
        self.buoy_port = port
        self.logs_path = logs_path
        self.timeutil = timeutil
        self.Time = timeutil.aslocaltimestr(datetime.utcnow())

    def BUOYlistener(self):
        while not self.shutdown_flag:
            while not self.Connected:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect((self.buoy_ip, self.buoy_port))
                    self.Connected = True
                    print 'Buoy TCP connected.'
                except BaseException:
                    time.sleep(2)
            while self.Connected:
                try:
                    response = sock.recv(1024)
                    message = formatter.parse(response)
                    name = message['sentence_type']
                    if name == 'BYS':
                        self.Field = message['data'][0]
                        # print 'Field:', self.Field
                        self.State = message['data'][1]
                        # print 'Buoy state:', self.State
                        self.Voltage = float(message['data'][2]) / 1000
                        # print 'Buoy voltage:', self.Voltage
                        self.Time = self.timeutil.rn_timestamp()
                        folder = 'Field_' + str(message['data'][0])
                    else:
                        name = 'BUOYlog'
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
                    print('Buoy TCP disconnected')
                    sock.close()
                    self.Connected = False
