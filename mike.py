#!/usr/bin/env python
# grep ^Subject MIKE\ DATA.mbox > m1
# grep -E "^Date|^Subject" MIKE\ DATA.mbox > m2

# @TODO 
#       Make searchable web page. (all fields, date range)
#       
from collections import Counter
import datetime
import argparse
import time
import pickle
import email.utils as eu
import numpy as np
import pandas as pd

#Subject line possible from/to
#a,b to c,d
#a b,c to d,e
#a,b to c d, e
#a b,c to d e,f

class MikeDataParser:
    def __init__(self,filename):   
        self._filename    = filename
        #self._record      = set()
        #self._received    = None
        self._dataframe   = None

    def readlines(self):
        record = list()
        with open(self._filename) as f: lines = f.readlines()
        for ll in lines:
            sl=ll.strip()
            spacesep = ll.split()
            commasep = ll.split(',')
            if spacesep[0] == "Date:": 
                received = [self.parseDateToPandas(sl[5:])]
            if spacesep[0] == "Subject:": 
                alist = self.parseSubjectToPandas(spacesep,commasep) 
                if alist is None: continue
                received.extend(alist)
                record.append(received)

        self._dataframe  = pd.DataFrame.from_records(record,columns=['Received Date','Pickup Date','From','To','Distance'])
        self._dataframe.drop_duplicates(inplace=True)

    def parseSubjectToPandas(self,line,commasep):
        #_ftd         = set()
        if line[1] != "PU:": return None
        pickupdate = pd.to_datetime(line[2]+" "+line[3])
        # this will be split into 4
        # find last digit (of time HH:MM) in order to
        # isolate the from location
        numindex = -1
        for i,c in enumerate(commasep[0]):
             if c.isdigit(): numindex = i+2  #skip the space
        if numindex == -1:
           print "error on %s"%l
           return None
        # need to get from state abbrev from the next token
        x = commasep[1].split("to")
        from_ = commasep[0][numindex:]+","+x[0]
        # need to get to state abbrev from the next token
        y = commasep[2].split()
        to_   = x[1][1:]+","+y[0]
        dist = int(y[1])
        if dist == None: 
           print "bad distance"
           return None

        return [pickupdate,from_,to_,dist]

    def parseSubject(self,line,commasep):
        """deprecated"""
        #_ftd         = set()
        if line[1] != "PU:": return -1
        date = line[2]
        dow=datetime.datetime.strptime(date,"%m/%d/%Y").strftime('%a')
        pickuptime = line[3]
        # this will be split into 4
        # find last digit (of time HH:MM) in order to
        # isolate the from location
        numindex = -1
        for i,c in enumerate(commasep[0]):
             if c.isdigit(): numindex = i+2  #skip the space
        if numindex == -1:
           print "error on %s"%l
           return -1

        # need to get from state abbrev from the next token
        x = commasep[1].split("to")
        from_ = commasep[0][numindex:]+","+x[0]
        # need to get to state abbrev from the next token
        y = commasep[2].split()
        to_   = x[1][1:]+","+y[0]
        dist = int(y[1])
        if dist == None: 
           raise Exception,"bad distance"
        #ft = (from_, to_)
        #z = (from_,to_,date+pickuptime)
        #if z not in _ftd:
        #    _ftd.add(z)
            #self._fromto.append(ft)
        if self._received != None:
            #rx = datetime.datetime(*self._received[:6]).isoformat()
            rx = time.strftime("%m/%d/%Y", self._received)
            rxtime = time.strftime("%H:%M", self._received)
            rxdow = time.strftime("%a", self._received)
        else: 
            rx = "Unknown"
        # automatically remove duplicates
        self._record.add((date,dow,pickuptime,from_,to_,dist,rx,rxdow,rxtime))
        return 1



    # email.utils.parsedate always returns 0 for day of week.
    # This is a feature. See https://docs.python.org/3/library/email.util.html
    # "Note that indexes 6, 7, and 8 of the result tuple are not usable."
    def _fix_struct_time(self,day):
        """deprecated"""
        if day == "Mon": return 0
        if day == "Tue": return 1
        if day == "Wed": return 2
        if day == "Thu": return 3
        if day == "Fri": return 4
        if day == "Sat": return 5
        if day == "Sun": return 6
        return -1

    def parseDateToPandas(self,line):
        return pd.to_datetime(line)

    def parseDate(self,line):
        """deprecated"""
        #print line
        t = eu.parsedate(line)
        # tuple are immutable, so convert to list, fix, and convert back
        b = list(t)
        b[6] = self._fix_struct_time(line[1:4])
        t = tuple(b)
        return t;

    def dataframe(self):
        """deprecated"""
        if self._dataframe is None:
            self._dataframe = pd.DataFrame([x for x in self._record],columns=['Pickup Date','Pickup Day','Pickup Time','From','To','Dist','Rcv Date', 'Rcv Day', 'Rcv Time'])
        return self._dataframe

    

    def mostCommon(self,num=5):
        """deprecated"""
        fromto = [(val[3],val[4]) for val in self._record]
        c = Counter(fromto)
        return c.most_common(num)

    def summarizeMostCommon(self,num=5):
        """deprecated"""
        c = self.mostCommon(num)
        if False:
            pickupdates = [val[6] for val in self._record]
            sd = sorted(pickupdates)
            print "%d Pickups, Date Coverage: %s to %s\n" % (len(sd),sd[0],sd[-1])
        print "%d Most Common Trips:" % (num)
        for p in c:
           print "%15s to %15s - %3d trips" % ( p[0][0], p[0][1],p[1])

    def longerThan(self,distance=300):
        df = self._dataframe
        return df[df.Dist>distance].sort_values(by=['Dist'],ascending=False)

    def dfmostCommonSeries(self,num=5):
        """Return pandas Series with most common trips sorted by number of repeats (descending)"""
        ft = self._dataframe.groupby(['From','To'],sort=False)
        print type(ft)
        s=ft.size().sort_values(0,ascending=False)
        s.name="%d Most Common Trips"%num
        return s.head(num)
        #print s.nlargest(num)  #same result

    def dfMostCommon(self,num=5):
        """Return most common trips sorted by number of repeats (descending)"""
        ft = self._dataframe.groupby(['From','To'],sort=False)
        return sorted(ft,key=lambda x:len(x[1]),reverse=True)[0:num]

    def listMostCommon(self,num=5):
        """DEPRECATED List most common trips sorted by number of repeats (descending)"""
        c = self.mostCommon(num)
        print "\nRCV-DATE   RCV-DAY RCV-TIME  PU-DATE    PU-DAY PU-TIME     FROM              TO         LDD"
        for p in c:
            thisrecord = dict()
            for r in self._record:
                if (r[3],r[4]) == p[0]:
                   thisrecord[r[0]] = r
            for k in sorted(thisrecord):
                z = thisrecord[k]
                print("%10s %5s %7s %12s %5s %7s %15s %15s %6s"%(z[6],z[7],z[8],k,z[1],z[2],z[3],z[4], z[5]))

    def search(self,column,expr,casesensitive=False):
        """Find string expr in column"""
        if not casesensitive: match = expr.upper()
        else:                 match = expr
        df = self._dataframe
        return df[df[column].str.contains(item)]

    # wrong. this will return the entire column
    #def searchLocation(self,location):
    #    """Find From or To that matches location"""
    #    return self.dataframe().filter(like=location)

    def searchFromOrTo(self,location):
        """Find From or To that matches location"""
        f=self.search('From',location,False)
        t=self.search('To',location,False)
        return pd.concat([f,t])

    def searchFrom(self,location):
        """Find From that matches location"""
        return self.search('From',location,False)

    def searchTo(self,location):
        """Find To that matches location"""
        return self.search('To',location,False)

    #def searchDate(self,daterange):


