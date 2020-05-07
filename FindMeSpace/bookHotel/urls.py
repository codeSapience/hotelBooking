from django.conf.urls import url
from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
# from rest_framework.authtoken import views as drf_views
from .apiviews import getNearbyPlaces

app_name = 'bookHotel'

urlpatterns = [
    path('properties', getNearbyPlaces, name="nearby_places"),
    # path("list/", CatererList.as_view(), name="caterer_list"),
    # path("detail/<int:pk>/", CatererDetail.as_view(), name="caterer_detail"),
    # path("create/", CatererCreate.as_view(), name="caterer_create"),
    # path("user/create/", UserCreate.as_view(), name="user_create"),
    # path("edit/<int:pk>/", CatererUpdate.as_view(), name="caterer_update"),
    # path("login/", UserLogin.as_view(), name="user_login"),
    # path("login/", drf_views.obtain_auth_token, name="user_login"),
    #TODO: path("logout/", drf_views.obtain_auth_token, name="user_logout"),
    #TODO: path("delete/", drf_views.obtain_auth_token, name="caterer_delete"),
    # path(r'swagger-docs/', schema_view),
]

urlpatterns = format_suffix_patterns(urlpatterns)