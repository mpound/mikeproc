import sys
import os
import bottle
from bottle import get, post, request, template
###
 
# grep ^Subject MIKE\ DATA.mbox > m1
# grep -E "^Date|^Subject" MIKE\ DATA.mbox > m2
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

directory = "/var/www/html/mikeproc/"
#############################################################################
def save(obj):
    myfile=directory+"mikedata.pickle"
    pickle.dump(obj,open(myfile,'wb'))

def load():
    myfile=directory+"mikedata.pickle"
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
        # note there seem to be some test entries 
        # from PU CITY, ST to DEL CITY, ST with zero distance
        if dist == None or dist < 1: 
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
        #print(type(ft))
        s=ft.size().sort_values(0,ascending=False)
        s.name="%d Most Common Trips"%num
        return s.head(num)
        #print s.nlargest(num)  #same result

    def mostCommonOldVersion(self,num=5):
        """Return most common trips sorted by number of repeats (descending)"""
        ft = self._dataframe.groupby(['From','To'],sort=False)
        return sorted(ft,key=lambda x:len(x[1]),reverse=True)[0:num]

    def mostCommon(self,num=5):
        """Return most common trips sorted by number of repeats (descending)"""
        df = self._dataframe
        df = df.assign(Frequency=df.groupby(['From','To'],sort=False)['From'].transform('count')).sort_values(by=['Frequency','From'],ascending=[False,True])
        # now remove columns so that we have From,To,Distance, Frequency
        df.drop(columns=['Received Date','Pickup Date'],inplace=True)
        df.drop_duplicates(inplace=True)
        df.sort_values(by=['Frequency'],ascending=False,inplace=True)

        #  NOT NEEDED!
        # regroup by frequency to flatten common from,to
        #s = df.groupby(['Frequency','From','To'],sort=False)
        # s.size() returns a Series, change it back to a DataFrame
        # This is not an optimal representation so handcraft a DataFrame instead
        #df = s.size().to_frame()
        #xdf = pd.DataFrame(columns=['Frequency','From','To','Distance'])
        return df.head(num)

    def grab(self,mask,num):
        if mask == "mostcommon":
           return self.mostCommon(num)
        if mask == "mostrecent":
           return self.mostRecent(num)


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
           if filter_mask[datestr][0] == None or filter_mask[datestr][0]=='':
              filter_mask[datestr][0] = pd.to_datetime("2018-01-01")
           if filter_mask[datestr][1] or filter_mask[datestr][1]== '':
              filter_mask[datestr][1] = pd.to_datetime('now')
           cond2 = df[datestr].between(filter_mask[datestr][0],filter_mask[datestr][1])
           df=df[cond2]
           #print("DATES: %s %s"%(filter_mask[datestr][0],filter_mask[datestr][1]))
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
###

htmlhead_str='''\
  <head>
    <meta http-equiv="content-type" content="text/html; charset=UTF-8">
    <meta charset="utf-8">
    <title>Mike Database Search</title>
<link rel="stylesheet" type="text/css" href="https://datatables.net/media/css/site-examples.css">
<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css">
<link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.10.19/css/dataTables.bootstrap.min.css">
<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css">

<link rel="stylesheet" type="text/css" href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap-datetimepicker/4.17.43/css/bootstrap-datetimepicker.min.css"> 
  </head>
'''

javascript_str = '''\
<!-- Include jQuery -->
<!-- Include Date Range Picker -->
<script type="text/javascript" src="https://code.jquery.com/jquery-3.3.1.min.js"></script>
<script type="text/javascript" src="https://cdn.datatables.net/1.10.19/js/jquery.dataTables.min.js"></script>
<script type="text/javascript" src="https://cdn.datatables.net/1.10.19/js/dataTables.bootstrap.min.js"></script>
<script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/moment.js/2.15.1/moment.min.js"></script>
<script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap-datetimepicker/4.17.43/js/bootstrap-datetimepicker.min.js"></script>
<script>
    $(document).ready(function(){
        $('#mostcommontable').DataTable({
             "pagingType": "full_numbers",
             "order": [[3,'desc']],
             "ordering": true,
             "info": true
        });
        $('#mostrecenttable').DataTable({
             "pagingType": "full_numbers",
             "order": [[0,'desc']],
             "ordering": true,
             "info": true
        });
        $('#alltable').DataTable({
             "pagingType": "full_numbers",
             "order": [[1,'asc']],
             "ordering": true,
             "info": true
        });
        $('#defaulttable').DataTable({
             "pagingType": "full_numbers",
             "order": [[0,'asc']],
             "ordering": true,
             "info": true
        });
        $('#pickerfrom').datetimepicker();
        $('#pickerto').datetimepicker();
    })
</script>'''

