#!/usr/bin/env python

import os
import time
import pytz
import errno
import sys
import signal
import logging
from flask import Flask, render_template, send_from_directory
from nmeaserver import server, formatter
from serv import timeutil, pinger, buoy, sevenseg
from datetime import date

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(name)s - %(message)s')
logger = logging.getLogger("roboserver")

# LOGS_PATH may need to change depending on where you are running this
# file from
LOGS_PATH = 'logs/'
WEB_PATH = 'wwwroot/'
COMPETITION = "RoboBoat 2019"
HTML_HEADER = '<head><title>' + COMPETITION + '</title>' + \
                '<meta http-equiv="refresh" content="5" ></head>'

timeutil = timeutil.TimeUtil(pytz.timezone('US/Eastern'))
ping = pinger.Pinger('192.168.1.6', 4000, LOGS_PATH, timeutil, 'pinger')
sevenseg = sevenseg.SevenSeg('192.168.1.7', 9000, LOGS_PATH, timeutil, 'sevenseg')
#buoy = buoy.Buoy('192.168.1.11', 4000, LOGS_PATH, timeutil, 'buoy')
nmeaserver = server.NMEAServer('', 9000)
app = Flask(__name__, static_folder=WEB_PATH, template_folder=WEB_PATH)
shutdown_flag = False

# The following object holds all information for a team's run


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

    # Heartbeat message parsing and story log
    def HRB(self, message, logfile):
        self.hbdate = message[0]
        self.hbtime = message[1]
        self.lat = message[2]
        self.NS = message[3]
        self.lon = message[4]
        self.EW = message[5]
        self.name = message[6]
        # write out to story log on mode change
        if self.mode != message[7]:
            if message[7] == '2':
                # write out to story log
                logger.info(self.name + ' vehicle in Auto')

                log = 'vehicle is autonomous. Run started.\n'
                if ping.Connected:
                    log += 'Field {} pinger {} active.\n'.format(
                        ping.Field, ping.Active)
                else:
                    log += 'Pinger not connected.'
                if sevenseg.Connected:
                    log += 'Field {} SevenSeg at {}.\n'.format(
                        sevenseg.Field, sevenseg.State)
                else:
                    log += 'Light buoy not connected.'

                self.print_log(log, logfile)
            elif message[7] == '1':
                logger.info(self.name + 'vehicle is in manual mode. run ended.\n\n')
                self.print_log(
                    'vehicle is in manual mode. run ended.\n', logfile)
        self.mode = message[7]

    # Raise The Flag message parsing and story log
    def FLG(self, message, logfile):
        self.date = message[0]
        self.time = message[1]
        self.name = message[2]
        self.flag = message[3]
        self.print_log(
            'reports Raise The Flag number: ' +
            self.flag +
            '.\n',
            logfile)

    # Docking message parsing and story log
    def DOK(self, message, logfile):
        self.date = message[0]
        self.time = message[1]
        self.name = message[2]
        self.dock = message[3]
        self.print_log(
            'reports Automated Docking in: ' +
            self.dock +
            '.\n',
            logfile)

    # Write out to story log
    def print_log(self, message, logfile):
        try:
            logfile.write(timeutil.rn_timestamp() +
                          '\n' + self.name + ' ' + message)
        except BaseException:
            logger.error('no story log file created.')


@nmeaserver.context_creator()
def onConnectionEstablished(context):
    logger.info("Connection established")
    context['team'] = Team()
    return context


@nmeaserver.prehandler()
def onEveryMessageBeforeHandler(context, raw_message):
    team = context['team']

    if team.name is None:
        message = formatter.parse(raw_message, False)
        
        if message['sentence'] == 'RBHRB':
            team.name = message['data'][6]
        elif message['sentence'] == 'RBDOK' or message['sentence'] == 'RBFLG':
            team.name = message['data'][2]
        else:
            return raw_message
            
        log_folder = LOGS_PATH + str(date.today()) + '/' + team.name
        context['logfile'] = open(log_folder + '_STORY.txt', 'a')
        context['rawlog'] = open(log_folder + '_RAW.txt', 'a')
        logger.info('Team ' + team.name + ' connected.')

    # write out to raw log file
    try:
        context['rawlog'].write(
            timeutil.rn_timestamp() +
            ' | ' +
            context['client_address'] +
            ' | ' +
            raw_message +
            '\n')
    except BaseException:
        logger.warn('error. NMEA message not logged.')

    return raw_message


