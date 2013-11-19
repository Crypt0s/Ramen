from django.conf.urls import patterns, url

from scanner_interface import views

urlpatterns = patterns('',
    url(r'^$',views.index,name='index'),
    url(r'^search$',views.search,name='search'),
    url(r'^(?P<testquery>\w+)$',views.atesturl,name='atesturl'),
)
