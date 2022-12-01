from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('posts.urls')),
    path('auth/', include('users.urls')),
    path('auth/', include('django.contrib.auth.urls')),
    path('about/', include('about.urls', namespace='about'))
]

handler404 = 'core.views.page_not_found'
handler403 = 'core.views.permission_denied_view'
handler500 = 'core.views.internal_server_error'
