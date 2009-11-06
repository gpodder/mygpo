# Create your views here.

def upload(request):
    emailaddr = request.GET['username']
    password  = request.GET['password']
    action    = request.GET['action']
    protocol  = request.GET['protocol']
    opml_file = request.FILES['opml']
    opml      = opml_file.read()
    
    user = UserAccount.objects.get(email__exact=emailaddr)
    if !user:
        #@AUTHFAIL
    
    if !user.check_password(password):
        #@AUTHFAIL

    #read podcasts


def getlist(request):
    emailaddr = request.GET['username']
    password  = request.GET['password']

    user = UserAccount.objects.get(email__exact=emailaddr)
    if !user:
        #@AUTHFAIL

    if !user.check_password(password):
        #@AUTHFAIL

    # build and send list

   
