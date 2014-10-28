wj (work journal)
=================

wj is a python script to help track your progress on all work projects.

It is meant as a thin layer on top of a brief text-based journal.

## A single page for every year

The primary objective is to make it easy to see at a glance what I
have been working on lately.  The long-term vision is to produce
a single page, year-long summary consisting of 52 sentences, one
per week.

The motivation for this is to give me a bird's eye view of my
own progress that is hard to see on a daily basis.  It's nice
to gain perspective on where I'm gaining or losing momentum,
as well as to keep an eye out for lower priority projects that
are eating up too much time.

## Support for the 7date calendar

Most people use the traditional Gregorian calendar. However,
I'm a fan of the 7date calendar which is more mathematically
consistent. You can use `wj` with the 7date calendar by changing
the `timeMode` setting of `Greg` to `7date` in the file `~/.wj/config`.

In case the 7date calendar is new to you:

* [This year's 7date calendar (with Gregorian dates as well).](http://tylerneylon.com/a/7date/)
* [The 7date calendar spec.](http://tylerneylon.com/a/7date_spec/)
