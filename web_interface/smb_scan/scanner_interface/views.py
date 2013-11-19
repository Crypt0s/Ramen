# Create your views here.
from django.http import HttpResponse
from django.template import RequestContext,loader
from django.shortcuts import render
import struct,socket,pdb
from scanner_interface.models import *

def index(request):
    # Get all the types of permissions in the permissions table so we can filter on them later.
    permission_types = [x.values()[0] for x in Permissions.objects.values('permission').distinct()]

    # Template rendering code
    template = loader.get_template('scanner_interface/index.html')
    context = RequestContext(request,{
        'permission_types':permission_types,
    })
    return HttpResponse(template.render(context))
#        'filenum':len(Files.objects.all()),
#        'usernum':len(Users.objects.all()),
#        'permissionnum':len(Permissions.objects.all()),
#        'sharenum':len(Shares.objects.all()),

def search(request):
    print 'hii'
    try:
        if request.POST['location'] is not u'':
            print "Location specced"
            # Comma support
            if ',' in request.POST['location']:
                locations = request.POST['location'].split(',')
                lids = [x.lid for x in Shares.objects.filter(server__in=locations)]

            # Netblock declaration support
            elif '/' in request.POST['location']:
                network = request.POST['location'].split('/')[0]
                hosts = request.POST['location'].split('/')[1]
                locations = []
                for i in xrange((2**(32-int(hosts)))):
                    locations.append(socket.inet_ntoa(struct.pack('!I',struct.unpack('!I', socket.inet_aton(network))[0]+i)))
                lids = [x.lid for x in Shares.objects.filter(server__in=locations)]

            elif chr(92) in request.POST['location']:
                print "OK I see your share."
            # Todo -- add support (with above) for naming a specific share as well - that'd be nice :)
            # Regular IP Address support
            else:
                lids = [x.lid for x in Shares.objects.filter(server__exact=request.POST['location'])]
            results = Files.objects.filter(filename__iregex=request.POST['filename'],lid__in=lids)
            print "Results1 : " + str(len(results))
        # No location spec'd
        else:
            results = Files.objects.filter(filename__iregex=request.POST['filename'])
            print "Results2 : " + str(len(results))

        if request.POST['username'] is not u'': #!= [u'']: #t.POST['username'] != u'':
            results = results.filter(permissions__uid__in=Users.objects.filter(username__iregex=request.POST['username']))
            print "Results3 : " + str(len(results))
        else:
            pass        
        
        print "Results4 : " + str(len(results))

        result_combo=[]
        for result in results:

            result.filename = chr(92)*2 + chr(92).join(result.filename.split('/')[3:])

            if request.POST['username'] != [u'']:
                users = Users.objects.filter(permissions__fid__exact=result.fid,username__iregex=request.POST['username'])
            else:
                users = Users.objects.filter(permissions__fid__exact=result.fid)

            perm_list = []
            for user in users:
                if 'permissions' in request.POST.keys():
                    perms = Permissions.objects.filter(fid__exact=result.fid,uid__exact=user.uid,permission__in=request.POST.getlist('permissions'))
                else:
                    perms = Permissions.objects.filter(fid__exact=result.fid,uid__exact=user.uid)
                for perm in perms:
                    perm_list.append((user,perm))
            result_combo.append((result,perm_list))


        #     [
        #    (Filename, [
        #               (user,permission),(user,permission),(user,permission)
        #                ])
        #     ]
        results = result_combo
        print "Results5 : " + str(len(results))

    except (KeyError):
        permission_types = [x.values()[0] for x in Permissions.objects.values('permission').distinct()]
        # If the POST was missing something, indicate an error on return page
        return render(request,'scanner_interface/results.html',{
            'err':1,
            'err_message':'missing a search parameter that is required',
            'request':request.POST,
            'permission_types':permission_types,
        })

    # We made it -- display the results
    #result_len = len(results)    
    template = loader.get_template('scanner_interface/results.html')
    context = RequestContext(request,{
        #'result_len':result_len,
        'results':results,
        'request':request.POST,
    })
    return HttpResponse(template.render(context))

def atesturl(request,testquery):
    template = loader.get_template('scanner_interface/index.html')
    context = RequestContext(request,{
        'testquery':testquery,
    })
    return HttpResponse(template.render(context))
