"""
URL configuration for automailer project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path 
from pdf_parser.apis.viewsets import  SubmittedView,TrackListView
from driver_list.views import DriverListAPIView,NewRaceDriversListView,NewRaceDriversListDeleteView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('',SubmittedView.as_view(),name = 'submit_email'),
    # path('submitted/', SubmittedView.as_view(), name='submitted'),
    path('api/driver-list/', DriverListAPIView.as_view(), name='driver-list-api'),
    # path('api/share-data/', share_data, name='share-data'),
    path('new-driver-list/<int:id>/', NewRaceDriversListDeleteView.as_view(), name='new_race_drivers_delete'),
    path('new-driver-list/', NewRaceDriversListView.as_view(), name='new_race_drivers_list'),
    # path('pro/', ParseDocxAPIView.as_view(), name='process-altitude-factors'),
    path('tracks/', TrackListView.as_view(), name='track-list'),

]



