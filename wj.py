#!/usr/bin/python

# Next todo items
# [x] List recent entries on interactive startup.
# [x] Add suggestions for recent missing entries.
# [x] Add an 'a' command in interactive mode to input all recent missing entries.
# [x] Make sure we can handle w,m,y actions.
# [x] Add a command-line way to view more than just -r entries. (-l added)

# Todo eventually
# [x] Provide output with -o option.
# [ ] Make sure everything works from the command line (non-interactive).
# [x] Support configuration settings file in the .wj folder.
# [x] Support Gregorian dates.
# [ ] In interactive mode, accept numbers 1,2,.. at the menu for missing marks.
# [ ] Be careful about not showing today's mark before noon.  I thought I saw this happen today.
# [ ] Exit more gracefully on ctrl-c.
# [ ] Simplify the week/month user string if month or year are the same.
# [ ] Handle cross-year-boundary weeks.  Its timestamp should be at the end of the beginning year,
#     which is an exception.

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
_verbose = False

# These are overridden by .wj/config's value, if it exists.
_userTimeMode = 'Greg'
_userDateFormat = '%d %b %Y'
_userMonFormat = '%b %Y'

# public functions
# ================

# TODO Standardize what's public and what's not.
#      The deciding factor is that anything they can
#      do from the command line they should be able to
#      very easily do in code as well; stuff that's not
#      easy from the command line should be privite.

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
  parser.add_option("-l", dest="listAll",
                    action="store_true",
                    help="show all messages")
  # TODO add options
  (options, args) = parser.parse_args(args)
  if options.listAll:
    showMessages()  # TODO make this an option in interactive mode
    return
  if options.showRecent:
    showMessages(8)
    return
  if options.outfile:
    texString = texStringForYear()
    f = open(options.outfile, 'w')
    f.write(texString)
    f.close()
    return
  if len(args) > 1:
    msg = ' '.join(args[1:])
    addMessage(msg)
  else:
    runInteractive()

# TODO Move this comment somewhere more useful.
# A timeMark is a string representing a time period we know about.
# It can be in one of these formats:
# 123.2011  day
# 12-.2011  week
# 1--.2011  month
# 2011      year
# To be able to store Gregorian-based day ranges:
# (day) - (day)  Gregorian week or month

def addMessage(msg, timeMark=None):
  if timeMark is None:
    timeMark = currentDefaultTimeMark()
  _setMessage(msg, timeMark)

def runInteractive():
  print "Work Journal (wj)"
  print "Recent messages:"
  showMessages(8)
  showRecentMissingUserTimeStrs()
  print "---------------------------------"
  print "Actions: [d]ay entry; [w]eek; [m]onth; [y]ear; [a]ll missing"
  print "         specify [t]ime; [o]utput; [h]elp; [q]uit."
  print "What would you like to do? [dwmyatohq]"
  actionChar = _getch()
  messageChars = ['d', 'w', 'm', 'y']
  if actionChar in messageChars:
    print "Today is %s" % _userDateForTime()
    timeMark = currentDefaultTimeMark(scope=actionChar)
    msg = raw_input("Enter message for %s: " % _userStrForMark(timeMark))
    addMessage(msg, timeMark)
  elif actionChar == 't':
    print "Today is %s" % _userDateForTime()
    getUserTimeStrAndMessage()
  elif actionChar == 'a':
    getAllRecentMissingMessages()
  elif actionChar == 'o':
    # TODO Input a filename and save to that file.
    # be sure to avoid code duplication with the
    # command-line version
    print texStringForYear()
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

def showMessages(num=None):
  global _yearMessages
  _loadYear()
  timeMarks = sorted(_yearMessages, key=_timestampForMark)
  if num:
    timeMarks = timeMarks[-num:] # Just keep the most recent num.
  for mark in timeMarks:
    print "%10s %s" % (_userStrForMark(mark), _yearMessages[mark])

def showRecentMissingUserTimeStrs():
  global _yearMessages
  _loadYear()
  allRecent = _recentTimeMarks(8)
  msgRecent = sorted(_yearMessages, key=_timestampForMark)[-8:]
  str = "Missing messages: "
  numMarks = 0
  for timeMark in allRecent:
    if timeMark not in msgRecent:
      if numMarks > 0: str += ", "
      str += _userStrForMark(timeMark)
      numMarks += 1
      if timeMark == _7dateForTime(time.time()):
        str += " (today)"
      elif timeMark == _7dateForTime(time.time() - 24 * 60 * 60):
        str += " (yesterday)"
  if numMarks > 0: print str

