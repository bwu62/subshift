from __future__ import division
import re



# use regex to find all HH:MM:SS.MS timestamps in string
# n specifies how many to look for (default None finds all)
# raises error if number found doesn't match n

def findNhms(string,n=None):
    found = re.findall(r"[,:\d\.]+",string)
    if (not n is None) and len(found)!=n:
        print(string)
        raise ValueError("Found wrong number of times.")
    else:
        return found


# converts HH:MM:SS.MS timestamp string to integer milliseconds
# if/else cases allow ommision of HH, or HH:MM, or HH:MM:SS if all zero

def hmsToMs(string):
    temp = string.replace(",",".").split(":")
    temp = map(lambda x: x if x else 0,temp)
    if len(temp) == 3:
        h,m,s = [int(temp[0]),int(temp[1]),float(temp[2])]
    elif len(temp) == 2:
        h,m,s = [0,int(temp[0]),float(temp[1])]
    elif len(temp) == 1:
        h,m,s = [0,0,float(temp[0])]
    else:
        raise ValueError("Wrong HMS format.")
    return int((h*3600+m*60+s)*1000)


# converts milliseconds back to timestamps for writing to file

def msToHms(x,sep=",",write=False):
    spacer = "" if write else " "
    sign = 1 if x >= 0 else -1
    x = x*sign
    ms = x%1000 ; x = (x-ms)//1000
    s  = x%60   ; x = (x-s)//60
    m  = x%60   ; x = (x-m)//60
    return "%s%02i:%02i:%02i%s%03i"%(spacer if sign==1 else "-",x,m,s,sep,ms)


# main method for parsing SRT files
# stores start/end time and text (supports multi-line) for each subtitle entry

def readSrt(filepath,skip):
    starts,ends,subs = [],[],[]
    
    # stat is a flag variable indicating what the program expects to find on the next line
    # logic checks based on format specification of SRT updates stat while iterating through lines
    # this is necessary since some entries may contain multiple lines
    
    stat = 'idx'
    multi = []
    with open(filepath,'r') as f:
        for i,line in enumerate(f):
            
            # strips leading non printing characters

            line = line.lstrip('\xef\xbb\xbf').lstrip('\xff\xfe').lstrip('\xfe\xff').replace("\x00","").rstrip()
            
            # after an 'idx' line (each entry is indexed starting from 1) next non empty line contains timestamps
            # the indices are irrelevant and not stored; they're automatically re-generated on output
            
            if stat == 'idx' and line != '':
                stat = 'time'
            
            # parse timestamp line, then set status flag to 'sub' for subtitle text

            elif stat == 'time':
                temp = map(hmsToMs,findNhms(line,2))
                stat = 'sub'
            
            # if stat is 'sub' and line nonempty, append to 'multi' (which may contain multiple lines of text)
            # each entry separated by empty line, so check for this to finish writing current entry

            elif stat == 'sub':
                if line != '':
                    multi.append(line)
                else:
                    stat = 'idx'
                    if skip > 0:
                        skip -= 1
                    elif len(multi) > 0:
                        starts.append(temp[0])
                        ends.append(temp[1])
                        subs.append(multi)
                    multi = []
    
    # check non-empty entry and store to arrays

    if stat == "sub" and len(multi) > 0:
        starts.append(temp[0])
        ends.append(temp[1])
        subs.append(multi)
    n = len(starts)
    return([[i,starts[i],ends[i],subs[i]] for i in xrange(n)])


# simple print function

def printLines(subtitles,Range=None):
    printsub = subtitles if Range is None else subtitles[slice(*Range)]
    return "\n".join(["\n".join(["\t".join(
        ["% 4d"%(entry[0]) if j==0 else " "*4 ,
         msToHms(entry[1],sep=".",write=False) if j==0 else " "*12,
         msToHms(entry[2],sep=".",write=False) if j==0 else " "*12, line]
    ) for j,line in enumerate(entry[3])]) for entry in printsub])


# function for writing index and subtitle entry to file

