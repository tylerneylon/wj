#!/usr/bin/python

import calendar
import datetime
import random
import time
import wj

def randomString():
  words = ["apple", "oatmeal", "honey", "marshmallow",
           "cracker", "peanut", "garlic", "onion",
           "mango", "wine", "rice", "noodles", "cucumber",
           "pear", "sage", "beef", "chicken", "lychee",
           "lentil", "butter", "basil", "cheese",
           "mushroom", "ham", "mayo", "mustard",
           "pickle", "salmon"]
  return " ".join(random.sample(words, 5))


# Get a timestamp for Jan 1 of this year.
now = time.localtime()
year = now.tm_year
date = datetime.date(year, 1, 1)
startStamp = calendar.timegm(date.timetuple())
startStamp += time.timezone

ts = startStamp
oneDay = 60 * 60 * 24
while time.localtime(ts).tm_year == year:
  # do stuff
  timeMark = wj._7dateForTime(ts)
  print timeMark
  print randomString()
  ts += oneDay

