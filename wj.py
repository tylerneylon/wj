#!/usr/bin/python

# TODO NEXT
# [x] List recent entries on interactive startup.
# [x] Add suggestions for recent missing entries.
# [ ] Add an 'a' command in interactive mode to input all recent missing entries.
# [ ] Make sure we can handle w,m,y actions.
# [ ] Allow the -r option to have an optional number of recent entries to show.

# TODO Eventually
# [ ] Provide output with -o option.
# [ ] Make sure everything works from the command line (non-interactive).
# [ ] Support configuration settings file in the .wj folder.
# [ ] Support Gregorian dates.

# imports
# =======

import calendar
import datetime
import fcntl
from optparse import OptionParser
import os
import pickle
import re
import sys
import termios
import time

# globals
# =======

_yearMessages = None
_yearLoaded = None
_verbose = True

# public functions
# ================

def handleArgs(args):
  parser = OptionParser()
  parser.add_option("-o", action="store", type="string",
                    dest="outfile",
                    help="generate a tex file with recent messages")
  parser.add_option("-t", dest="userTimeMark",
                    help="add a message for the specified time unit")
  parser.add_option("-r", dest="showRecent",
                    action="store_true",
                    help="show recent messages")
  # TODO add options
  (options, args) = parser.parse_args(args)
  if options.showRecent:
    showRecentMessages()
    exit()
  if len(args) > 1:
    msg = ' '.join(args[1:])
    addMessage(msg)
  else:
    runInteractive()

# A timeMark is a string representing a time period we know about.
# It can be in one of these formats:
# 123.2011  day
# 12-.2011  week
# 1--.2011  month
# 2011      year

def addMessage(msg, timeMark=None):
  print "addMessage(%s)" % msg
  print "what is the timeMark?"
  print _7dateForTime()
  if timeMark is None:
    print "requesting default timeMark"
    timeMark = currentDefaultTimeMark()
    print "default timeMark given as %s" % `timeMark`
  _setMessage(msg, timeMark)

def makeOutput(filename, timeMark=None):
  pass

def runInteractive():
  print "Work Journal (wj)"
  showRecentMessages()
  showRecentMissingTimeMarks()
  print "---------------------------------"
  print "Actions: [d]ay entry; [w]eek; [m]onth; [y]ear; [a]ll missing"
  print "         specify [t]ime; [o]utput; [h]elp; [q]uit."
  print "What would you like to do? [dwmyatohq]"
  actionChar = _getch()
  messageChars = ['d', 'w', 'm', 'y']
  if actionChar in messageChars:
    print "Today is %s" % _7dateForTime()
    timeMark = currentDefaultTimeMark(scope=actionChar)
    msg = raw_input("Enter message for %s: " % timeMark)
    addMessage(msg, timeMark)
  elif actionChar == 't':
    print "Today is %s" % _7dateForTime()
    _getUserTimeMarkAndMessage()
  elif actionChar == 'a':
    pass # TODO HERE
  elif actionChar == 'o':
    pass
  elif actionChar == 'h':
    pass
  elif actionChar == 'q':
    print "Goodbye"
  else:
    # TODO add error-handling for unhandled characters
    pass

# Open an editor to get the latest message.
def getMessage():
  pass

# Returns the string for the current
# time mark.  The scope is expected to
# be in the set [dwmy].
def currentDefaultTimeMark(scope="d"):
  hour = 60 * 60
  day = 24 * hour
  scopes = list('dwmy')
  timeDeltas = [12 * hour, 2.5 * day, 4 * day, 10 * day]
  if not scope in scopes:
    raise Exception("Expected one of [dmwy] input to currentDefaultTimeMark")
  timestamp = time.time() - timeDeltas[scopes.index(scope)]
  timeMark = _7dateForTime(timestamp)
  return _fromDayToScope(timeMark, scope)

def showRecentMessages():
  global _yearMessages
  # TODO show only the most recent ones
  # for now I'll just print out everything
  _loadYear()
  print "Recent messages:"
  timeMarks = sorted(_yearMessages, key=_timestampForMark)
  timeMarks = timeMarks[-8:] # Just keep the most recent 8.
  for timeMark in timeMarks:
    print "%10s %s" % (timeMark, _yearMessages[timeMark])
  #print "_yearMessages=\n", _yearMessages

def showRecentMissingTimeMarks():
  global _yearMessages
  _loadYear()
  allRecent = _recentTimeMarks(8)
  msgRecent = sorted(_yearMessages, key=_timestampForMark)[-8:]
  str = "Missing messages: "
  numMarks = 0
  for timeMark in allRecent:
    if timeMark not in msgRecent:
      if numMarks > 0: str += ", "
      str += "%s" % timeMark
      numMarks += 1
      if timeMark == _7dateForTime(time.time()):
        str += " (today)"
      elif timeMark == _7dateForTime(time.time() - 24 * 60 * 60):
        str += " (yesterday)"
  if numMarks > 0: print str

# private functions
# =================

def _getUserTimeMarkAndMessage():
  timestamp = None
  while timestamp is None:
    print "Formats: 123.2025 (day), 12-.2025 (week), 1--.2025 (month), 2025 (year)"
    timeMark = raw_input("Enter timemark: ")
    timestamp = _timestampForMark(timeMark)
    if timestamp is None:
      print "Couldn't parse that timemark."
  msg = raw_input("Enter message for %s: " % timeMark)
  addMessage(msg, timeMark)

