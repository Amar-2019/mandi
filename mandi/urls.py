from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('i18n/', include('django.conf.urls.i18n')),
]

# Remove i18n_patterns if you don't need language-specific URLs
# urlpatterns += i18n_patterns(
#     prefix_default_language=False,
# )