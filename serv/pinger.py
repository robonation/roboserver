import socket
import os
from nmeaserver import formatter
import time
from datetime import datetime, date

# global pinger object 'ping' holds pinger state


class Pinger():
    Field = 'None'
    Active = 0
    Sync = 'I'
    Voltage = 0
    Time = None
    Connected = False

    pinger_ip = None
    pinger_port = None
    log_path = None
    timeutil = None

    def __init__(self, ip, port, log_path, timeutil):
        self.pinger_ip = ip
        self.pinger_port = port
        self.log_path = log_path
        self.timeutil = timeutil
        self.Time = timeutil.aslocaltimestr(datetime.utcnow())

    # connect to pinger via TCP
    def PINGlistener(self):
        while True:
            # try to connect to the pinger box
            while not self.Connected:
                try:
                    # create a new socket and try to connect
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect((self.pinger_ip, self.pinger_port))
                    print('Pinger TCP connected')
                    self.Connected = True
                except BaseException:
                    # if it doesn't work, try again in two seconds
                    time.sleep(2)
            # once we are connected to the pingers:
            while self.Connected:
                try:
                    response = sock.recv(1024)
                    # print response, 'received from', addr
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
                    print('Pinger TCP disconnected')
                    sock.close()
