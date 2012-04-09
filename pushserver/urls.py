from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url('^$', 'pushserver.views.passthrough', name='pushserver-passthrough'),
)
