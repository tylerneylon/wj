#!/usr/bin/python

import sys
import wj

# TODO PRIORITY
# Make sure we handle errors well.
# We should avoid exceptions (catch them)
# and say something friendly about it
# to the user.

def expectVsActual(expected, actual, comment=None):
  if expected == actual: return
  print "Failure"
  print "expected %s" % `expected`
  print "actual %s" % `actual`
  if comment: print "comment: %s" % comment
  sys.exit(1)


mark = wj._markFromUserTimeStr("345.2001")
expectVsActual("345.2001", mark)

# It would take a little more effort to make these
# tests work at any time.
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

testStrs = [["Jan, 1988", "0--.1988"],
            ["December 1972", "10--.1972"],
            ["12 1972", "10--.1972"],
            ["06/01/79", "304.1979"],
            ["0623423/01/793242", None],
            ["9-11-01", "511.2001"],
            ["Feb/29/2000", "113.2000"],
            ["Feb/29/2001", None],
            ["1 Jan 2025", "0.2025"],
            ["1 February 1950", "43.1950"],
            ["1 Feb,1950", "43.1950"],
            ["30 Feb 3000", None],
            ["10/22/11-10/28/11", "60-.2011"],
            ["1/1-7/11", "0-.2011"],
            ["Feb 5 - 11 2001", "5-.2001"],
            ["9/3 - 9/9/1995", "50-.1995"],
            ["1/29-2/4/88", "4-.1988"],
            ["22 - 28 Oct 2011", "60-.2011"],
            ["1-7 Jan 11", "0-.2011"],
            ["29 Jan - 4 Feb 1988", "4-.1988"]]

for testCase in testStrs:
  mark = wj._markFromUserTimeStr(testCase[0])
  expectVsActual(testCase[1], mark, comment=testCase[0])

wj._userTimeMode = 'Greg'
testStrs = [["0.2001", "1 Jan 2001"],
            ["3-.1979", "22 Jan 1979 - 28 Jan 1979"],
            ["0--.1988", "1 Jan 1988 - 18 Feb 1988"],
            ["0.1965 - 6.1965", "1 Jan 1965 - 7 Jan 1965"],
            ["0.2011 - 42.2011", "Jan 2011"],
            # This next case is weird, and I decided the
            # current string is best because it is true
            # (albeit redundant) and includes the idea that
            # the scope is abstractly more than a day.
            # In most cases, users will never see this.
            ["103-.2035", "31 Dec 2035 - 31 Dec 2035"],
            ["10--.2025", "10 Dec 2025 - 31 Dec 2025"]]
for testCase in testStrs:
  userStr = wj._userStrForMark(testCase[0])
  expectVsActual(testCase[1], userStr, comment=testCase[0])

print "fortune smiles upon you... for now - all tests passed"
exit(0)
