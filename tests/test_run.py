# -*- coding: utf-8 -*-
"""
	tests_run
	~~~~~~~~~~~~~~~~~~~~~

	The basic run.

	:license: APLv2, see LICENSE for more details.
"""

from unittest import TestCase
from serv import nmea
import socket
import sys
import threading

import server

PORT = 9000
SERV = None

class TestRun(TestCase):
	@classmethod
	def setUpClass(cls):
		TestCase.setUpClass()
		#Start an actual server
		cls.SERV = threading.Thread(target=server.main, args=())
		cls.SERV.setDaemon(True)
		cls.SERV.start()

	def test_run(self):		
		#Make calls to it
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		server_address = ('localhost', PORT)
		print >>sys.stderr, 'connecting to %s port %s' % server_address
		sock.connect(server_address)
		try:
			# Send heartbeat
			message = nmea.formatSentence('RBHRB,101218,161229,21.31198,N,157.88972,W,AUVSI,2')
			print >>sys.stderr, 'sending "%s"' % message
			sock.sendall(message)
			
			# Send docking
			message = nmea.formatSentence('RBDOK,101218,161229,AUVSI,2')
			print >>sys.stderr, 'sending "%s"' % message
			sock.sendall(message)
			
			# Send flag
			message = nmea.formatSentence('RBFLG,101218,161229,AUVSI,3')
			print >>sys.stderr, 'sending "%s"' % message
			sock.sendall(message)
			
			# Send heartbeat
			message = nmea.formatSentence('RBHRB,101218,161229,21.31198,N,157.88972,W,AUVSI,2')
			print >>sys.stderr, 'sending "%s"' % message
			sock.sendall(message)
		finally:
			print >>sys.stderr, 'closing socket'
			sock.close()
		self.assertTrue(True)
		
	def test_bad_sentence(self):		
		#Make calls to it
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		server_address = ('localhost', PORT)
		print >>sys.stderr, 'connecting to %s port %s' % server_address
		sock.connect(server_address)
		try:
			# Send heartbeat
			message = nmea.formatSentence('RBHRB,101218,161229,21.31198,N,157.88972,W,AUVSI,2')
			print >>sys.stderr, 'sending "%s"' % message
			sock.sendall(message)
			
			# Send invalid message
			message = nmea.formatSentence('RBWOW,101218')
			print >>sys.stderr, 'sending "%s"' % message
			sock.sendall(message)
		finally:
			print >>sys.stderr, 'closing socket'
			sock.close()
		self.assertTrue(True)

	@classmethod	
	def tearDownClass(cls):
		TestCase.tearDownClass()
		cls.SERV.join()