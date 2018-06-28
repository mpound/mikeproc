#!/algol2/mpound/anaconda3/bin/python
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
from pathlib import Path

#Subject line possible from/to
#a,b to c,d
#a b,c to d,e
#a,b to c d, e
#a b,c to d e,f

#############################################################################
def save(obj):
    pickle.dump(obj,open('mikedata.pickle','wb'))

def load():
    myfile="mikedata.pickle"
    if Path(myfile).is_file():
        return pickle.load(open(myfile,'rb'))
    return None

def columns():
    return ['Received Date','Pickup Date','From','To','Distance']
#############################################################################

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

        self._dataframe  = pd.DataFrame.from_records(record,columns=columns())
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
           print("error on %s"%l)
           return None
        # need to get from state abbrev from the next token
        x = commasep[1].split("to")
        from_ = commasep[0][numindex:]+","+x[0]
        # need to get to state abbrev from the next token
        y = commasep[2].split()
        to_   = x[1][1:]+","+y[0]
        dist = int(y[1])
        if dist == None: 
           print("bad distance")
           return None

        return [pickupdate,from_.upper(),to_.upper(),dist]

    def parseDateToPandas(self,line):
        return pd.to_datetime(line)

    def longerThan(self,distance=300):
        """Return trips longer than distance, longest first"""
        df = self._dataframe
        return df[df.Dist>distance].sort_values(by=['Dist'],ascending=False)

    def shorterThan(self,distance=300):
        """Return trips shorter than distance, shortest first"""
        df = self._dataframe
        return df[df.Dist<distance].sort_values(by=['Dist'],ascending=True)

    def mostCommonSeries(self,num=5):
        """Return pandas Series with most common trips sorted by number of repeats (descending)"""
        ft = self._dataframe.groupby(['From','To'],sort=False)
        print(type(ft))
        s=ft.size().sort_values(0,ascending=False)
        s.name="%d Most Common Trips"%num
        return s.head(num)
        #print s.nlargest(num)  #same result

    def grab(self,mask,num):
        if mask == "mostcommon":
           return self.mostCommon(num)
        if mask == "mostrecent":
           return self.mostRecent(num)

    def mostCommon(self,num=5):
        """Return most common trips sorted by number of repeats (descending)"""
        ft = self._dataframe.groupby(['From','To'],sort=False)
        return sorted(ft,key=lambda x:len(x[1]),reverse=True)[0:num]

    def mostCommon2(self,num=5):
        """Return most common trips sorted by number of repeats (descending)"""
        df = self._dataframe
        df.assign(freq=df.groupby(['From','To'],sort=False)['From'].transform('count')).sort_values(by=['freq','From'],ascending=[False,True])
        return df[0:num]

    def dataframe(self):
        return self._dataframe

    def to_html(self):
        return self._dataframe.to_html()

    def mostRecent(self,num=5):
        """Return most recent (Pickup Date) trips sorted by most recent first"""
        return self._dataframe.sort_values(by=['Pickup Date'],ascending=False)[0:num]

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

    #['Received Date','Pickup Date','From','To','Distance']
    def filter(self,filter_mask):
       df = self._dataframe
       if filter_mask['Distance']!=None:
          df=df.query('Distance'+filter_mask['Distance'])
       if filter_mask["Received Date"] != None:
          datestr = "Received Date"
       elif filter_mask["Pickup Date"] != None:
          datestr = "Pickup Date"
       else:
          datestr=None
       if datestr != None:
           if filter_mask[datestr][0] == None:
              filter_mask[datestr][0] = pandas.to_datetime("2018-01-01")
           if filter_mask[datestr][1] == None:
              filter_mask[datestr][1] = pandas.to_datetime('now')
           cond2 = df[datestr].between(filter_mask[datestr][0],filter_mask[datestr][1])
           df=df[cond2]
       if filter_mask["From"] != None:
           df=df[df["From"].str.contains(filter_mask["From"])]
       if filter_mask["To"] != None:
           df=df[df["To"].str.contains(filter_mask["To"])]
       return df


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
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process Fedex Pickup data.')
    parser.add_argument('-s','--save',help='save the data in a pickle (will overwrite old data)',action="store_true")
    parser.add_argument('-l','--load',help='load previous data from a pickle',action="store_true")
    parser.add_argument('filename',metavar='input_file',help='input file name (output of grep -E "^Date|^Subject" MBOX)')
    args = parser.parse_args()
    if args.load:
        dataparser = load()
        if dataparser != None:
            dataparser._filename = args.filename
        else:
            dataparser = MikeDataParser(args.filename)
    else:
        dataparser = MikeDataParser(args.filename)

    dataparser.readlines()
    x=dataparser.mostCommon(5)
    for i in x:
       s=i[1].sort_values(by=['Pickup Date'])
       print(s.to_string(index=False))
    #print dataparser.longerThan(1500).to_string(index=False)
    #print dataparser.longerThan(1500).to_html(index=False)

    if args.save: 
        save(dataparser)
