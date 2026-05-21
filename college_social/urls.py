from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import landing_view

urlpatterns = [
    path('', landing_view, name='landing'),
    path('student/', include('students.urls')),
    path('teacher/', include('teachers.urls')),
    path('admin-panel/', include('admin_panel.urls')),
    # If using Django admin temporarily or at all
    path('django-admin/', admin.site.urls),
]

handler404 = 'core.views.custom_404'
handler500 = 'core.views.custom_500'


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
