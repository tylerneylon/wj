#!/usr/bin/python

from optparse import OptionParser
import os
import pickle
import sys
import time

# Globals
# =======

_yearMessages = None
_yearLoaded = None

# Public functions
# ================

def handleArgs(args):
  parser = OptionParser()
  parser.add_option("-o", action="store", type="string",
                    dest="outfile")
  # TODO add options
  (options, args) = parser.parse_args(args)
  print "args=", args
  if len(args) > 1:
    msg = ' '.join(args[1:])
  else:
    msg = getMessage()
  addMessage(msg)

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
  pass

# Open an editor to get the latest message.
def getMessage():
  pass

# Returns the string for the current
# time mark.  The scope is expected to
# be in the set {day, week, month, year}.
def currentDefaultTimeMark(scope="day"):
  return _7dateForTime()

# Private functions
# =================

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

def _setMessage(msg, timeMark, verbose=True):
  global _yearMessages
  global _yearLoaded
  print "_setMessage(%s, %s, %s)" % (`msg`, `timeMark`, `verbose`)
  year = _yearFromTimeMark(timeMark)
  if _yearLoaded != year:
    _loadYear(year)
  print "just after year loaded verification, _yearMessages=%s" % `_yearMessages`
  if verbose and timeMark in _yearMessages:
    print "replaced"
    print "%s %s" % (timeMark, _yearMessages[timeMark])
    print "with"
  elif verbose:
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

# Main
# ====

if __name__ ==  "__main__":
  handleArgs(sys.argv)
