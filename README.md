# UPDATE: deprecation

I'm deprecating this project in favor of [srtfix](https://github.com/bwu62/srtfix) which is a rewritten cli-tool that's significantly simpler in code and easier to use.

---

---

---

# subshift subtitle syncer

Couldn't find a subtitle syncer I liked so I just wrote my own. Currently only .srt files are supported (.ass file support may be added in the future)

this is a work in progress, feel free to test it, submit issues, or fork it.

## Main methods:

 - linear shift (increase/decrease delay)
 - linear mapping (given 2 source timestamps and 2 target timestamps, it will linearly stretch and shift them to match)
 - delay mapping (similar to linear mapping, except instead of 2 target timestamps, the subtitle delay correction value is given at two timestamps)

## Other features supported:
 - sorting
 - reset method (if you wish to revert all changes made to the current sub)
 - read and write features (obviously)
 - slicing
 - head and tail to quickly view them

## Example usage:

```
# import

import subshift


# load .srt file
# all srt files should be supported (unless there's weird encoding issues)
# multi-line subs are of course supported and cause no problems
# 
# the index number for each entry in .srt ignored by subshift at import
# and automatically corrected and written at export

sub = subshift.Subtitle("/path/to/subtitle.srt")


# inspect subtitles
# both head and tail default to 10 lines, but you can ask for more/less

sub.head()
sub.tail(lines=20)


# also supports standard python slicing

print sub[50:60]


# usually not needed unless you're adding new subtitles, but you can sort
# (sorting is done chronologically by start time)

sub.sort()


# shift the subtitles by giving amount of time to increase or decrease delay
# (positive number increases delay, i.e. they appear later)
# (negative number decrease delay, i.e. they appear earlier)

sub.shift(5)       # increase delay by 5 seconds
sub.shift(-3.14)   # decrease delay by 3 seconds, 140 milliseconds


# linearly map 2 points in the file to 2 points in the video
# input should be a single string with 4 time stamps in the HH:MM:SS.MS format
# Also: leading and trailing zeroes, HH, and HH:MM can all be omitted
# 
# for example, to map 55 seconds to 1 min 7 sec 400 milliseconds, and also map
# 1 hour 20 min 55 sec 300 ms to 1 hour 21 min 6 sec 950 ms, you can do:

sub.linearMap("55 1:7.4 1:20:55.3 1:21:06.95")


# Note: any delimiter except : and . can be used
# subshift matches a regular expression to find 4 timestamps in input string
# Also: if only 2 timestamps are found, a simple shift is done to match them
# 
# you can also specify the delay correction (in seconds) at two HMS timestamps
# for example, if the subtitle is 0.5 seconds early at 1 min 20 sec 600 ms but
# 2.8 seconds late at 1 hour 40 min 10 sec, you can do:

sub.delayMap("1:20.6 0.5 1:40:10 -2.8")


# if you mess up and want to start over, you can reset subs to original state:

sub.reset()


# to write out your new subtitles, use write
# any subtitles shifted to a negative timestamp will be automatically ignored
# by the write method, but this can be disabled by setting dropNegatives=False

sub.write("/path/to/newsubtitle.srt")

```
