from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from .views import *

urlpatterns = [
    path('',cache_test_view,name="cache_test_view"),

]
