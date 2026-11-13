from . import views
from django.urls import path,include

urlpatterns = [
     # Farmer  Management
    path("farmers/", views.farmer_list, name="farmer_list"),
    path("farmers/create/", views.farmer_create, name="farmer_create"),
    path("farmers/<uuid:pk>/", views.farmer_detail, name="farmer_detail"),
    path("farmers/<uuid:pk>/edit/", views.farmer_update, name="farmer_update"),
    path("farmers/<uuid:pk>/delete/", views.farmer_delete, name="farmer_delete"),
      # Farm  Management
    path("farms/", views.farm_list, name="farm_list"),
    path("farms/create/", views.farm_create, name="farm_create"),
    path("farms/<uuid:pk>/", views.farm_detail, name="farm_detail"),
    path("farms/<uuid:pk>/edit/", views.farm_update, name="farm_update"),
    path("farms/<uuid:pk>/delete/", views.farm_delete, name="farm_delete"),
    path("sectors/", views.get_sectors, name="get_sectors"),

    # Crop Management
    path("crops/", views.crop_list, name="crop_list"),
    path("crops/create/", views.crop_create, name="crop_create"),
    path("crops/<uuid:pk>/", views.crop_detail, name="crop_detail"),
    path("crops/<uuid:pk>/update/", views.crop_update, name="crop_update"),
    path("crops/<uuid:pk>/delete/", views.crop_delete, name="crop_delete"),


# Agricultural Input Management 
    path("agricultural-inputs/",views.agricultural_input_list,name="agricultural_input_list",),
    path("agricultural-inputs/create/", views.agricultural_input_create,name="agricultural_input_create",),
    path("agricultural-inputs/<uuid:pk>/",views.agricultural_input_detail,name="agricultural_input_detail",),
    path("agricultural-inputs/<uuid:pk>/update/",views.agricultural_input_update,name="agricultural_input_update",),
    path("agricultural-inputs/<uuid:pk>/delete/",views.agricultural_input_delete,name="agricultural_input_delete",),


# Planting Record Management
    path("planting-records/",views.planting_record_list,name="planting_record_list",),
    path("planting-records/create/",views.planting_record_create, name="planting_record_create",),
    path("planting-records/<uuid:pk>/",views.planting_record_detail,name="planting_record_detail",),
    path("planting-records/<uuid:pk>/update/",views.planting_record_update,name="planting_record_update",),
    path( "planting-records/<uuid:pk>/delete/",views.planting_record_delete, name="planting_record_delete",),
    
# Planting Input Management
    path("planting-inputs/", views.planting_input_list,name="planting_input_list",),
    path("planting-inputs/create/",views.planting_input_create,name="planting_input_create",),
    path("planting-inputs/<uuid:pk>/",views.planting_input_detail,name="planting_input_detail",),
    path( "planting-inputs/<uuid:pk>/update/",views.planting_input_update,name="planting_input_update",),
    path("planting-inputs/<uuid:pk>/delete/",views.planting_input_delete,name="planting_input_delete",),
    ]