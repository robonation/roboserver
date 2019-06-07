import socket
import os
import nmea
import time
from datetime import datetime, date

#global buoy object 'buoy' holds light buoy state
class Buoy():
    Field = 'None'
    State = '0'
    Voltage = 0
    Time = None
    Connected = False
    
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
        #THIS FUNCTION IS NEARLY IDENTICAL TO PINGlistener()
        while True:
            while not self.Connected:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect((self.buoy_ip, self.buoy_port))
                    self.Connected = True
                    print 'Buoy TCP connected.'
                except:
                    time.sleep(2)
            while self.Connected:
                try:
                    response = sock.recv(1024)
                    message = nmea.parseNMEA(response)
                    name = message['sentence_type']
                    if name == 'BYS':
                        self.Field = message['data'][0]
                        #print 'Field:', self.Field
                        self.State = message['data'][1]
                        #print 'Buoy state:', self.State
                        self.Voltage = float(message['data'][2])/1000
                        #print 'Buoy voltage:', self.Voltage
                        self.Time = self.timeutil.aslocaltimestr(datetime.utcnow())
                        folder = 'Field_'+str(message['data'][0])
                    else:
                        name = 'BUOYlog'
                        folder = 'ERRORS'
                    try:
                        with open(self.logs_path + str(date.today())+'/'+folder+'/'+name+'.txt', 'a') as f:
                            f.write(str(self.Time)+' | '+response)
                    except:
                        os.mkdir(self.logs_path + str(date.today())+'/'+folder)
                        with open(self.logs_path +  str(date.today())+'/'+folder+'/'+name+'.txt', 'a') as f:
                            f.write(str(self.Time)+' | '+response)
                except:
                    print 'Buoy TCP disconnected'
                    sock.close()
                    self.Connected = False
