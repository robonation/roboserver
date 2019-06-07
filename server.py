#!/usr/bin/env python

import os
import threading
import time
import pytz
import errno
import sys
from serv import nmea, pinger, buoy
from serv import timeutil
from datetime import datetime, date
from serv.nmea import NMEAServer

#LOGS_PATH may need to change depending on where you are running this file from
LOGS_PATH = 'logs/'
WEB_PATH = 'wwwroot/'
HTML_HEADER = '<head><title>RoboBoat 2019</title><meta http-equiv="refresh" content="5" ></head>'

timeutil = timeutil.TimeUtil(pytz.timezone('US/Eastern'))
ping = pinger.Pinger('192.168.1.6', 4000, LOGS_PATH, timeutil)
buoy = buoy.Buoy('192.168.1.11', 4000, LOGS_PATH, timeutil)
nmeaserver = NMEAServer('',9000)

#The following object holds all information for a team's run
class Team():
    name = None
    date = 0
    hbdate = 0
    time = 0
    hbtime = 0
    lat = 0.0
    NS = 'N'
    lon = 0.0
    EW = 'E'
    mode = '1'
    dock = ''
    flag = ''

    #Heartbeat message parsing and story log
    def HRB(self, message, logfile):
        self.hbdate = message[0]
        self.hbtime = message[1]
        self.lat = message[2]
        self.NS = message[3]
        self.lon = message[4]
        self.EW = message[5]
        self.name = message[6]
        #write out to story log on mode change
        if self.mode != message[7]:
            if message[7] == '2':
                #write out to story log
                print(self.name + 'Vehicle in Auto\n')
                
                log = 'vehicle is autonomous. Run started.\n'
                if ping.Connected:
                    log += 'Field {} pinger {} active.\n'.format(ping.Field, ping.Active)
                else:
                    log += 'Pinger not connected.'
                if buoy.Connected:
                    log += 'Field {} Light buoy at {}.\n'.format(buoy.Field, buoy.State)
                else:
                    log += 'Light buoy not connected.'
                    
                self.print_log(log, logfile)
            elif message[7] == '1':
                print(self.name + 'vehicle is in manual mode. run ended.\n')
                self.print_log('vehicle is in manual mode. run ended.\n', logfile)
        self.mode = message[7]

    #Raise The Flag message parsing and story log
    def FLG(self, message, logfile):
        self.date = message[0]
        self.time = message[1]
        self.name = message[2]
        self.flag = message[3]
        self.print_log('reports Raise The Flag number: '+self.flag+'.\n', logfile)

    #Docking message parsing and story log
    def DOK(self, message, logfile):
        self.date = message[0]
        self.time = message[1]
        self.name = message[2]
        self.dock = message[3]
        self.print_log('reports Automated Docking in: '+self.dock+'.\n', logfile)
    
    #Write out to story log
    def print_log(self, message, logfile):
        try:
            logfile.write(timeutil.now_to_local_string()+'\n'+self.name+' '+message)
        except:
            print('no story log file created.')
            



@nmeaserver.connection_context_creator()
def onConnectionEstablished(context):
    print("Connection established")
    context['team'] = Team()
    return context

@nmeaserver.prehandler()
def onEveryMessageBeforeHandler(context, raw_message):
    team = context['team']
    
    if team.name is None:
        message = nmea.parseNMEA(raw_message, False)
        team.name = message['data'][0]
        context['logfile'] = open(LOGS_PATH+str(date.today())+'/'+team.name+'_STORY.txt','a')
        context['rawlog'] = open(LOGS_PATH+str(date.today())+'/'+team.name+'_RAW.txt','a')
        print('Team '+team.name+' connected.')
        
    #write out to raw log file
    try:
        context['rawlog'].write(timeutil.now_to_local_string()+' | '+context['client_address']+' | '+raw_message+'\n')
    except:
        print('error. NMEA message not logged.')

    return raw_message

