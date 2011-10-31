#!/usr/bin/python

import sys
import wj

# TODO PRIORITY
# Make sure we handle errors well.
# We should avoid exceptions (catch them)
# and say something friendly about it
# to the user.

def expectVsActual(expected, actual):
  if expected == actual: return
  print "Failure"
  print "expected %s" % `expected`
  print "actual %s" % `actual`
  sys.exit(1)


mark = wj._markFromUserTimeStr("345.2001")
expectVsActual("345.2001", mark)

if False:
  mark = wj._markFromUserTimeStr("today")
  expectVsActual("606.2011", mark)

  mark = wj._markFromUserTimeStr("yesterday")
  expectVsActual("605.2011", mark)

  mark = wj._markFromUserTimeStr("3 days ago")
  expectVsActual("603.2011", mark)

  mark = wj._markFromUserTimeStr("last week")
  expectVsActual("56-.2011", mark)

  mark = wj._markFromUserTimeStr("last last week")
  expectVsActual("55-.2011", mark)

  mark = wj._markFromUserTimeStr("last month")
  expectVsActual("5--.2011", mark)

mark = wj._markFromUserTimeStr("Jan, 1988")
expectVsActual("0--.1988", mark)

mark = wj._markFromUserTimeStr("December 1972")
expectVsActual("10--.1972", mark)

mark = wj._markFromUserTimeStr("12 1972")
expectVsActual("10--.1972", mark)

mark = wj._markFromUserTimeStr("06/01/79")
expectVsActual("304.1979", mark)

mark = wj._markFromUserTimeStr("0623423/01/793242")
expectVsActual(None, mark)

mark = wj._markFromUserTimeStr("9-11-01")
expectVsActual("511.2001", mark)

mark = wj._markFromUserTimeStr("Feb/29/2000")
expectVsActual("113.2000", mark)

mark = wj._markFromUserTimeStr("Feb/29/2001")
expectVsActual(None, mark)

print "fortune smiles upon you... for now - all tests passed"

