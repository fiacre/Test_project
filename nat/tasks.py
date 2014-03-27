from __future__ import absolute_import

from nat.celery import app
import urllib2
from lxml.html import fromstring, tostring

@app.task
def add(x, y):
    return x + y


@app.task
def mul(x, y):
    return x * y


@app.task
def xsum(numbers):
    return sum(numbers)

@app.task
def all_titles():
    import redis
    r = redis.StrictRedis(host='localhost', port=6379, db=1)
    url = 'http://www.dmoz.org/Games/Video_Games/Console_Platforms/Microsoft/Xbox_360/Titles/'
    req = urllib2.urlopen(url)
    html = req.read()

    root = fromstring(html)
    set_name = "titles"
    for ref in root.iterlinks():
        r.sadd(set_name, ref[0].text_content())


