#!/usr/bin/python

# TODO NEXT
# [x] List recent entries on interactive startup.
# [x] Add suggestions for recent missing entries.
# [x] Add an 'a' command in interactive mode to input all recent missing entries.
# [ ] Make sure we can handle w,m,y actions.
# [ ] Add a command-line way to view more than just -r entries.

# TODO Eventually
# [x] Provide output with -o option.
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
_verbose = False
# Possible values are '7date', 'Greg'
# TODO Load this from a conf file, if it exists.
_userTimeMode = '7date'

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
    exit()
  if options.showRecent:
    showMessages(8)
    exit()
  if options.outfile:
    texString = texStringForYear()
    f = open(options.outfile, 'w')
    f.write(texString)
    f.close()
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
  if timeMark is None:
    timeMark = currentDefaultTimeMark()
  _setMessage(msg, timeMark)

def runInteractive():
  print "Work Journal (wj)"
  print "Recent messages:"
  showMessages(8)
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
    getUserTimeMarkAndMessage()
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
  for timeMark in timeMarks:
    print "%10s %s" % (timeMark, _yearMessages[timeMark])

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

def getAllRecentMissingMessages():
  global _yearMessages
  _loadYear()
  allRecent = _recentTimeMarks(8)
  msgRecent = sorted(_yearMessages, key=_timestampForMark)[-8:]
  for timeMark in allRecent:
    if timeMark not in msgRecent:
      msg = raw_input("Enter message for %s: " % timeMark)
      addMessage(msg, timeMark)

def getUserTimeMarkAndMessage():
  timestamp = None
  while timestamp is None:
    print "Formats: 123.2025 (day), 12-.2025 (week), 1--.2025 (month), 2025 (year)"
    timeMark = raw_input("Enter timemark: ")
    timestamp = _timestampForMark(timeMark)
    if timestamp is None:
      print "Couldn't parse that timemark."
  msg = raw_input("Enter message for %s: " % timeMark)
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
  scopeExpr = [[r"\d+$", "y"],
               [r"\d+\.\d+$", "d"],
               [r"\d+-\.\d+$", "w"],
               [r"\d+--\.\d+$", "m"]]
  for exp, scope in scopeExpr:
    if re.match(exp, timeMark): return scope
  return None

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
    if dotIndex > 1:
      timeMarkChars[dotIndex - 1] = '-'
    else:
      timeMarkChars = list("0-.%s" % timeMark[dotIndex + 1:])
  elif scope == "m":
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
  hour = 60 * 60
  scope = _scopeForMark(timeMark)
  if scope == "y":
    year = int(timeMark)
    date = datetime.date(year + 1, 1, 1)
    ts = calendar.timegm(date.timetuple())
    return ts - 9 * hour
  elif scope == "d":
    ts = _timestampFor7date(timeMark)
    return ts + 12 * hour
  elif scope == "w":
    lastDig = '6'
    if timeMark[:3] == '103':
      isLeap = calendar.isleap(int(timeMark[-4:]))
      lastDig = '1' if isLeap else '0'
    timeMark = timeMark.replace('-', lastDig)
    ts = _timestampFor7date(timeMark)
    return ts + 13 * hour
  elif scope == "m":
    if timeMark[:2] == '10':
      isLeap = calendar.isleap(int(timeMark[-4:]))
      lastDigs = '31' if isLeap else '30'
      timeMark = timeMark.replace('--', lastDigs)
    else:
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

# user time functions
# ===================


# We accept formats:
# [x] Any valid timeMark.
# [x] today
# [x] yesterday
# [x] n days ago
# [x] last+ week = starts w most recently-done week.
# [x] last month = most recently-done month.
# [ ] <d_1> = <m>/dd/<y>, where <y> = yy or yyyy,
#                               <m> = mm or MMM.
# [ ] <d_2> = dd MMM,? <y>           MMM = Jan, Feb, etc.
# [ ] <d> = <d_1> or <d_2>
# [ ] <d> - <d>, interpreted as a week
# [ ] dd[/ ][<m>] - dd[/ ]<m>[/ ]<y>, interpreted as a week
# [ ] dd[/ ]<m> - dd[/ ][<m>][/ ]<y>
# [ ] MMM dd[(st,nd,rd,th)],? - MMM dd[(st,nd,rd,th)],? <y>
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
  m = re.match(r"%s,? (\d+)" % monthExp, userTimeStr)
  if m:
    mon = _monFromStrs(m.group(1), m.group(2))
    year = int(m.group(3))
    tm = (year, mon, 15, 12, 00, 00, 0, 0, -1)
    return _fromDayToScope(_7dateForTime(time.mktime(tm)), 'm', inputMode='Greg')
  # TODO HERE and below; update to match the new d_1, d_2 syntaxes above (oops)
  # dayExp gives back 4 groups - hand them to _dayFromStrs
  dayExp = r"(\d+)[/ -]%s,?[/ -](\d+)" % monthExp
  m = re.match(dayExp, userTimeStr)
  if m:
    ts = _dayFromStrs(m.group(1), m.group(2), m.group(3), m.group(4))
    return _7dateForTime(ts)
  return None
  
def _monFromStrs(wholeMatch, firstLetters):
  if wholeMatch.isdigit(): return int(wholeMatch)
  monStrs = calendar.month_abbr
  match = [i for i in enumerate(monStrs) if i[1].lower() == firstLetters.lower()]
  return match[0][0] if match else None

# Returns a timestamp for noon on the given day,
# or None if there's an error.  TODO check this is correct
def _dayFromStrs(mday, mon1, mon2, year):
  mday = int(mday)
  if len(year) == 2:
    tm = time.localtime()
    year = (tm.tm_year // 100) * 100 + int(year)
    # Interpret 95 as 1995 (not 2095) if it's 2013.
    if year > tm.tm_year + 1:
      year -= 100
  else:
    year = int(year)
  mon = _monFromStrs(mon1, mon2)
  if mon is None: return None
  return time.mktime((year, mon, mday, 12, 0, 0, 0, 0, -1))

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

if __name__ ==  "__main__":
  handleArgs(sys.argv)
