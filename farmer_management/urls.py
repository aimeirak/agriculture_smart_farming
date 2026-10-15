from . import views
from django.urls import path,include

urlpatterns = [
    path("farmers/", views.farmer_list, name="farmer_list"),
    path("farmers/create/", views.farmer_create, name="farmer_create"),
    path("farmers/<uuid:pk>/", views.farmer_detail, name="farmer_detail"),
    path("farmers/<uuid:pk>/edit/", views.farmer_update, name="farmer_update"),
    path("farmers/<uuid:pk>/delete/", views.farmer_delete, name="farmer_delete"),
    path("farms/", views.farm_list, name="farm_list"),
    path("farms/create/", views.farm_create, name="farm_create"),
    path("farms/<uuid:pk>/", views.farm_detail, name="farm_detail"),
    path("farms/<uuid:pk>/edit/", views.farm_update, name="farm_update"),
    path("farms/<uuid:pk>/delete/", views.farm_delete, name="farm_delete"),
    path("sectors/", views.get_sectors, name="get_sectors"),
    ]