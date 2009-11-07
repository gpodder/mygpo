# Create your views here.

def upload(request):
    action    = request.GET['action']
    protocol  = request.GET['protocol']
    opml_file = request.FILES['opml']
    opml      = opml_file.read()
    
    if !auth(request):
        #@AUTHFAIL
    
    #read podcasts


def getlist(request):
    if !auth(request):
        #@AUTHFAIL

    # build and send list


def auth(request):
    emailaddr = request.GET['username']
    password  = request.GET['password']

    user = UserAccount.objects.get(email__exact=emailaddr)
    if !user:
        return false

    if !user.check_password(password):
        return false
    
    return user