def _fromDayToScope(timeMark, scope="d"):
  timeMarkChars = list(timeMark)
  dotIndex = timeMark.find('.')
  if scope == "d":
    pass
  elif scope == "w":
    timeMarkChars[dotIndex - 1] = '-'
  elif scope == "m":
    timeMarkChars[(dotIndex - 2):dotIndex] = list('--')
  elif scope == "y":
    timeMarkChars = timeMarkChars[(dotIndex + 1):]
  else:
    raise Exception("Expected one of [dmwy] input to _fromDayToScope")
  return ''.join(timeMarkChars)

def _timestampForMark(timeMark):
  tm = time.struct_time([2001, 1, 1, 0, 0, 0, 0, 1, 0])
  hour = 60 * 60
  if re.match(r"\d+$", timeMark):
    # year
    year = int(timeMark)
    date = datetime.date(year + 1, 1, 1)
    ts = calendar.timegm(date.timetuple())
    return ts - 9 * hour
  elif re.match(r"\d+\.\d+$", timeMark):
    # day
    ts = _timestampFor7date(timeMark)
    return ts + 12 * hour
  elif re.match(r"\d+-\.\d+$", timeMark):
    # week
    timeMark = timeMark.replace('-', '6')
    ts = _timestampFor7date(timeMark)
    return ts + 13 * hour
  elif re.match(r"\d+--\.\d+$", timeMark):
    # month
    timeMark = timeMark.replace('-', '6')
    ts = _timestampFor7date(timeMark)
    return ts + 14 * hour
  return None

# Returns a 7date string for the given timestamp,
# which is seconds-since-epoch (compatible with
# the output of time.time()).
def _7dateForTime(timestamp=None):
  if timestamp is None:
    timestamp = time.time()
  tm = time.localtime(timestamp)
  return "%s.%d" % (_baseNString(7, tm.tm_yday - 1), tm.tm_year)

# The inverse of _7dateForTime.
# Returns the timestamp for midnight at the start of the date,
# which is the first second within that date.
def _timestampFor7date(sevenDate):
  m = re.match(r"(\d+)\.(\d+)", sevenDate)
  date = datetime.date(int(m.group(2)), 1, 1)
  numDays = _intFromBaseNString(7, m.group(1))
  date += datetime.timedelta(days=numDays)
  return calendar.timegm(date.timetuple())

# Returns the base n string representation of i.
# This assumes i >= 0 and n > 1, both integers.
# Also assumes n <= 10 for now.
def _baseNString(n, i):
  if i == 0:
    return "0"
  reverseDigits = []
  while i > 0:
    reverseDigits.append(i % n)
    i /= n
  s = ""
  while len(reverseDigits):
    s += `reverseDigits.pop()`
  return s

# Complement to _baseNString.
def _intFromBaseNString(n, str):
  val = 0
  while len(str):
    val *= n
    val += (ord(str[0]) - ord('0'))
    str = str[1:]
  return val

def _yearFromTimeMark(timeMark):
  print "_yearFromTimeMark(%s)" % `timeMark`
  return timeMark.split(".")[-1]

def _setMessage(msg, timeMark):
  global _yearMessages
  global _yearLoaded
  global _verbose
  print "_setMessage(%s, %s)" % (`msg`, `timeMark`)
  year = _yearFromTimeMark(timeMark)
  if _yearLoaded != year:
    _loadYear(year)
  print "just after year loaded verification, _yearMessages=%s" % `_yearMessages`
  if _verbose and timeMark in _yearMessages:
    print "replaced"
    print "%s %s" % (timeMark, _yearMessages[timeMark])
    print "with"
  elif _verbose:
    print "set"
  _yearMessages[timeMark] = msg
  _saveMessages()
  print "%s %s" % (timeMark, msg)

def _loadYear(year=None):
  global _yearMessages
  global _yearLoaded
  # TODO also load previous year if needed
  if year is None: year = str(time.localtime().tm_year)
  filename = _fileForYear(year)
  _yearLoaded = year
  if not os.path.isfile(filename):
    _yearMessages = {}
  else:
    file = open(filename, 'r')
    _yearMessages = pickle.load(file)
    file.close()

def _saveMessages():
  global _yearMessages
  if not os.path.exists(_wjDir()):
    os.mkdir(_wjDir())
  file = open(_fileForYear(_yearLoaded), 'w+')
  pickle.dump(_yearMessages, file, pickle.HIGHEST_PROTOCOL)
  file.close()

# This returns a list of all possible recent time marks,
# regardless of whether or not the user has any messages for them.
def _recentTimeMarks(n):
  timestamp = time.time()
  oneDay = 24 * 60 * 60
  markSet = set([_7dateForTime(timestamp - i * oneDay) for i in range(n)])
  markSet |= set([_fromDayToScope(i, scope) for i in markSet for scope in ["w", "m", "y"]])
  marks = sorted(markSet, key=_timestampForMark)
  return [m for m in marks if _timestampForMark(m) < timestamp]

# We expect year as a string.
def _fileForYear(year):
  return _wjDir() + year

def _wjDir():
  homeDir = os.path.expanduser('~') + '/'
  return homeDir + ".wj/"

# utility functions
# =================

def _getch():
  fd = sys.stdin.fileno()

  oldterm = termios.tcgetattr(fd)
  newattr = termios.tcgetattr(fd)
  newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
  termios.tcsetattr(fd, termios.TCSANOW, newattr)

  oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
  fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)

  try:        
    while 1:            
      try:
        c = sys.stdin.read(1)
        break
      except IOError: pass
  finally:
    termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
    fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)
  return c

# Main
# ====

if __name__ ==  "__main__":
  handleArgs(sys.argv)
