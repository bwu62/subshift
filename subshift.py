from __future__ import division
import re

def findNhms(string,n=None):
    temp = re.findall(r"[,:\d\.]+",string)
    if (not n is None) and len(temp)!=n:
        print(string)
        raise ValueError("Found wrong number of times.")
    else:
        return temp

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

def msToHms(x,sep=",",write=False):
    spacer = "" if write else " "
    sign = 1 if x >= 0 else -1
    x = x*sign
    ms = x%1000 ; x = (x-ms)//1000
    s  = x%60   ; x = (x-s)//60
    m  = x%60   ; x = (x-m)//60
    return "%s%02i:%02i:%02i%s%03i"%(spacer if sign==1 else "-",x,m,s,sep,ms)

def readSrt(filepath,skip):
    starts,ends,subs = [],[],[]
    stat = 'idx'
    multi = []
    with open(filepath,'r') as f:
        for i,line in enumerate(f):
            line = line.lstrip('\xef\xbb\xbf').lstrip('\xff\xfe').lstrip('\xfe\xff').replace("\x00","").rstrip()
            if stat == 'idx' and line != '':
                stat = 'time'
            elif stat == 'time':
                temp = map(hmsToMs,findNhms(line,2))
                stat = 'sub'
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
    if stat == "sub" and len(multi) > 0:
        starts.append(temp[0])
        ends.append(temp[1])
        subs.append(multi)
    n = len(starts)
    return([[i,starts[i],ends[i],subs[i]] for i in xrange(n)])

def printLines(subtitles,Range=None):
    printsub = subtitles if Range is None else subtitles[slice(*Range)]
    return "\n".join(["\n".join(["\t".join(
        ["% 4d"%(entry[0]) if j==0 else " "*4 ,
         msToHms(entry[1],sep=".",write=False) if j==0 else " "*12,
         msToHms(entry[2],sep=".",write=False) if j==0 else " "*12, line]
    ) for j,line in enumerate(entry[3])]) for entry in printsub])

def writeEntry(n,entry):
    return "{}\n{} --> {}\n{}\n".format(n,msToHms(entry[1],write=True),msToHms(entry[2],write=True),"\n".join(entry[3]))

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
    
    def __getitem__(self,choice):
        if isinstance(choice,int):
            return eval("Subtitle([" + repr(self.subtitles.__getitem__(choice))+ "])")
        elif isinstance(choice,slice):
            return eval("Subtitle(" + repr(self.subtitles.__getitem__(choice))+ ")")
        else:
            raise TypeError("Wrong slice")
    
    def head(self,lines=10):
        print printLines(self.subtitles[:lines])
    
    def tail(self,lines=10):
        print printLines(self.subtitles[-lines:])
    
    def reset(self):
        self.subtitles = self._backup
    
    def sort(self):
        self.subtitles = sorted(self.subtitles,key=lambda x:x[1])
        for i in xrange(len(self.subtitles)):
            self.subtitles[i][0] = i+1

    def shift(self,s):
        if isinstance(s,str):
            s = hmsToMs(s)/1000
        func = lambda x: int(x+s*1000)
        self.subtitles = map(lambda x:[x[0],func(x[1]),func(x[2]),x[3]],self.subtitles)
        
    def linearMap(self,hmsStrings):
        temp = findNhms(hmsStrings)
        if len(temp) == 4:
            a,A,b,B = map(hmsToMs,temp)
            func = lambda x: int((x-a)*(A-B)/(a-b)+A)
        elif len(temp) == 2:
            a,A = map(hmsToMs,temp)
            func = lambda x: int(x+(A-a))
        self.subtitles = map(lambda x:[x[0],func(x[1]),func(x[2]),x[3]],self.subtitles)
    
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