@nmeaserver.posthandler()
def onEveryMessageAfterHandler(context, message, response):
    team = context['team']
    
    html_path = WEB_PATH+team.name+'/index.html'
    if not os.path.exists(os.path.dirname(html_path)):
        try:
            os.makedirs(os.path.dirname(html_path))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise
                
    print('***** message: ' + message['sentence'])
    html_log = open(html_path,'w')
    html_log.write("{}Team {}<br /> Last heartbeat timestamp: {}<br /> Last \"Automated Docking\" reported: {}<br /> Last \"Raise The Flag\" reported: {}<br /> Last raw message: {}".format(HTML_HEADER, team.name, team.hbtime, team.dock, team.flag, message['sentence']))
    html_log.truncate()
    html_log.close()

    return response

@nmeaserver.message('RBHRB')
def heartbeat_handler(context, message):
    context['team'].HRB(message['data'], context['logfile'])
    return nmea.formatSentence("TDHRB,{},Success".format(datetime.now().strftime("%m%d%y,%H%M%S")))

@nmeaserver.message('RBDOK')
def automated_docking_handler(context, message):
    context['team'].DOK(message['data'], context['logfile'])
    return nmea.formatSentence("TDDOK,{},Success".format(datetime.now().strftime("%m%d%y,%H%M%S")))

@nmeaserver.message('RBFLG')
def raise_the_flag_handler(context, message):
    context['team'].FLG(message['data'], context['logfile'])
    return nmea.formatSentence("TDFLG,{},Success".format(datetime.now().strftime("%m%d%y,%H%M%S")))

@nmeaserver.bad_checksum()
def bad_checksum(context, raw_message):
    sentence = nmea.formatSentence(raw_message[:raw_message.find('*')])
    parsed = nmea.parseNMEA(sentence)
    valid_checksum = nmea.calcchecksum(sentence)
    return nmea.formatSentence("TDERR,{},{},Invalid Checksum. Valid one was: {}").format(datetime.now().strftime("%m%d%y,%H%M%S"), parsed['sentence_id'], valid_checksum)

@nmeaserver.unknown_message()
def unknown_message(context, message):
    print("Receiving unknown message::: {}".format(message))
    
    return nmea.formatSentence("TDERR,{},{},Invalid MessageID received. Valid ones are: RBFLG, RBDOK & RBHRB").format(datetime.now().strftime("%m%d%y,%H%M%S"), message['sentence_id'])

@nmeaserver.error()
def error(context):
    team = context['team']
    print('Team {} disconnected.'.format(team.name))
    context['logfile'].close()
    context['rawlog'].close()
    html_path = WEB_PATH+team.name+'/index.html'
    if not os.path.exists(os.path.dirname(html_path)):
        try:
            os.makedirs(os.path.dirname(html_path))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise
            
    html_log = open(html_path,'w')
    html_log.write(HTML_HEADER + 'Team ' + team.name + '<br /> NOT CONNECTED')
    html_log.truncate()
    html_log.close()
    raise

# Main method to run the RoboServer    
def main():
    # if today's folder hasn't been created, create it
    try:
        log_dir = LOGS_PATH+str(date.today())
        if os.path.isdir(log_dir) == False:
            os.makedirs(log_dir)
            print("created: " + log_dir)
        else:
            print("directory: " +  log_dir)
    except:
        print("Oops! {} occurred.". format(sys.exc_info()[0]))
        #pass
    # start the threads to listen to the boats.
    # this breaks off another thread for each TCP connection.   
    nmeaserver.start()

    # start the threads to listen to the buoy and pingers.
    # this is the TCP listener. It runs as long as the program runs.
    PINGlisten_thread = threading.Thread(name='pinger', target = ping.PINGlistener)
    PINGlisten_thread.daemon = True
    PINGlisten_thread.start()

    BUOYlisten_thread = threading.Thread(name='buoy', target = buoy.BUOYlistener)
    BUOYlisten_thread.daemon = True
    BUOYlisten_thread.start()

if __name__ == '__main__':
    main()

    while True:
        try:
            time.sleep(0.2)
        except:
            nmeaserver.stop()
            print("Server going down")
            sys.exit(0)
            break
