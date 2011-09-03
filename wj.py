#!/usr/bin/python

# imports
# =======

import fcntl
from optparse import OptionParser
import os
import pickle
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
  print "args=", args
  if options.showRecent:
    print "showing recent messages"
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
  print "Actions: [d]ay entry; [w]eek; [m]onth; [y]ear; [o]utput; [h]elp."
  print "What would you like to do? [dwmyoh]"
  actionChar = _getch()
  messageChars = ['d', 'w', 'm', 'y']
  if actionChar in messageChars:
    timeMark = currentDefaultTimeMark(scope=actionChar)
    msg = raw_input("Enter message for %s: " % timeMark)
    addMessage(msg, timeMark)
  elif actionChar == 'o':
    pass
  elif actionChar == 'h':
    pass
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
  tm = time.localtime()
  # TODO also load previous year if needed
  _loadYear(`tm.tm_year`)
  print "_yearMessages=\n", _yearMessages

# private functions
# =================

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

def _timeForMark(timeMark):
  pass

# Returns a 7date string for the given timestamp,
# which is seconds-since-epoch (compatible with
# the output of time.time()).
def _7dateForTime(timestamp=None):
  if timestamp is None:
    timestamp = time.time()
  tm = time.localtime(timestamp)
  return "%s.%d" % (_baseNString(7, tm.tm_yday - 1), tm.tm_year)

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

def _loadYear(year):
  global _yearMessages
  global _yearLoaded
  print "_loadYear(%s)" % `year`
  filename = _fileForYear(year)
  _yearLoaded = year
  if not os.path.isfile(filename):
    print "setting to empty dict"
    _yearMessages = {}
  else:
    print "attempting to load from file"
    file = open(filename, 'r')
    _yearMessages = pickle.load(file)
    file.close()
  print "at end of _loadYear,_yearMessages=%s" % `_yearMessages`

def _saveMessages():
  global _yearMessages
  if not os.path.exists(_wjDir()):
    os.mkdir(_wjDir())
  file = open(_fileForYear(_yearLoaded), 'w+')
  pickle.dump(_yearMessages, file, pickle.HIGHEST_PROTOCOL)
  file.close()

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
