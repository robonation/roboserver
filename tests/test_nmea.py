# -*- coding: utf-8 -*-
"""
    tests.nmea
    ~~~~~~~~~~~~~~~~~~~~~

    Test the nmea module.

    :license: APLv2, see LICENSE for more details.
"""

import unittest

from serv import nmea

class TestStringMethods(unittest.TestCase):
    def test_calcchecksum_singledigit(self):
        self.assertEqual(nmea.calcchecksum("RBHRB,101218,161229,21.31198,N,157.88972,W,AUVSI,2"), '01')

    def test_calcchecksum_hex_character(self):
        self.assertEqual(nmea.calcchecksum("$RBDOK,101218,161229,AUVSI,2*3E"), '3E')

    def test_calcchecksum_prefix(self):
        self.assertEqual(nmea.calcchecksum("$RBHRB,101218,161229,21.31198,N,157.88972,W,AUVSI,2"), '01')

    def test_calcchecksum_already_has_checksum(self):
        self.assertEqual(nmea.calcchecksum("$RBHRB,101218,161229,21.31198,N,157.88972,W,AUVSI,2*01"), '01')

    def test_formatSentence_missing_prefix(self):
        self.assertEqual(nmea.formatSentence("RBHRB,101218,161229,21.31198,N,157.88972,W,AUVSI,2*01"), '$RBHRB,101218,161229,21.31198,N,157.88972,W,AUVSI,2*01')

    def test_formatSentence_missing_checksum(self):
        self.assertEqual(nmea.formatSentence("$RBHRB,101218,161229,21.31198,N,157.88972,W,AUVSI,2"), '$RBHRB,101218,161229,21.31198,N,157.88972,W,AUVSI,2*01')

    def test_formatSentence_missing_prefix_and_checksum(self):
        self.assertEqual(nmea.formatSentence("RBHRB,101218,161229,21.31198,N,157.88972,W,AUVSI,2"), '$RBHRB,101218,161229,21.31198,N,157.88972,W,AUVSI,2*01')

    def test_formatSentence_missing_nothing(self):
        self.assertEqual(nmea.formatSentence("$RBHRB,101218,161229,21.31198,N,157.88972,W,AUVSI,2*01"), '$RBHRB,101218,161229,21.31198,N,157.88972,W,AUVSI,2*01')

    def test_parseNMEA(self):
        nmea_str = '$RBHRB,101218,161229,21.31198,N,157.88972,W,AUVSI,2*01'
        self.assertEqual(nmea.parseNMEA(nmea_str)['talker'], 'RB')
        self.assertEqual(nmea.parseNMEA(nmea_str)['sentence_type'], 'HRB')
        self.assertEqual(nmea.parseNMEA(nmea_str)['data'][0], '101218')
        self.assertEqual(nmea.parseNMEA(nmea_str)['data'][1], '161229')
        self.assertEqual(nmea.parseNMEA(nmea_str)['data'][2], '21.31198')
        self.assertEqual(nmea.parseNMEA(nmea_str)['data'][3], 'N')
        self.assertEqual(nmea.parseNMEA(nmea_str)['data'][4], '157.88972')
        self.assertEqual(nmea.parseNMEA(nmea_str)['data'][5], 'W')
        self.assertEqual(nmea.parseNMEA(nmea_str)['data'][6], 'AUVSI')
        self.assertEqual(nmea.parseNMEA(nmea_str)['data'][7], '2')
    
    def test_parseNMEA_noChecksum(self):
        nmea_str = '$RBHRB,101218,161229,21.31198,N,157.88972,W,AUVSI,2'
        self.assertEqual(nmea.parseNMEA(nmea_str, False)['talker'], 'RB')
        self.assertEqual(nmea.parseNMEA(nmea_str, False)['sentence_type'], 'HRB')
        self.assertEqual(nmea.parseNMEA(nmea_str, False)['data'][0], '101218')
        self.assertEqual(nmea.parseNMEA(nmea_str, False)['data'][1], '161229')
        self.assertEqual(nmea.parseNMEA(nmea_str, False)['data'][2], '21.31198')
        self.assertEqual(nmea.parseNMEA(nmea_str, False)['data'][3], 'N')
        self.assertEqual(nmea.parseNMEA(nmea_str, False)['data'][4], '157.88972')
        self.assertEqual(nmea.parseNMEA(nmea_str, False)['data'][5], 'W')
        self.assertEqual(nmea.parseNMEA(nmea_str, False)['data'][6], 'AUVSI')
        self.assertEqual(nmea.parseNMEA(nmea_str, False)['data'][7], '2')
        
    def test_parseNMEA_noChecksum_strict(self):
        nmea_str = '$RBHRB,101218,161229,21.31198,N,157.88972,W,AUVSI,2'
        with self.assertRaises(ValueError):
            nmea.parseNMEA(nmea_str, True)

    def test_parseNMEA_one_data(self):
        nmea_str = '$RBHRB,Test*52'
        self.assertEqual(nmea.parseNMEA(nmea_str)['talker'], 'RB')
        self.assertEqual(nmea.parseNMEA(nmea_str)['sentence_type'], 'HRB')
        self.assertEqual(nmea.parseNMEA(nmea_str)['data'][0], 'Test')
    
    def test_parseNMEA_bad_checksum(self):
        nmea_str = '$RBHRB,Test*28'
        with self.assertRaises(ValueError):
            nmea.parseNMEA(nmea_str)


if __name__ == '__main__':
    unittest.main()