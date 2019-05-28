import operator
import re

def calcchecksum(nmea_str):
	#Strip '$' and everything after the '*'
	if nmea_str.startswith('$'):
		nmea_str = nmea_str[1:]
	if nmea_str.find('*') >= 0:
		nmea_str = nmea_str[:nmea_str.find('*')]

	# this returns a 2 digit hexadecimal string to use as a checksum.
	sum = hex(reduce(operator.xor, map(ord, nmea_str), 0))[2:].upper()
	if len(sum) == 2:
		return sum
	else:
		return '0' + sum

def formatSentence(sentence):
	if sentence.find('*') < 0:
		sentence = sentence + '*' + calcchecksum(sentence)
	if sentence.startswith('$') == False:
		sentence = '$' + sentence
	return sentence

def parseNMEA(nmea_str):
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
	nmea_dict['sentence_id'] = match.group('talker').upper() + match.group('sentence_type').upper()
	nmea_dict['talker'] = match.group('talker').upper()
	nmea_dict['sentence_type'] = match.group('sentence_type').upper()
	nmea_dict['data'] = match.group('data').split(',')
	checksum = match.group('checksum')
	# check the checksum to ensure matching data.
	if checksum != calcchecksum(nmea_str):
		raise ValueError('Checksum does not match: %s != %s.' %
			(checksum, calcchecksum(nmea_str)))
	return nmea_dict