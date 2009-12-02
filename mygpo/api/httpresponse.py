from django.http import HttpResponse

def HttpResponseNotAuthorized():
    response =  HttpResponse(('You\'re not authorized to visit this area!'), mimetype="text/plain")
    response['WWW-Authenticate'] = 'Basic realm=""'
    response.status_code = 401
    return response

