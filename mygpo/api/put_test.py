import sys
import httplib
import base64

def put_data(dev_uid, format, data, username, password):
    cmd = '/subscriptions/%s/%d.%s' % (username, dev_uid, format)
    connection = httplib.HTTPConnection('127.0.0.1:8000')
    headers = {}
    headers['Authorization'] = ' '.join(('Basic', base64.encodestring(':'.join((username, password)))))
    connection.request('PUT', cmd, data, headers)
    response = connection.getresponse()
    #print response.read()
    connection.close()
