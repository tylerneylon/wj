#!/usr/bin/python

import calendar
import datetime
import random
import sys
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

def outputStringForTimeMark(timeMark):
  wj._setMessage(randomString(), timeMark)

# Confirm the user wants to do this.
print "This will overwrite data in ~/.wj.  Are you sure?"
confirmStr = raw_input("Type 'Yes' to continue ")
if confirmStr != "Yes":
  sys.exit(0)

# Get a timestamp for Jan 1 of this year.
now = time.localtime()
year = now.tm_year
date = datetime.date(year, 1, 1)
startStamp = calendar.timegm(date.timetuple())
startStamp += time.timezone

# Set a message for every timemark in the year.
outputStringForTimeMark(str(year))
ts = startStamp
oneDay = 60 * 60 * 24
while time.localtime(ts).tm_year == year:
  dayMark = wj._7dateForTime(ts)
  outputStringForTimeMark(dayMark)
  weekMark = wj._fromDayToScope(dayMark, "w")
  outputStringForTimeMark(weekMark)
  monthMark = wj._fromDayToScope(dayMark, "m")
  outputStringForTimeMark(monthMark)
  ts += oneDay

