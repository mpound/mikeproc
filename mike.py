#!/usr/bin/env python
# grep ^Subject MIKE\ DATA.mbox > m1
# grep -E "^Date|^Subject" MIKE\ DATA.mbox > m2

# @TODO 
#       Make searchable web page. (all fields, date range)
#       
import argparse
import time
import pickle
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

    def parseDateToPandas(self,line):
        return pd.to_datetime(line)

    def longerThan(self,distance=300):
        """Return trips longer than distance"""
        df = self._dataframe
        return df[df.Dist>distance].sort_values(by=['Dist'],ascending=False)

    def mostCommonSeries(self,num=5):
        """Return pandas Series with most common trips sorted by number of repeats (descending)"""
        ft = self._dataframe.groupby(['From','To'],sort=False)
        print type(ft)
        s=ft.size().sort_values(0,ascending=False)
        s.name="%d Most Common Trips"%num
        return s.head(num)
        #print s.nlargest(num)  #same result

    def mostCommon(self,num=5):
        """Return most common trips sorted by number of repeats (descending)"""
        ft = self._dataframe.groupby(['From','To'],sort=False)
        return sorted(ft,key=lambda x:len(x[1]),reverse=True)[0:num]

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
    x=dataparser.mostCommon(5)
    for i in x:
       s=i[1].sort_values(by=['Pickup Date'])
       print s.to_string(index=False)
    #print dataparser.longerThan(1500).to_string(index=False)
    #print dataparser.longerThan(1500).to_html(index=False)

    if args.save: 
        save(dataparser)
