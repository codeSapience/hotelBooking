from django.conf.urls import url
from django.urls import path
from rest_framework_swagger.views import get_swagger_view
# from rest_framework.urlpatterns import format_suffix_patterns
from .apiviews import getNearbyPlaces, MakeBooking, getBookings, UserLogin, UserSignup, logoutUser

app_name = 'bookHotel'

schema_view = get_swagger_view(title='Hotel Booking API')

urlpatterns = [
    path('properties', getNearbyPlaces, name="nearby_places"),
    path('bookings', MakeBooking.as_view(), name="book_a_property"),
    url(r'^properties/(?P<PROPERTY_ID>here:pds:place:[0-9A-Za-z]+-[0-9A-Za-z]+)/bookings$',
        getBookings,
        name="get_bookings"),
    path('signup', UserSignup.as_view(), name="user_signup"),
    path("login", UserLogin.as_view(), name="user_login"),
    path("logout", logoutUser, name="user_logout"),
    path('docs/', schema_view),
]

# urlpatterns = format_suffix_patterns(urlpatterns)