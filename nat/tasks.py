from __future__ import absolute_import

from nat.celery import app
import urllib2
from io import StringIO
import redis
from lxml import etree
import re
import sys

@app.task
def _all_titles():
    red = redis.StrictRedis(host='localhost', port=6379, db=1)
    parser = etree.HTMLParser()
    url = 'http://en.wikipedia.org/wiki/List_of_Xbox_360_games'
    response = urllib2.urlopen(url)
    html = response.read()
    html = html.decode('utf-8')
    tree = etree.parse(StringIO(html), parser)
    root = tree.getroot()
    anchors = root.xpath('//div[@id="mw-content-text"]/table/tr/td/i/a')
    names = [a.text.strip() for a in anchors]

    for name in sorted(names, key=lambda s : s.lower()):
        for n in range(1,len(name)):
            sys.stderr.write( name[:n], "\n")
            red.zadd('xbox_titles', 0, name[:n])
        sys.stderr.write( "%s%s" % (name, "|"), "\n")
        red.zadd('xbox_titles', 0, "%s%s" % (name, "|"))

@app.task
def titles():
    _all_titles.apply_async((),link_error=error_handler.s(), countdown=5)
        #countdown=60*60*24*7


@app.task
def error_handler(uuid):
    result = AsyncResult(uuid)
    exc = result.get(propagate=False)
    print('Task {0} raised exception: {1!r}\n{2!r}'.format(
          uuid, exc, result.traceback))