def getAllRecentMissingMessages():
  global _yearMessages
  _loadYear()
  allRecent = _recentTimeMarks(8)
  msgRecent = sorted(_yearMessages, key=_timestampForMark)[-8:]
  for timeMark in allRecent:
    if timeMark not in msgRecent:
      msg = raw_input("Enter message for %s: " % _userStrForMark(timeMark))
      addMessage(msg, timeMark)

def getUserTimeStrAndMessage():
  global _userTimeMode
  timestamp = None
  while timestamp is None:
    if _userTimeMode == '7date':
      print "Formats: 123.2025 (day), 12-.2025 (week), 1--.2025 (month), 2025 (year)"
    else:
      print "Formats: 1/30/99 or 30 Jan 1999 (day), <day> - <day> (week), Jan 1999 (month), 1999 (year)"
    userTimeStr = raw_input("Enter time: ")
    timeMark = _markFromUserTimeStr(userTimeStr)
    timestamp = _timestampForMark(timeMark)
    if timestamp is None:
      print "Couldn't parse that time."
  msg = raw_input("Enter message for %s: " % _userStrForMark(timeMark))
  addMessage(msg, timeMark)

def texStringForYear(year=None):
  global _yearLoaded
  _loadYear(year)
  msg = _yearMessages[_yearLoaded] if _yearLoaded in _yearMessages else ""
  strPieces = [texBegin % (int(_yearLoaded), msg)]
  timeMarks = sorted(_yearMessages, key=_timestampForMark)
  monthMarks = []
  weekMarks = []
  for timeMark in timeMarks:
    scope = _scopeForMark(timeMark)
    if scope == "w":
      weekMarks.append(timeMark)
    elif scope == "m":
      monthMarks.append(timeMark)
  for mark in monthMarks:
    monthNum = int(mark[:mark.find('-')])
    msg = _escForTex(_yearMessages[mark])
    strPieces.append(texMonthLine % (monthNum, msg))
  strPieces.append(texMiddle)
  for mark in weekMarks:
    weekNum = int(mark[:mark.find('-')])
    msg = _escForTex(_yearMessages[mark])
    strPieces.append(texMonthLine % (weekNum, msg))
  strPieces.append(texEnd)
  return '\n'.join(strPieces)

# tex template strings
# ====================

# Combine these strings like this:
#  texBegin % (year, yearMsg)
#  texMonthLine % (num, msg) [n times]
#  texMiddle
#  texWeekLine % (num, msg) [n times]
#  texEnd

texBegin = """
\\documentclass[11pt]{amsart}
\\usepackage{multicol}

\\pagestyle{empty}
\\begin{document}
\\thispagestyle{empty}

\\centerline{\\LARGE\\bf %d}
\\bigskip
\\centerline{%s}

\\vspace{1cm}

\\centerline{\\Large Months}
"""

# Input is (monthNum, msg).
texMonthLine = "{\\bf %d.}  %s\n"

texMiddle = """
\\bigskip
\\centerline{\\Large Weeks}

\\begin{multicols}{2}
"""

# Input is (weekNum, msg).
texWeekLine = "{\\bf %d.} %s\n"

texEnd = """
\\end{multicols}

\\end{document}
"""

# private functions
# =================

def _escForTex(str):
  # It's important that we escape out backslashes first.
  # Otherwise we might do something like "\{" -> "\\{" -> "\\\\{",
  # which tex would translate back to "\\{", oops.
  str = str.replace("\\", r"\\")
  str = str.replace("&", r"\&")
  str = str.replace("{", r"\{")
  return str

# This function can also be used as a
# heuristic to see if a string looks
# like a 7date.
def _scopeForMark(timeMark):
  if timeMark.find(' - ') != -1:
    [ts1, ts2] = _firstLastTimesForMark(timeMark)
    if not ts1 or not ts2: return None
    numDays = (ts2 - ts1) / (60 * 60 * 24) + 1
    if 6 < numDays < 8: return 'w'
    if 27 < numDays < 50: return 'm'
    return None
  scopeExpr = [[r"\d+$", "y"],
               [r"\d+\.\d+$", "d"],
               [r"\d+-\.\d+$", "w"],
               [r"\d+--\.\d+$", "m"]]
  for exp, scope in scopeExpr:
    if re.match(exp, timeMark): return scope
  return None

