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

def get_data(dev_uid, format, username, password):
    data = ''
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
    p1 = 'http://www.podcast1.com\n'
    p2 = 'http://www.podcast2.com\n'
    p3 = 'http://www.podcast3.com\n'
    data_txt_1 = '%s\n%s\n' % (p1, p2)
    data_txt_2 = '%s\n%s\n' % (p2, p3)
    
    put_data(1, 'txt', data_txt_1, u, p)
    print "1.get"
    get_data(1, 'txt', u, p)
    put_data(1, 'txt', data_txt_2, u, p)
    print "2. get"
    get_data(1, 'json', u, p)
