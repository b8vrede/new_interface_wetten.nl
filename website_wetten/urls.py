from django.conf.urls import patterns, include, url
from django.conf import settings
from django.conf.urls.static import static

from django.contrib import admin
from overview import views
from ajax import views as ajaxViews
from showGraph import views as showGraph
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'website_wetten.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', include('overview.urls')),
    url(r'^overview/', include('overview.urls')),
    url(r'^graph/', showGraph.showGraph),
    url(r'^ajax/history/', ajaxViews.article_history),
    url(r'^ajax/law_text/$', ajaxViews.load_law_text),
    url(r'^ajax/related_law/$', ajaxViews.related_law),
    url(r'^(?P<expression>id/BWB[VR]\d{7}/(?:nl/)?\d{4}-\d{2}-\d{2}/data.xml)$', views.law, name='expression'),
    url(r'^(?P<bwb>BWB[VR]\d{7})/artikel/(?P<article>[^/]+)/?$', views.law, name='article'),
    url(r'^(?P<bwb>BWB[VR]\d{7})/artikel/(?P<article>[^/]+)/?$', views.law, name='article'),
    url(r'^(?P<ref>BWB[VR]\d{7}.*?/extref/.*$)', views.law, name='bwb'),
    url(r'^(?P<bwb>BWB[VR]\d{7})/$', views.law, name='bwb'),
    url(r'^(?P<ecli>ECLI:[^:]+:[^:]+:\d{4}:[^/]+)/$', views.ecli, name='ecli'),
    
    
) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
