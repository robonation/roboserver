import os
import operator
import socket
import random
import re
import SocketServer
import sys
import threading
import time
import pytz
from datetime import datetime, date

local_tz = pytz.timezone('Pacific/Honolulu')

def utc_to_local(utc_dt):
    local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
    return local_tz.normalize(local_dt)

def aslocaltimestr(utc_dt):
    return utc_to_local(utc_dt).strftime('%Y-%m-%d %H:%M:%S.%f %Z%z')

#LOGS_PATH may need to change depending on where you are running this file from
LOGS_PATH = '../LOGS/'
BUOY_IP = '192.168.1.11'
BUOY_PORT = 4000
PING_IP = '192.168.1.6'
PING_PORT = 4000
WEB_PATH = '/var/www/html/'

HTML_HEADER = '<head><title>RobotX 2018</title><meta http-equiv="refresh" content="5" ></head>'

#global pinger object 'ping' holds pinger state
class Pinger():
	Field = 'None'
	Active = 0
	Sync = 'I'
	Voltage = 0
	Time = aslocaltimestr(datetime.utcnow())
	Connected = False

ping = Pinger()

#global buoy object 'buoy' holds light buoy state
class Buoy():
	Field = 'None'
	State = '0'
	Voltage = 0
	Time = aslocaltimestr(datetime.utcnow())
	Connected = False

buoy = Buoy()

# connect to pinger via TCP
def PINGlistener():
	while True:
		#try to connect to the pinger box
		while not ping.Connected:
			try:
				#create a new socket and try to connect
				sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				sock.connect((PING_IP,PING_PORT))
				print 'Pinger TCP connected'
				ping.Connected = True
			except:
				# if it doesn't work, try again in two seconds
				time.sleep(2)
		#once we are connected to the pingers:
		while ping.Connected:
			try:
				response = sock.recv(1024)
				#print response, 'received from', addr
				message = readNMEA(response)
				# update the field docs with buoy and pinger info.
				name = message['sentence_type']
				if name == 'PNS':
					ping.Field = message['data'][0]
					#print 'Field:', ping.Field
					ping.Active = message['data'][1]
					#print 'Active pinger:', ping.Active
					ping.Sync = message['data'][2]
					#print 'Pinger Sync Mode:', ping.Sync
					ping.Voltage = float(message['data'][3])/1000
					#print 'Pinger voltage:', ping.Voltage
					ping.Time = aslocaltimestr(datetime.utcnow())
					#print 'Time:', str(ping.Time)
					folder = 'Field_'+str(message['data'][0])

				else:
					name = 'PINGlog'
					folder = 'ERRORS'
				# store NMEA messages in log files.
				try:
					with open(LOGS_PATH+str(date.today())+'/'+folder+'/'+name+'.txt', 'a') as f:
						f.write(str(buoy.Time)+' | '+response)
				except:
					os.mkdir(LOGS_PATH+str(date.today())+'/'+folder)
					with open(LOGS_PATH+str(date.today())+'/'+folder+'/'+name+'.txt', 'a') as f:
						f.write(str(buoy.Time)+' | '+response)
			except:
				print 'Pinger TCP disconnected'
				sock.close()
				ping.Connected = False

def BUOYlistener():
	#THIS FUNCTION IS NEARLY IDENTICAL TO PINGlistener()
	while True:
		while not buoy.Connected:
			try:
				sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				sock.connect((BUOY_IP,BUOY_PORT))
				buoy.Connected = True
				print 'Buoy TCP connected.'
			except:
				time.sleep(2)
		while buoy.Connected:
			try:
				response = sock.recv(1024)
				message = readNMEA(response)
				name = message['sentence_type']
				if name == 'BYS':
					buoy.Field = message['data'][0]
					#print 'Field:', buoy.Field
					buoy.State = message['data'][1]
					#print 'Buoy state:', buoy.State
					buoy.Voltage = float(message['data'][2])/1000
					#print 'Buoy voltage:', buoy.Voltage
					buoy.Time = aslocaltimestr(datetime.utcnow())
					folder = 'Field_'+str(message['data'][0])
				else:
					name = 'BUOYlog'
					folder = 'ERRORS'
				try:
					with open(LOGS_PATH+str(date.today())+'/'+folder+'/'+name+'.txt', 'a') as f:
						f.write(str(buoy.Time)+' | '+response)
				except:
					os.mkdir(LOGS_PATH+str(date.today())+'/'+folder)
					with open(LOGS_PATH+str(date.today())+'/'+folder+'/'+name+'.txt', 'a') as f:
						f.write(str(buoy.Time)+' | '+response)
			except:
				print 'Buoy TCP disconnected'
				sock.close()
				buoy.Connected = False