form_str = '''\
    <div class="container">
    <br>
    <h1>Search the Pickup/Delivery database</h1>
    <hr>
    <form method="post" class="form-horizontal" action="">
      <div class="form-group row">
        <label for="selecttype" class="col-xs-2">Show  the</label> 
        <div class="col-xs-3">
          <select id="selecttype" name="selecttype" required="required" class="custom-select">
            <option value="mostcommon">most common</option>
            <option value="mostrecent">most recent</option>
            <option value="all">all</option>
          </select>
        </div>
      <!-- </div> 
      <div class="form-grouprow">
-->
        <div class="col-xs-4">
          <div class="input-group">
            <input id="numresults" name="numresults" value="10" type="text" required="required" class="form-control here"  aria-describedby="numresultsHelpBlock"> 
            <div class="input-group-addon append">trips</div>
          </div>
          <span id="numresultsHelpBlock" class="form-text text-muted">ignored if selection is "all"</span>
        </div>
      </div>
      <div class="form-group row">
        <label class="col-xs-3">with Load Distance</label> 
        <div class="col-xs-3">
          <label class="custom-control custom-radio">
            <input name="distanceradio" type="radio" required="required" class="custom-control-input" value=">=" checked="checked"> 
            <span class="custom-control-indicator"></span> 
            <span class="custom-control-description">greater</span>
          </label>
          <label class="custom-control custom-radio">
            <input name="distanceradio" type="radio" required="required" class="custom-control-input" value="<"> 
            <span class="custom-control-indicator"></span> 
            <span class="custom-control-description">less</span>
          </label>
        </div>
<!--
      </div>
      <div class="form-group row">
        <label for="numresults" class="col-1 col-form-label">than</label> 
-->
        <div class="col-xs-4">
          <div class="input-group">
            <div class="input-group-addon prepend">than</div>
            <input id="Distance" name="Distance" required="required" value="500" type="text" class="form-control here"> 
            <div class="input-group-addon append">miles</div>
          </div>
        </div>
      </div>
      <div class="form-group row">
        <label for="pickupcity" class="col-xs-2 col-form-label">Pick-up city</label> 
        <div class="col-xs-8">
          <div class="input-group">
            <input id="pickupcity" name="pickupcity" type="text" aria-describedby="pickupcityHelpBlock" class="form-control here"> 
            <div class="input-group-addon append">(optional)</div>
          </div> 
          <span id="pickupcityHelpBlock" class="form-text text-muted">case-insensitive minimum match, e.g. "memph" will match Memphis</span>
        </div>
      </div>
      <div class="form-group row">
        <label for="endcity" class="col-xs-2 col-form-label">End city</label> 
        <div class="col-xs-8">
          <div class="input-group">
            <input id="endcity" name="endcity" type="text" aria-describedby="endcityHelpBlock" class="form-control here"> 
            <div class="input-group-addon append">(optional)</div>
          </div> 
          <span id="endcityHelpBlock" class="form-text text-muted">case-insensitive minimum match, e.g. "memph" will match Memphis</span>
        </div>
      </div>
      <div class="form-group row">
        <label class="col-xs-2">with</label> 
        <div class="col-xs-10">
          <label class="custom-control custom-radio">
            <input name="datetimeradio" type="radio" required="required" class="custom-control-input" value="Pickup Date" checked="checked"> 
            <span class="custom-control-indicator"></span> 
            <span class="custom-control-description">Pickup Date/Time</span>
          </label>
          <label class="custom-control custom-radio">
            <input name="datetimeradio" type="radio" required="required" class="custom-control-input" value="Received Date"> 
            <span class="custom-control-indicator"></span> 
            <span class="custom-control-description">Received Date/Time</span>
          </label>
        </div>
      </div>
<!--
      <div class="form-group row">
        <label for="datefrom" class="col-2 col-form-label">From</label> 
        <div class="col-6 input-group">
          <input id="datefrom" name="datefrom" type="text" class="form-control here">
          <div class="input-group-addon append"> <i class="fa fa-calendar"></i> </div>
        </div>
      </div>
      <div class="form-group row">
        <label for="dateto" class="col-2 col-form-label">To</label> 
        <div class="col-6 input-group">
          <input id="dateto" name="dateto" type="text" class="form-control here">
          <div class="input-group-addon append"> <i class="fa fa-calendar"></i> </div>
        </div>
      </div> 
-->
      <div class="form-group row">
        <label for="datefrom" class="col-xs-2 col-form-label">From</label> 
        <div class="col-xs-6">
         <div class="input-group date" id="pickerfrom">
          <input id="datefrom" name="datefrom" type="text" class="form-control here" aria-describedby="datefromHelpBlock">
          <div class="input-group-addon append"> <i class="fa fa-calendar"></i> </div>
         </div>
         <span id="datefromHelpBlock" class="form-text text-muted">&nbsp;Click on icon to input date &amp; time. Leave blank to indicate earliest possible date</span>
        </div>
      </div>
      <div class="form-group row">
        <label for="dateto" class="col-xs-2 col-form-label">To</label> 
        <div class="col-xs-6">
         <div class="input-group date" id="pickerto">
          <input id="dateto" name="dateto" type="text" class="form-control here" aria-describedby="datetoHelpBlock">
          <div class="input-group-addon append"> <i class="fa fa-calendar"></i> </div>
         </div>
          <span id="datetoHelpBlock" class="form-text text-muted">&nbsp;Click on icon to input date &amp; time. Leave blank to indicate "now."</span>
        </div>
      </div> 
      <div class="form-group row">
        <div class="offset-4 col-xs-8">
          <button name="submit" type="submit" class="btn btn-primary">Submit</button>
        </div>
      </div>
    </form>
    </div>
    <hr>
</form>
'''

