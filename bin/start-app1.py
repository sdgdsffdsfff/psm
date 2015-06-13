import urllib2
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def start_app1():
    apps = json.loads(urllib2.urlopen('http://172.17.100.13:8080/v2/apps').read())
    for app in apps['apps']:
        if '/app1' == app['id']:
            return
    res = urllib2.urlopen('http://172.17.100.13:8080/v2/apps', data=json.dumps({
        'id': 'app1',
        'cmd': 'python %s/app/app1.py' % BASE_DIR
    })).read()
    print(res)

start_app1()