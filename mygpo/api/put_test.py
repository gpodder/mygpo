import sys
import httplib
import base64
import time

def put_data(dev_uid, format, data, username, password):
    cmd = '/subscriptions/%s/%d.%s' % (username, dev_uid, format)
    connection = httplib.HTTPConnection('127.0.0.1:8000')
    headers = {}
    headers['Authorization'] = ' '.join(('Basic', base64.encodestring(':'.join((username, password)))))
    connection.request('PUT', cmd, data, headers)
    response = connection.getresponse()
    print response.read()
    connection.close()

def get_data(dev_uid, format, username, password):
    data = None
    cmd = '/subscriptions/%s/%d.%s' % (username, dev_uid, format)
    connection = httplib.HTTPConnection('127.0.0.1:8000')
    headers = {}
    headers['Authorization'] = ' '.join(('Basic', base64.encodestring(':'.join((username, password)))))
    connection.request('GET', cmd, data, headers)
    response = connection.getresponse()
    print response.read()
    connection.close()
    
if __name__ == "__main__":
    u = 'ale'
    p = 'ale'
    p1 = 'http://www.podcast1.com'
    p2 = 'http://www.podcast2.com'
    p3 = 'http://www.podcast3.com'
    p4 = 'http://www.podcast4.com'
    data_txt_1 = '%s\n%s\n\n' % (p1, p2)
    data_txt_2 = '%s\n%s\n\n' % (p2, p3)
    data_txt_3 = '%s\n%s\n%s\n\n' % (p1, p3, p4)
    d1 = 1
    print 'put %s and %s on device %d' % (p1, p2, d1)
    put_data(d1, 'txt', data_txt_1, u, p)
    print 'get subscriptions'
    get_data(d1, 'txt', u, p)
    time.sleep(2)
    print 'put %s and %s on device %d' % (p2, p3, d1)
    put_data(d1, 'txt', data_txt_2, u, p)
    print 'get subscriptions'
    get_data(d1, 'txt', u, p)
    time.sleep(2)
    print 'put %s, %s and %s on device %d' % (p1, p3, p4, d1)
    put_data(d1, 'txt', data_txt_3, u, p)
    print 'get subscriptions'
    get_data(d1, 'txt', u, p)
