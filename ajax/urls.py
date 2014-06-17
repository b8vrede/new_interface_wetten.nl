from django.conf.urls import patterns, url
from django.shortcuts import redirect
from ajax import views

urlpatterns = patterns('',
    url(r'^$', ajax.default, name='default'),
)