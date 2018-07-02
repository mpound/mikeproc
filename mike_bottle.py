#!/algol2/mpound/anaconda3/bin/python
import bottle
from bottle import get, post, request, template
import mike 
import pandas

js_str = '''\
<!-- Include jQuery -->
<!-- Include Date Range Picker -->
<!--
<script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap-datepicker/1.4.1/js/bootstrap-datepicker.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap-datepicker/1.4.1/css/bootstrap-datepicker3.css"/>
-->
<script type="text/javascript" src="https://code.jquery.com/jquery-1.12.4.min.js"></script>
  <script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/moment.js/2.15.1/moment.min.js"></script>
  <script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap-datetimepicker/4.17.43/js/bootstrap-datetimepicker.min.js"></script>
<script>
    $(document).ready(function(){
        //var fromdate_input=$('input[name="datefrom"]'); 
        //var container=$('.bootstrap-iso form').length>0 ? $('.bootstrap-iso form').parent() : "body";
        //fromdate_input.datepicker({
            //format: 'mm/dd/yyyy',
            //container: container,
        //    todayHighlight: true,
        //    autoclose: true,
        //})
        //var todate_input=$('input[name="dateto"]'); 
        //var container=$('.bootstrap-iso form').length>0 ? $('.bootstrap-iso form').parent() : "body";
        //todate_input.datepicker({
            //format: 'mm/dd/yyyy hh:mm',
            //container: container,
         //   todayHighlight: true,
          //  autoclose: true,
        //})
        $('#pickerfrom').datetimepicker();
        $('#pickerto').datetimepicker();
    })
</script>'''

form_str = '''\
  <head>
    <meta http-equiv="content-type" content="text/html; charset=UTF-8">
    <meta charset="utf-8">
    <title>Form</title>
<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u" crossorigin="anonymous"> 
<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css">

  <link rel="stylesheet" type="text/css" href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap-datetimepicker/4.17.43/css/bootstrap-datetimepicker.min.css"> 

  </head>
  <body>
    <div class="container">
    <br>
    <h1>Search the email database</h1>
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
            <input name="distanceradio" type="radio" required="required" class="custom-control-input" value=">="> 
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
            <input name="datetimeradio" type="radio" required="required" class="custom-control-input" value="Pickup Date"> 
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
         <span id="datefromHelpBlock" class="form-text text-muted">&nbsp;click on icon to input date &amp; time Leave blank to indicate earliest possible date</span>
        </div>
      </div>
      <div class="form-group row">
        <label for="dateto" class="col-xs-2 col-form-label">To</label> 
        <div class="col-xs-6">
         <div class="input-group date" id="pickerto">
          <input id="dateto" name="dateto" type="text" class="form-control here" aria-describedby="datetoHelpBlock">
          <div class="input-group-addon append"> <i class="fa fa-calendar"></i> </div>
         </div>
          <span id="datetoHelpBlock" class="form-text text-muted">&nbsp;click on icon to input date &amp; time. Leave blank to indicate "now."</span>
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
<!-- Include jQuery -->
<!-- Include Date Range Picker -->
<!--
<script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap-datepicker/1.4.1/js/bootstrap-datepicker.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap-datepicker/1.4.1/css/bootstrap-datepicker3.css"/>
-->
<script type="text/javascript" src="https://code.jquery.com/jquery-1.12.4.min.js"></script>
  <script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/moment.js/2.15.1/moment.min.js"></script>
  <script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap-datetimepicker/4.17.43/js/bootstrap-datetimepicker.min.js"></script>
<script>
    $(document).ready(function(){
        //var fromdate_input=$('input[name="datefrom"]'); 
        //var container=$('.bootstrap-iso form').length>0 ? $('.bootstrap-iso form').parent() : "body";
        //fromdate_input.datepicker({
            //format: 'mm/dd/yyyy',
            //container: container,
        //    todayHighlight: true,
        //    autoclose: true,
        //})
        //var todate_input=$('input[name="dateto"]'); 
        //var container=$('.bootstrap-iso form').length>0 ? $('.bootstrap-iso form').parent() : "body";
        //todate_input.datepicker({
            //format: 'mm/dd/yyyy hh:mm',
            //container: container,
         //   todayHighlight: true,
          //  autoclose: true,
        //})
        $('#pickerfrom').datetimepicker();
        $('#pickerto').datetimepicker();
    })
</script>
'''

@get('/my_form')
def show_form():
    return "<html>"+form_str+"</body><html>"

@post('/my_form')
def process_form():
    xxxx = "{} ".format(request.POST.distanceradio) +"select {} ".format(request.POST.selecttype) +"# {} ".format(request.POST.numresults) +"LDD {} ".format(request.POST.distance) +"PU {} ".format(request.POST.pickupcity) +"END {} ".format(request.POST.endcity) +"D/T {} ".format(request.POST.datetimeradio) +"DATEFROM {} ".format(request.POST.datefrom) +"DATETO {} ".format(request.POST.dateto)

    filter_mask= dict.fromkeys(mike.columns(),None)
    filter_mask["Distance"] = request.POST.distanceradio+request.POST.Distance
    filter_mask["From"]     = request.POST.pickupcity.upper()
    filter_mask["To"]       = request.POST.endcity.upper()
    filter_mask[ request.POST.datetimeradio ] = [request.POST.datefrom,request.POST.dateto]
    
    fname = "m2"
    dataparser = mike.load()
    if dataparser != None:
        dataparser._filename = fname
    else:
        dataparser = mike.MikeDataParser(fname)
    dataparser.readlines()
    mike.save(dataparser)
    filtered_df = dataparser.filter(filter_mask)
    nr = int(request.POST.numresults)
    dataparser._dataframe = filtered_df
    if request.POST.selecttype == "mostcommon":
        x=dataparser.mostCommon2(nr).to_html()
    if request.POST.selecttype == "mostrecent":
        x=dataparser.mostRecent(nr).to_html()
    if request.POST.selecttype == "all":
        x=dataparser.dataframe().sort_values(by=['Pickup Date']).to_html()
    newx=x.replace('<table','<table class="table"')
    return "<html>"+form_str+"<br><br>"+newx+"</body><html>"
    


#self._dataframe  = pd.DataFrame.from_records(record,columns=['Received Date','Pickup Date','From','To','Distance'])


application=bottle.default_app()       # run in a WSGI server
bottle.run(host='localhost', port=8080) # run in a local test server
