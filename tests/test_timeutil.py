'''
Created on Jun 18, 2019

@author: felixpageau
'''
import pytz
from datetime import datetime

"""
    test_timeutil
    ~~~~~~~~~~~~~~~~~~~~~

    Test the timeutil module.

    :license: APLv2, see LICENSE for more details.
"""

from unittest import TestCase
from serv import timeutil
import re

class TestRun(TestCase):

    def test_init(self):
        self.assertEqual(timeutil.TimeUtil(None).local_tz, pytz.utc, "Verify that default TZ is UTC")
        self.assertEqual(timeutil.TimeUtil(pytz.timezone('US/Eastern')).local_tz, pytz.timezone('US/Eastern'), "Verify that setup with EST works")

    def test_rn_timestamp(self):
        pattern = re.compile('''[0-9]{4}-[0-9]{2}-[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2}.+''', re.X | re.IGNORECASE)

        timeu = timeutil.TimeUtil(pytz.timezone('US/Hawaii'))
        self.assertTrue(pattern.match(timeu.rn_timestamp()), timeu.rn_timestamp())

    def test_log_timestamp(self):
        timeu = timeutil.TimeUtil(None)
        self.assertEqual(timeu.log_timestamp("101218", "161229"), "12/10/18 16:12:29", "Test robotX timestamp")
        self.assertEqual(timeu.log_timestamp("180619", "102434"), "06/18/19 10:24:34", "Test roboboat timestamp")

