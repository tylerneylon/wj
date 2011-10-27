#!/usr/bin/python

import sys
import wj

def expectVsActual(expected, actual):
  if expected == actual: return
  print "Failure"
  print "expected %s" % `expected`
  print "actual %s" % `actual`
  sys.exit(1)


mark = wj._markFromUserTimeStr("345.2001")
expectVsActual("345.2001", mark)

mark = wj._markFromUserTimeStr("today")
expectVsActual("604.2011", mark)

mark = wj._markFromUserTimeStr("yesterday")
expectVsActual("603.2011", mark)

mark = wj._markFromUserTimeStr("3 days ago")
expectVsActual("601.2011", mark)

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

print "fortune smiles upon you... for now - all tests passed"