def calcchecksum(nmea_str):
	# this returns a 2 digit hexadecimal string to use as a checksum.
	sum = hex(reduce(operator.xor, map(ord, nmea_str), 0))[2:].upper()
	if len(sum) == 2:
		return sum
	else:
		return '0' + sum

def readNMEA(nmea_str):
	# parse NMEA string into dict of fields.
	# the data will be split by commas and accessible by index.
	NMEApattern = re.compile('''
		^[^$]*\$?
		(?P<nmea_str>
			(?P<talker>\w{2})
			(?P<sentence_type>\w{3}),
			(?P<data>[^*]+)
		)(?:\\*(?P<checksum>[A-F0-9]{2}))
		[\\\r\\\n]*
		''', re.X | re.IGNORECASE)
	match = NMEApattern.match(nmea_str)
	if not match:
		raise ValueError('Could not parse data:', nmea_str)
	nmea_dict = {}
	nmea_str = match.group('nmea_str')
	nmea_dict['talker'] = match.group('talker').upper()
	nmea_dict['sentence_type'] = match.group('sentence_type').upper()
	nmea_dict['data'] = match.group('data').split(',')
	checksum = match.group('checksum')
	# check the checksum to ensure matching data.
	if checksum != calcchecksum(nmea_str):
		raise ValueError('Checksum does not match: %s != %s.' %
			(checksum, calcchecksum(nmea_str)))
	return nmea_dict

#The following object holds all information for a team's run
class Team():
	name = ''
	date = 0
	hbdate = 0
	time = 0
	hbtime = 0
	lat = 0.0
	NS = 'N'
	lon = 0.0
	EW = 'E'
	mode = '1'
	status = '1'
	entrance = '0'
	exit = '0'
	LBactive = 'N'
	LBpattern = ''
	CODpattern = ''
	DOKcolor = ''
	DOKshape = ''
	DELcolor = ''
	DELshape = ''
	#Heartbeat message parsing and story log
	def HRB(self, message, file):
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
				try:
					print self.name + 'Vehicle in Auto\n'
					file.write(str(aslocaltimestr(datetime.utcnow()))+'\n'+self.name+' vehicle is autonomous. Run started.\n')
					if ping.Connected:
						file.write('Field '+ping.Field+' pinger '+ping.Active+' active.\n')
					else:
						file.write('Pinger not connected.')
					if buoy.Connected:
						file.write('Field '+buoy.Field+' Light buoy at '+buoy.State+'.\n')
					else:
						file.write('Light buoy not connected.')
				except:
					print 'no story log file created.'
			elif message[7] == '1':
				print self.name + 'vehicle is in manual mode. run ended.\n'
				try:
					file.write(str(aslocaltimestr(datetime.utcnow()))+'\n'+self.name+' vehicle is in manual mode. run ended.\n')
				except:
					print 'no story log file created.'
		self.mode = message[7]
		self.status = message[8]
		
		

	#Gate message parsing and story log
	def GAT(self, message, file):
		self.date = message[0]
		self.time = message[1]
		self.name = message[2]
		self.entrance = message[3]
		self.exit = message[4]
		self.LBactive = message[5]
		self.LBpattern = message[6]
		#write out to story log
		try:
			file.write(str(aslocaltimestr(datetime.utcnow()))+'\n'+self.name+' reports\n')
			file.write('Active entrance gate: '+self.entrance+'\n')
			file.write('Active exit gate: '+self.exit+'\n')
			file.write('Light buoy active: '+self.LBactive+'\n')
			if self.LBactive == 'Y':
				file.write('Light buoy pattern: '+self.LBpattern)
		except:
			print 'no story log file created.'

	#Scan the code message parsing and story log
	def COD(self, message, file):
		self.date = message[0]
		self.time = message[1]
		self.name = message[2]
		self.CODpattern = message[3]
		try:
			file.write(str(aslocaltimestr(datetime.utcnow()))+'\n'+self.name+' reports ')
			file.write('Scan the code pattern '+self.CODpattern+'.\n')
		except:
			print 'no story log file created.'
	#Docking message parsing and story log
	def DOK(self, message, file):
		self.date = message[0]
		self.time = message[1]
		self.name = message[2]
		self.DOKcolor = message[3]
		self.DOKshape = message[4]
		#convert color to readable text
		if self.DOKcolor == 'R':
			color = 'Red'
		elif self.DOKcolor == 'B':
			color = 'Blue'
		elif self.DOKcolor == 'G':
			color = 'Green'
		else:
			color = '<invalid/no color reported>'
		#convert shape to readable text
		if self.DOKshape == 'CRUCI':
			shape = 'crucible'
		elif self.DOKshape == 'TRIAN':
			shape = 'triangle'
		elif self.DOKshape == 'CIRCL':
			shape = 'circle'
		else:
			shape = '<invalid/no shape reported>'
		#write out to story log
		try:
			file.write(str(aslocaltimestr(datetime.utcnow()))+'\n'+self.name+' reports ')
			file.write(color+' '+shape+' for docking challenge.\n')
		except:
			print 'no story log file created.'

	#Detect and deliver message parsing and story log
	def DEL(self, message, file):
		self.date = message[0]
		self.time = message[1]
		self.name = message[2]
		self.DELcolor = message[3]
		self.DELshape = message[4]
		#convert color to readable text
		if self.DELcolor == 'R':
			color = 'Red'
		elif self.DELcolor == 'B':
			color = 'Blue'
		elif self.DELcolor == 'G':
			color = 'Green'
		else:
			color = '<invalid/no color reported>'
		#convert shape to readable text
		if self.DELshape == 'CRUCI':
			shape = 'crucible'
		elif self.DELshape == 'TRIAN':
			shape = 'triangle'
		elif self.DELshape == 'CIRCL':
			shape = 'circle'
		else:
			shape = '<invalid/no shape reported>'
		#write out to story log
		try:
			file.write(str(aslocaltimestr(datetime.utcnow()))+'\n'+self.name+' reports ')
			file.write(color+' '+shape+' for detect and deliver challenge.\n')
		except:
			print 'no story log file created.'