def writeEntry(n,entry):
    return "{}\n{} --> {}\n{}\n".format(n,msToHms(entry[1],write=True),msToHms(entry[2],write=True),"\n".join(entry[3]))


# main subtitle class

class Subtitle:
    
    def __init__(self,subtitleFile,skip=0):
        if isinstance(subtitleFile,str):
            self.subtitles = readSrt(subtitleFile,skip)
            self.sort()
            self._sorted = True
        elif isinstance(subtitleFile,list):
            self.subtitles = subtitleFile
            self._sorted = False
        self._backup = repr(self.subtitles)
    
    def __repr__(self):
        return "Subtitle([" + ",".join([repr(self.subtitles[i]) for i in xrange(len(self.subtitles))]) + "])"
    
    def __str__(self):
        return printLines(self.subtitles)
    
    def __len__(self):
        return len(self.subtitles)
    

    # implements native pythonic slicing for subtitle class for easy access

    def __getitem__(self,choice):
        if isinstance(choice,int):
            return eval("Subtitle([" + repr(self.subtitles.__getitem__(choice))+ "])")
        elif isinstance(choice,slice):
            return eval("Subtitle(" + repr(self.subtitles.__getitem__(choice))+ ")")
        else:
            raise TypeError("Wrong slice")
    

    # head and tail methods for convenience (defaults to 10 entries)

    def head(self,lines=10):
        print printLines(self.subtitles[:lines])
    
    def tail(self,lines=10):
        print printLines(self.subtitles[-lines:])
    

    # restores subtitles to initial load from file if you mess up
    # ._backup automatically stores a copy on instantiation

    def reset(self):
        self.subtitles = self._backup
    

    # sort entries by start time
    
    def sort(self):
        self.subtitles = sorted(self.subtitles,key=lambda x:x[1])
        for i in xrange(len(self.subtitles)):
            self.subtitles[i][0] = i+1
    
    
    # basic linear shift method (in seconds)
    # positive shift to increase delay, negative to decrease
    # see readme for detailed usage examples
    
    def shift(self,s):
        func = lambda x: int(x+s*1000)
        self.subtitles = map(lambda x:[x[0],func(x[1]),func(x[2]),x[3]],self.subtitles)
    
    
    # linear mapping algorithm for subtitles stored at different FPS than video
    # maps two given pairs of timestamps in subtitle file to video file
    # see readme for detailed usage examples
    
    def linearMap(self,hmsStrings):
        temp = findNhms(hmsStrings)
        if len(temp) == 4:
            a,A,b,B = map(hmsToMs,temp)
            func = lambda x: int((x-a)*(A-B)/(a-b)+A)
        elif len(temp) == 2:
            a,A = map(hmsToMs,temp)
            func = lambda x: int(x+(A-a))
        self.subtitles = map(lambda x:[x[0],func(x[1]),func(x[2]),x[3]],self.subtitles)
    
    
    # similar to linearMap but uses two corrective delays at two points in video to calculate map
    # see readme for detailed usage examples
    
    def delayMap(self,hmsStrings):
        temp = findNhms(hmsStrings)
        if len(temp) == 4:
            a,A,b,B = map(hmsToMs,temp)
            a,A = (a-A,a)
            b,B = (b+B,b)
            func = lambda x: int((x-a)*(A-B)/(a-b)+A)
        else:
            raise ValueError("Wrong input.")
        self.subtitles = map(lambda x:[x[0],func(x[1]),func(x[2]),x[3]],self.subtitles)
    
    
    # write subtitles to file
    # indices are automatically recalculated
    # dropNegatives (default True) removes entries with negative start time
    # auto-sorts subtitles if new entries were added and not sorted

    def write(self,filepath,dropNegatives=True):
        if not self._sorted:
            self.sort()
        sep = "\n"
        n = 1
        with open(filepath,'w') as f:
            for entry in self.subtitles:
                if dropNegatives and min(entry[1],entry[2])>=0:
                    if entry == self.subtitles[-1]:
                        sep = ""
                    f.write(writeEntry(n,entry)+sep)
                    n += 1
            f.write("\n")