def _firstLastTimesForMark(mark):
  hour = 60 * 60
  sepIndex = mark.find(' - ')
  if sepIndex == -1:
    scope = _scopeForMark(mark)
    if scope == "y":
      year = int(mark)
      date = datetime.date(year, 1, 1)
      ts1 = calendar.timegm(date.timetuple()) + 12 * hour
      date = datetime.date(year + 1, 1, 1)
      ts2 = calendar.timegm(date.timetuple()) - 9 * hour
      return [ts1, ts2]
    elif scope == "d":
      ts = _timestampFor7date(mark) + 12 * hour
      return [ts, ts]
    elif scope == "w":
      lastDig = '6'
      if mark[:3] == '103':
        isLeap = calendar.isleap(int(mark[-4:]))
        lastDig = '1' if isLeap else '0'
      ts1 = _timestampFor7date(mark.replace('-', '0')) + 12 * hour
      ts2 = _timestampFor7date(mark.replace('-', lastDig)) + 13 * hour
      return [ts1, ts2]
    elif scope == "m":
      ts1 = _timestampFor7date(mark.replace('--', '00')) + 12 * hour
      if mark[:2] == '10':
        isLeap = calendar.isleap(int(mark[-4:]))
        lastDigs = '31' if isLeap else '30'
        mark = mark.replace('--', lastDigs)
      else:
        mark = mark.replace('-', '6')
      ts2 = _timestampFor7date(mark) + 14 * hour
      return [ts1, ts2]
    return [None, None]
  dayMarks = [mark[:sepIndex], mark[sepIndex + 3:]]
  # Confirm both dayMarks are valid day marks.
  if any([s != 'd' for s in map(_scopeForMark, dayMarks)]):
    return [None, None]
  times = map(_timestampFor7date, dayMarks)
  times = [t + 12 * hour for t in times]
  numDays = (times[1] - times[0]) / (60 * 60 * 24) + 1
  if 6 < numDays < 8: times[1] += hour  # week
  if 27 < numDays < 50: times[1] += 2 * hour  # month
  return times

# TODO HERE
def _fromDayToScope(timeMark, scope="d", inputMode=None):
  global _userTimeMode
  if inputMode and scope in ["w", "m"] and inputMode != _userTimeMode:
    warn = "Warning: non-%s input provided while in %s mode"
    print warn % (_userTimeMode, _userTimeMode)
  timeMarkChars = list(timeMark)
  dotIndex = timeMark.find('.')
  if scope == "d":
    pass
  elif scope == "w":
    if _userTimeMode == 'Greg':
      ts = _timestampForMark(timeMark)
      d = datetime.datetime.utcfromtimestamp(ts)
      d1 = d + datetime.timedelta(days=(-1 * d.weekday()))
      d2 = d1 + datetime.timedelta(days=6)
      timeMarkChars = list("%s - %s" % tuple(map(_7dateForDateTime, [d1, d2])))
    else:
      if dotIndex > 1:
        timeMarkChars[dotIndex - 1] = '-'
      else:
        timeMarkChars = list("0-.%s" % timeMark[dotIndex + 1:])
  elif scope == "m":
    if _userTimeMode == 'Greg':
      ts = _timestampForMark(timeMark)
      d = datetime.datetime.utcfromtimestamp(ts)
      tm = d.timetuple()
      d1 = d + datetime.timedelta(days=(1 - tm.tm_mday))
      daysInMonth = calendar.monthrange(tm.tm_year, tm.tm_mon)[1]
      d2 = d1 + datetime.timedelta(days=(daysInMonth - 1))
      timeMarkChars = list("%s - %s" % tuple(map(_7dateForDateTime, [d1, d2])))
    else:
      if dotIndex > 2:
        timeMarkChars[(dotIndex - 2):dotIndex] = list('--')
      else:
        timeMarkChars = list("0--.%s" % timeMark[dotIndex + 1:])
  elif scope == "y":
    timeMarkChars = timeMarkChars[(dotIndex + 1):]
  else:
    raise Exception("Expected one of [dmwy] input to _fromDayToScope")
  return ''.join(timeMarkChars)

def _timestampForMark(timeMark):
  return _firstLastTimesForMark(timeMark)[1]