class MyTCPHandler(SocketServer.StreamRequestHandler):
	# read TCP message. Pass it through parser.
	def handle(self):
		#create an object for the team. This object can be used by GUI
		team = Team()
		#read in the first message to get team name
		self.data = self.rfile.readline().strip()
		message = readNMEA(self.data)
		getattr(team, message['sentence_type'])(message['data'], 0)
		print 'Team '+team.name+' connected.'
		#create human readable 'story log' and raw log for team.
		STORY_LOG = open(LOGS_PATH+str(date.today())+'/'+team.name+'_STORY.txt','a')
		RAW_LOG = open(LOGS_PATH+str(date.today())+'/'+team.name+'_RAW.txt','a')  
		while True:
			# this pulls off one line of data from the TCP message,
			# which should be the entire message.
			try:
				self.data = self.rfile.readline().strip()
				message = readNMEA(self.data)
			except:
				print 'Team '+team.name+' disconnected.'
				STORY_LOG.close()
				RAW_LOG.close()
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
				break

			if message['talker'] == 'RX':
				try:
					#calls parsing function within 'team' object by sentence type
					getattr(team, message['sentence_type'])(message['data'], STORY_LOG)
					name = team.name
				except:
					name = 'errors'
				#write out to raw log file
				try:
					RAW_LOG.write(str(aslocaltimestr(datetime.utcnow()))+' | '+self.client_address[0]+' | '+self.data+'\n')
				except:
					print 'error. NMEA message not logged.'
				html_path = WEB_PATH+team.name+'/index.html'
				if not os.path.exists(os.path.dirname(html_path)):
					try:
						os.makedirs(os.path.dirname(html_path))
					except OSError as exc: # Guard against race condition
						if exc.errno != errno.EEXIST:
							raise
							
				html_log = open(html_path,'w')
				html_log.write(HTML_HEADER + 'Team ' + team.name + '<br /> Last heartbeat timestamp:' + team.hbtime + '<br /> Last "Scan the Code" reported: ' + team.CODpattern + '<br /> Last "Gates" reported, Entrance:  ' + team.entrance + ' Exit: ' + team.exit + ' Code: ' + team.LBpattern + '<br /> Last raw message: ' + self.data)
				html_log.truncate()
				html_log.close()
			else:
				raise ValueError('Invalid talker, got', message['talker'])
			


class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer): pass

if __name__ == '__main__':
	# if today's folder hasn't been created, create it
	try:
		os.mkdir(LOGS_PATH+str(date.today()))
	except:
		pass
	# start the threads to listen to the boats.
	# this breaks off another thread for each TCP connection.
	HOST, PORT = '', 9000
	server = ThreadedTCPServer((HOST, PORT), MyTCPHandler)
	server_thread = threading.Thread(target = server.serve_forever)
	server_thread.daemon = True
	server_thread.start()
	print 'Server Address:', socket.gethostbyname(socket.gethostname())
	print 'Connect to server on port:', PORT

	# start the threads to listen to the buoy and pingers.
	# this is the TCP listener. It runs as long as the program runs.
	PINGlisten_thread = threading.Thread(target = PINGlistener)
	PINGlisten_thread.daemon = True
	PINGlisten_thread.start()

	BUOYlisten_thread = threading.Thread(target = BUOYlistener)
	BUOYlisten_thread.daemon = True
	BUOYlisten_thread.start()

	while True:
		try:
			time.sleep(0.2)
		except:
			break

