#!/algol2/mpound/anaconda3/bin/python
import bottle
from bottle import get, post, request, template
import mike 
import pandas

import os
# Change working directory so relative paths (and template lookup) work again
os.chdir(os.path.dirname(__file__))
 

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
             "order": [[0,'asc']],
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

@get('/my_form')
def show_form():
    return "<html>"+htmlhead_str+"<body>"+form_str+javascript_str+"</body><html>"

@post('/my_form')
def process_form():
    rawinputs = "{} ".format(request.POST.distanceradio) +"select {} ".format(request.POST.selecttype) +"# {} ".format(request.POST.numresults) +"LDD {} ".format(request.POST.distance) +"PU {} ".format(request.POST.pickupcity) +"END {} ".format(request.POST.endcity) +"D/T {} ".format(request.POST.datetimeradio) +"DATEFROM {} ".format(request.POST.datefrom) +"DATETO {} ".format(request.POST.dateto)

    filter_mask= dict.fromkeys(mike.columns(),None)
    filter_mask["Distance"] = request.POST.distanceradio+request.POST.Distance
    filter_mask["From"]     = request.POST.pickupcity.upper()
    filter_mask["To"]       = request.POST.endcity.upper()
    filter_mask[ request.POST.datetimeradio ] = [request.POST.datefrom,request.POST.dateto]
    print(filter_mask)
    
    fname = "m2"
    dataparser = mike.load()
    if dataparser != None:
        dataparser._filename = fname
    else:
        dataparser = mike.MikeDataParser(fname)
    dataparser.readlines()
    mike.save(dataparser)

    # html formatting for table returned from search
    tableclasses="table table-striped table-bordered"
    border="1"
    table_id="defaulttable"
    justify="left"
    index=False
    bold_rows=False

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
        x=dataparser.mostRecent(nr).to_html(index=index,classes=tableclasses,table_id=table_id,border=border,justify=justify,bold_rows=bold_rows)
    if request.POST.selecttype == "all":
        table_id="alltable"
        x=dataparser.dataframe().sort_values(by=['Pickup Date']).to_html(index=index,classes=tableclasses,table_id=table_id,border=border,justify=justify,bold_rows=bold_rows)

    return "<html>"+htmlhead_str+"\n<body>\n"+form_str+"\n<div class='container'>"+x+"</div>\n"+javascript_str+"</body><html>"
    

# run in a WSGI server
application=bottle.default_app()       