# Returns a 7date string for the given timestamp,
# which is seconds-since-epoch (compatible with
# the output of time.time()).
def _7dateForTime(timestamp=None):
  if timestamp is None: timestamp = time.time()
  tm = time.localtime(timestamp)
  return "%s.%d" % (_baseNString(7, tm.tm_yday - 1), tm.tm_year)

# Assumes the datetime is naive (has no timezone info),
# and is given UTC for the date in mind.
def _7dateForDateTime(dt):
  return _7dateForTime(calendar.timegm(dt.timetuple()))

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
  return timeMark.split(".")[-1]

def _setMessage(msg, timeMark):
  global _yearMessages
  global _yearLoaded
  global _verbose
  year = _yearFromTimeMark(timeMark)
  if _yearLoaded != year:
    _loadYear(year)
  if _verbose and timeMark in _yearMessages:
    print "replaced"
    print "%s %s" % (timeMark, _yearMessages[timeMark])
    print "with"
  elif _verbose:
    print "set"
  if _verbose: print "%s %s" % (timeMark, msg)
  _yearMessages[timeMark] = msg
  _saveMessages()

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
  nonFutureMarks = [m for m in marks if _timestampForMark(m) < timestamp]
  return nonFutureMarks[-8:]

# We expect year as a string.
def _fileForYear(year):
  return _wjDir() + year

def _wjDir():
  homeDir = os.path.expanduser('~') + '/'
  return homeDir + ".wj/"

def _loadConfig():
  global _userTimeMode
  global _userDateFormat
  try:
    try:
      f = open(_wjDir() + 'config')
    except IOError, e:
      return
    config = eval(f.read())
    if 'timeMode' in config: _userTimeMode = config['timeMode']
    if 'dateFormat' in config: _userDateFormat = config['dateFormat']
    f.close()
  finally:
    # TODO TEMP DEBUG
    print "=== Mode: %s ===" % _userTimeMode

# TODO Be able to change user time modes, and call this
#      to save it.
def _saveConfig():
  global _userTimeMode
  global _userDateFormat
  f = open(_wjDir() + 'config', 'w')
  f.write("# Config file for wj.\n")
  f.write("# File format: the string representation of a python dictionary.\n")
  f.write("# dateFormat uses the codes specified on this page:\n")
  f.write("# http://docs.python.org/library/time.html#time.strftime\n")
  config = {'timeMode':_userTimeMode,'dateFormat':_userDateFormat}
  f.write(`config` + "\n")
  f.close()

# user time functions
# ===================

def _userDateForTime(ts=None):
  global _userTimeMode
  global _userDateFormat
  if _userTimeMode == '7date': return _7dateForTime(ts)
  # Gregorian.
  str = time.strftime(_userDateFormat, time.localtime(ts))
  while str[0] == '0': str = str[1:]  # Drop leading 0's.
  return str

def _userStrForMark(mark):
  global _userTimeMode
  global _userDateFormat
  if _userTimeMode == '7date': return mark
  # Produce a Gregorian string.
  scope = _scopeForMark(mark)
  times = _firstLastTimesForMark(mark)
  if scope == 'd': return _userDateForTime(_timestampForMark(mark))
  if scope == 'w': return "%s - %s" % tuple(map(_userDateForTime, times))
  if scope == 'm':
    [tm1, tm2] = map(time.localtime, _firstLastTimesForMark(mark))
    if tm1.tm_mon != tm2.tm_mon or tm1.tm_mday > 1:
      return "%s - %s" % tuple(map(_userDateForTime, times))
    else:
      return time.strftime(_userMonFormat, tm1)
  if scope == 'y': return mark
  print "Warning: Failed to parse the timeMark %s" % mark
  return None