@get('/')
def show_form():
    return "<html>"+htmlhead_str+"<body>"+form_str+javascript_str+"</body><html>"

@post('/')
def process_form():
    rawinputs = "{} ".format(request.POST.distanceradio) +"select {} ".format(request.POST.selecttype) +"# {} ".format(request.POST.numresults) +"LDD {} ".format(request.POST.distance) +"PU {} ".format(request.POST.pickupcity) +"END {} ".format(request.POST.endcity) +"D/T {} ".format(request.POST.datetimeradio) +"DATEFROM {} ".format(request.POST.datefrom) +"DATETO {} ".format(request.POST.dateto)

    filter_mask= dict.fromkeys(columns(),None)
    filter_mask["Distance"] = request.POST.distanceradio+request.POST.Distance
    filter_mask["From"]     = request.POST.pickupcity.upper()
    filter_mask["To"]       = request.POST.endcity.upper()
    filter_mask[ request.POST.datetimeradio ] = [request.POST.datefrom,request.POST.dateto]
    print(filter_mask)
    
    fname = directory+"m2"
    #dataparser = load()
    #if dataparser != None:
    #    dataparser._filename = fname
    #else:
    #    dataparser = MikeDataParser(fname)
    dataparser = MikeDataParser(fname)
    dataparser.readlines()
    save(dataparser)

    # html formatting for table returned from search
    tableclasses="table table-striped table-bordered"
    border="1"
    table_id="defaulttable"
    justify="left"
    index=False
    bold_rows=False
    # want Day name in the date display. Default is %Y-%m-%d %T
    # found example at https://github.com/pandas-dev/pandas/issues/10690
    # Note must put day at end or column sorting is incorrect
    formatters = {'Received Date': lambda x: x.strftime('%Y-%m-%d %T %a'),
                  'Pickup Date': lambda x: x.strftime('%Y-%m-%d %T %a')
                 }

    # this needs to be int rather than string
    nr = int(request.POST.numresults)

    # filter the table, then replace the original
    filtered_df = dataparser.filter(filter_mask)
    dataparser._dataframe = filtered_df

    if request.POST.selecttype == "mostcommon":
        table_id="mostcommontable"
        x=dataparser.mostCommon(nr).to_html(index=index,classes=tableclasses,table_id=table_id,border=border,justify=justify,bold_rows=bold_rows)
    if request.POST.selecttype == "mostrecent":
        table_id="mostrecenttable"
        x=dataparser.mostRecent(nr).to_html(index=index,classes=tableclasses,table_id=table_id,border=border,justify=justify,bold_rows=bold_rows,formatters=formatters)
    if request.POST.selecttype == "all":
        table_id="alltable"
        x=dataparser.dataframe().sort_values(by=['Pickup Date']).to_html(index=index,classes=tableclasses,table_id=table_id,border=border,justify=justify,bold_rows=bold_rows,formatters=formatters)

    return "<html>"+htmlhead_str+"\n<body>\n"+form_str+"\n<div class='container'>"+x+"</div>\n"+javascript_str+"</body><html>"
    

############################
# run in a WSGI server
############################
application=bottle.default_app()       
