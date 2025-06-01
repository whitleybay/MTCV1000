from django.contrib import admin
from django.urls import include, path


urlpatterns = [
        path('admin/', admin.site.urls),  # <--- Crucial
        path('', include('mtc_checker.urls')), # Include your app's URLs
    ]