# We accept formats:
# [x] Any valid timeMark.
# [x] today
# [x] yesterday
# [x] n days ago
# [x] last+ week = starts w most recently-done week.
# [x] last month = most recently-done month.
# [x] <d_1> = <m>/dd/<y>, where <y> = yy or yyyy,
#                               <m> = mm or MMM.
# [x] <d_2> = dd MMM,? <y>           MMM = Jan, Feb, etc.
# [x] <d> = <d_1> or <d_2>
# [x] <d> - <d>, interpreted as a week
# [x] <m>[/ ]dd - [<m>][/ ]dd[/ ]<y>, interpreted as a week
# [x] dd - dd MMM,? <y>
# [x] <m>,? <y>
# Note that yyyy is already a valid timeMark.
# There is probably a better way to express all this.
# TODO eventually replace the above comments with a user-visible
#      string that we can display in a help screen.
def _markFromUserTimeStr(userTimeStr):
  dayTime = 60 * 60 * 24
  weekTime = dayTime * 7
  scope = _scopeForMark(userTimeStr)
  if scope: return userTimeStr
  if userTimeStr == 'today':
    return _7dateForTime(time.time())
  if userTimeStr == 'yesterday':
    return _7dateForTime(time.time() - dayTime)
  m = re.match(r"(\d+) days? ago", userTimeStr)
  if m:
    daysAgo = int(m.group(1))
    return _7dateForTime(time.time() - daysAgo * dayTime)
  m = re.match(r"((?:last )+)week", userTimeStr)
  if m:
    weeksAgo = len(m.group(1).split(' ')) - 1
    nowForThisWeek = time.time() + 60 * 60 * 11
    aDay = _7dateForTime(nowForThisWeek - weeksAgo * weekTime)
    return _fromDayToScope(aDay, 'w')
  if userTimeStr == 'last month':
    nowForThisMonth = time.time() + 60 * 60 * 10
    aDay = _7dateForTime(nowForThisMonth)
    thisMonth = _fromDayToScope(aDay, 'm')
    aMonth = thisMonth
    prevTime = nowForThisMonth
    while thisMonth == aMonth:
      prevTime -= dayTime * 28  # Min month length.
      aMonth = _fromDayToScope(_7dateForTime(prevTime), 'm')
    return aMonth
  # monthExp gives back two groups - hand them to _monFromStrs
  monthExp = r"((?i)(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*|\d+)"
  m = re.match(r"%s,? (\d+)$" % monthExp, userTimeStr)
  if m:
    mon = _monFromStrs(m.group(1), m.group(2))
    year = int(m.group(3))
    tm = (year, mon, 15, 12, 00, 00, 0, 0, -1)
    # TODO Move warnings into this fun; use an auxilliary function to help out.
    return _fromDayToScope(_7dateForTime(time.mktime(tm)), 'm', inputMode='Greg')
  dayExp1 = r"%s[/ -](\d+)[/ -](\d+)" % monthExp  # 4 groups
  dayExp2 = r"(\d+) (\w+)[, ]+(\d+)"  # 3 groups
  dayExp = r"(?:%s|%s)" % (dayExp1, dayExp2)  # 7 groups
  m = re.match("%s$" % dayExp, userTimeStr)
  if m:
    ts = _dayFromMatch(m, 0)
    return _7dateForTime(ts) if ts else None
  weekExp1 = r"%s ?- ?%s" % (dayExp, dayExp)
  m = re.match(weekExp1, userTimeStr)
  if m:
    ts = _week1FromMatch(m)
    return _fromDayToScope(_7dateForTime(ts), 'w') if ts else None
  weekExp2 = r"%s[/ ](\d+) ?- ?(?:%s[/ ])?(\d+)[/ ](\d+)" % (monthExp, monthExp)
  m = re.match(weekExp2, userTimeStr)
  if m:
    ts = _week2FromMatch(m)
    return _fromDayToScope(_7dateForTime(ts), 'w') if ts else None
  weekExp3 = r"(\d+)(?: (\w+))? ?- ?(\d+) (\w+),? (\d+)"
  m = re.match(weekExp3, userTimeStr)
  if m:
    ts = _week3FromMatch(m)
    return _fromDayToScope(_7dateForTime(ts), 'w') if ts else None
  return None

def _week1FromMatch(m):
  ts1 = _dayFromMatch(m, 0)
  ts2 = _dayFromMatch(m, 7)
  if ts1 is None or ts2 is None: return None
  return (ts1 + ts2) / 2.0

def _week2FromMatch(m):
  mon1 = _monFromStrs(m.group(1), m.group(2))
  mday1 = int(m.group(3))
  mon2 = mon1
  if m.group(4) or m.group(5):
    mon2 = _monFromStrs(m.group(4), m.group(5))
  mday2 = int(m.group(6))
  year = _yearFromStr(m.group(7))
  if not all([mon1, mday1, mon2, mday2, year]): return None
  ts1 = time.mktime((year, mon1, mday1, 12, 0, 0, 0, 0, -1))
  ts2 = time.mktime((year, mon2, mday2, 12, 0, 0, 0, 0, -1))
  return (ts1 + ts2) / 2.0
  