@nmeaserver.posthandler()
def onEveryMessageAfterHandler(context, message, response):
    team = context['team']

    html_path = WEB_PATH + team.name + '/index.html'
    if not os.path.exists(os.path.dirname(html_path)):
        try:
            os.makedirs(os.path.dirname(html_path))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    html_log = open(html_path, 'w')
    html_log.write(
        "{}Team {}<br /> Last heartbeat timestamp: {}<br /> Last \"Automated" + \
        " Docking\" reported: {}<br /> Last \"Raise The Flag\" reported: {}" + \
        "<br /> Last raw message: {}".format(
            HTML_HEADER,
            team.name,
            team.hbtime,
            team.dock,
            team.flag,
            message['sentence']))
    html_log.truncate()
    html_log.close()

    return response


@nmeaserver.message('RBHRB')
def heartbeat_handler(context, message):
    context['team'].HRB(message['data'], context['logfile'])
    return formatter.format("TDHRB,{},Success".format(timeutil.rn_timestamp()))


@nmeaserver.message('RBDOK')
def automated_docking_handler(context, message):
    context['team'].DOK(message['data'], context['logfile'])
    return formatter.format("TDDOK,{},Success".format(timeutil.rn_timestamp()))


@nmeaserver.message('RBFLG')
def raise_the_flag_handler(context, message):
    context['team'].FLG(message['data'], context['logfile'])
    return formatter.format("TDFLG,{},Success".format(timeutil.rn_timestamp()))


@nmeaserver.bad_checksum()
def bad_checksum(context, raw_message):
    sentence = formatter.format(raw_message[:raw_message.find('*')])
    parsed = formatter.parse(sentence)
    valid_checksum = formatter.calc_checksum(sentence)
    return formatter.format("TDERR,{},{},Invalid Checksum. Valid one was: {}").format(
        timeutil.nmea_timestamp(), parsed['sentence_id'], valid_checksum)


@nmeaserver.unknown_message()
def unknown_message(context, message):
    logger.info("Receiving unknown message::: {}".format(message))

    return formatter.format("TDERR,{},{},Invalid MessageID received. Valid" \
                            " ones are: RBFLG, RBDOK & RBHRB").format( \
                            timeutil.nmea_timestamp(), message['sentence_id'])

@nmeaserver.error()
def error(context, err):
    team = context['team']
    logger.info('Team {} disconnected.'.format(team.name))
    context['logfile'].close()
    context['rawlog'].close()
    html_path = WEB_PATH + team.name + '/index.html'
    if not os.path.exists(os.path.dirname(html_path)):
        try:
            os.makedirs(os.path.dirname(html_path))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    html_log = open(html_path, 'w')
    html_log.write(HTML_HEADER + 'Team ' + team.name + '<br /> NOT CONNECTED')
    html_log.truncate()
    html_log.close()
    raise

@app.route('/', strict_slashes=False)
@app.route('/index.html')  
def teams():
    dirs = next(os.walk(WEB_PATH))[1]
    return render_template('index.html', name="", dirs=dirs, competition=COMPETITION)
    #return send_from_directory(WEB_PATH, 'index.html')

@app.route('/team/<teamname>/', strict_slashes=False)  
def team(teamname):
    return send_from_directory(WEB_PATH, teamname+'/index.html')

# Main method to run the RoboServer
def main():
    # if today's folder hasn't been created, create it
    try:
        log_dir = LOGS_PATH + str(date.today())
        if os.path.isdir(log_dir) == False:
            os.makedirs(log_dir)
            logger.info("created: " + log_dir)
        else:
            logger.info("directory: " + log_dir)
    except BaseException:
        logger.exception("Oops something bad happened:")

    nmeaserver.start() #starts the nmeaserver
    ping.start()
    sevenseg.start()
    app.run() #starts the webserver


def signal_handler(sig, frame):
        logger.info('You pressed Ctrl+C!')
        shutdown()
signal.signal(signal.SIGINT, signal_handler)

def shutdown():
    shutdown_flag = True
    logger.warn("Server going down")
    sevenseg.shutdown()
    ping.shutdown()
    nmeaserver.shutdown()
    sys.exit(0)

if __name__ == '__main__':
    main()

    while not shutdown_flag:
        try:
            time.sleep(0.2)
        except BaseException:
            pass
    shutdown()
