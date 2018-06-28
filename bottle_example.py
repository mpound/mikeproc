#!/algol2/mpound/anaconda3/bin/python
import bottle
from bottle import get, post, request

@get('/my_form')
def show_form():
    return '''\
<form action="" method="POST">
    <label for="name">What is your name?</label>
    <input type="text" name="name"/>
    <input type="submit"/>
</form>'''

@post('/my_form')
def show_name():
    return "Hello, {}!".format(request.POST.name)

application=bottle.default_app()       # run in a WSGI server
bottle.run(host='localhost', port=8080) # run in a local test server