def _week3FromMatch(m):
  mday1 = int(m.group(1))
  mday2 = int(m.group(3))
  mon2 = _monFromStrs(None, m.group(4))
  mon1 = mon2
  if m.group(2):
    mon1 = _monFromStrs(None, m.group(2))
  year = _yearFromStr(m.group(5))
  if not mon1 or not mon2: return None
  ts1 = time.mktime((year, mon1, mday1, 12, 0, 0, 0, 0, -1))
  ts2 = time.mktime((year, mon2, mday2, 12, 0, 0, 0, 0, -1))
  return (ts1 + ts2) / 2.0

def _monFromStrs(wholeMatch, firstLetters):
  if wholeMatch and wholeMatch.isdigit():
    mon = int(wholeMatch)
    return mon if 0 < mon <= 12 else None
  monStrs = calendar.month_abbr
  letters = firstLetters[:3].lower()
  match = [i for i in enumerate(monStrs) if i[1].lower() == letters]
  return match[0][0] if match else None

# Returns a timestamp for noon on the given day,
# or None if there's an error.
def _day1FromMatch(m, offset):
  mon = _monFromStrs(m.group(1 + offset), m.group(2 + offset))
  mday = int(m.group(3 + offset))
  year = _yearFromStr(m.group(4 + offset))
  return _timeFromDayMonYear(mday, mon, year)

def _day2FromMatch(m, offset):
  mon = _monFromStrs(None, m.group(2 + offset))
  mday = int(m.group(1 + offset))
  year = _yearFromStr(m.group(3 + offset))
  return _timeFromDayMonYear(mday, mon, year)

def _dayFromMatch(m, offset):
  if any([m.group(i) for i in range(1, 5)]):
    return _day1FromMatch(m, offset)
  return _day2FromMatch(m, 4)

def _timeFromDayMonYear(mday, mon, year):
  if not all([mday, mon, year]): return None
  if mon < 1 or mon > 12: return None
  lastMDay = calendar.monthrange(year, mon)[1]
  if mday < 1 or mday > lastMDay: return None
  return time.mktime((year, mon, mday, 12, 0, 0, 0, 0, -1))

def _yearFromStr(year):
  if len(year) > 2: return int(year)
  tm = time.localtime()
  year = (tm.tm_year // 100) * 100 + int(year)
  # Interpret 95 as 1995 (not 2095) if it's 2013.
  if year > tm.tm_year + 1: year -= 100
  return year

def _gregDayStrFromTm(tm):
  months = calendar.month_abbr
  return "%s %d, %d" % (months[tm.tm_mon], tm.tm_mday, tm.tm_year)

def _userTimeStrFromMark(timeMark):
  global _userTimeMode
  if _userTimeMode == '7date':
    return timeMark
  elif _userTimeMode == 'Greg':
    scope = _scopeForMark(timeMark)
    ts = _timestampForMark(timeMark)
    tm = time.localtime(ts)
    months = calendar.month_abbr
    if scope == "d":
      return _gregDayStrFromTm(tm)
    elif scope == "w":
      lastTm = time.localtime(ts + 60 * 60 * 24 * 6)
      if tm.tm_year != lastTm.tm_year:
        return "%s - %s" % (_gregDayFromTm(tm), _gregDayFromTm(lastTm))
      elif tm.tm_mon != lastTm.tm_mon:
        strArgs = (months[tm.tm_mon], tm.tm_mday, months[lastTm.tm_mon],
                   lastTm.tm_mday, tm.tm_year)
        return "%s %d - %s %d, %d" % strArgs
      else:
        return "%s %d - %d, %d" % (months[tm.tm_mon], tm.tm_mday,
                                   lastTm.tm_mday, tm.tm_year)
    elif scope == "m":
      return "%s %d" % (months[tm.tm_mon], tm.tm_year)
    # It's either a year or an error here.
    return timeMark
  else:
    print "ruh roh: unrecognized userTimeMode %s" % _userTimeMode
  return timeMark

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

_loadConfig()  # Load config whether this is an import or an execution.

if __name__ ==  "__main__":
  handleArgs(sys.argv)
  _saveConfig()
  # TODO HERE
  # I'm currently working on getting everything to run smoothly in Gregorian mode.
  # I'd like to test it more by directly using it, and do a read-through of the
  # time conversion functions to look for any cases I may have missed.