#############################################################################
def save(obj):
    pickle.dump(obj,open('mikedata.pickle','wb'))

def load():
    return pickle.load(open('mikedata.pickle','rb'))

#############################################################################
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process Fedex Pickup data.')
    #parser.add_argument('-c','--custom',help='use custom format instead of pandas',action="store_true")
    parser.add_argument('-s','--save',help='save the data in a pickle (will overwrite old data)',action="store_true")
    parser.add_argument('-l','--load',help='load previous data from a pickle',action="store_true")
    parser.add_argument('filename',metavar='input_file',help='input file name (output of grep -E "^Date|^Subject" MBOX)')
    args = parser.parse_args()
    if args.load:
        dataparser = load()
        dataparser._filename = args.filename
    else:
        dataparser = MikeDataParser(args.filename)

    dataparser.readlines()
    #if False: dataparser.listMostCommon(5)
    #if args.custom:
    #    dataparser.listMostCommon(5)
    #    dataparser.summarizeMostCommon(5)
    #else:
    #print dataparser.dfmostCommon(5)
    x=dataparser.dfMostCommon(5)
    for i in x:
       s=i[1].sort_values(by=['Pickup Date'])
       print s.to_string(index=False)
    #print dataparser.longerThan(1500).to_string(index=False)
    #print dataparser.longerThan(1500).to_html(index=False)

    if args.save: 
        save(dataparser)
