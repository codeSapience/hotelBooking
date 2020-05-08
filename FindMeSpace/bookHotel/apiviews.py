# python module
import requests as req

# django module
from django.contrib.auth import authenticate, logout
from django.conf import settings
from rest_framework.parsers import JSONParser, json
from django.db.utils import IntegrityError

# rest_framework module
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, serializers

# custom module
from .serializers import BookingSerializer, UserSerializer
from .models import Booking

API_KEY = getattr(settings, "HERE_API_KEY")
PROPERTY_TYPE = 'hotel'


@api_view(http_method_names=['GET'])
@permission_classes([])
def getNearbyPlaces(request):
    """
    Returns the property/place around a given (Lat,Lon) coordinate. \
    REQUIRES one(1) GET param named 'at' e.g. {api_endpoint}?at=LAT,LONG
    """
    PLACES_QUERY_LIM = 1

    position = request.query_params.get("at", None)
    if position:
        if len(request.query_params) > 1:
            handler400 = "ERROR! Please supply valid value for ONLY the 'at' param, NO OTHER PARAM IS EXPECTED BESIDES 'at'"
            return Response(handler400, status=status.HTTP_400_BAD_REQUEST)
        try:
            coordinate = [
                float(item.strip(' ')) for item in position.split(",")
            ]
            api_url = "https://discover.search.hereapi.com/v1/discover?at={LAT},{LONG}&limit={LIM}&q={KEYWORD}&apiKey={API_KEY}".format(
                LAT=coordinate[0],
                LONG=coordinate[1],
                LIM=PLACES_QUERY_LIM,
                KEYWORD=PROPERTY_TYPE,
                API_KEY=API_KEY)
            fetch_places = req.get(api_url)
            if fetch_places.status_code == 200:
                return Response({
                    "message": {
                        "coordinate": {
                            'lat': coordinate[0],
                            'lon': coordinate[1]
                        },
                        "queryLimit": PLACES_QUERY_LIM
                    },
                    "result": fetch_places.content
                })
            elif 400 <= fetch_places.status_code < 500:
                handler400 = "INVALID VALUE! Check your supplied value for 'at' and try again."
                return Response(handler400,
                                status=status.HTTP_424_FAILED_DEPENDENCY)
            elif fetch_places.status_code >= 500:
                handler500 = "A third-party error occured! Please retry shortly."
                return Response(handler500,
                                status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception:
            handler400 = "ERROR! Please supply VALID value for 'at' param like this ?at=LAT,LONG \
                \n 1. Be sure to seperate both values (LAT and LONG) with a comma (,) \
                \n2. And that they (LAT and LONG) are both valid numbers."

            return Response(handler400, status=status.HTTP_400_BAD_REQUEST)

    handler400 = "ERROR! Please supply a value for 'at' param in your URL as in format ?at=LAT,LONG"
    return Response(handler400, status=status.HTTP_400_BAD_REQUEST)


class MakeBooking(APIView):
    """
    Creates a booking for a property/place. \
    REQUIRES place_id param in payload
    """
    permission_classes = (permissions.IsAuthenticated, )

    def post(self, request):
        req_input = ('place_id', )

        input_list_dict = dict(self.request.data)
        handler400 = f"All expected fields = {req_input}."

        try:  # VALIDATION TO CHECK THAT REQ FIELDS VALUE ARE SUPPLIED, AND NOT AS EMPTY
            for each in req_input:
                assert each in input_list_dict.keys(
                ), f" But {each} wasn't found!"
                assert input_list_dict[each] != [
                    ""
                ], f" NO VALUE SUPPLIED FOR {each}!"
        except AssertionError as errAssert:
            handler400 += str(errAssert)
            return Response(handler400, status=status.HTTP_400_BAD_REQUEST)
        place_id = self.request.data["place_id"]
        base_url = "https://lookup.search.hereapi.com/v1/lookup"
        api_url = f"{base_url}?id={place_id}&apiKey={API_KEY}"
        place_lookup = req.get(api_url)
        if place_lookup.status_code == 200:
            new_booking = BookingSerializer(
                data={
                    "place_id": place_id,
                    "place_title": json.loads(place_lookup.content)["title"],
                })
            new_booking.user = UserSerializer(
                instance=self.request.user
            )  # Get username from currently logged in user
            try:
                if new_booking.is_valid(raise_exception=True):
                    new_booking.save()
                    return Response(
                        {
                            "message": "Property Booked!",
                            "result": new_booking.data
                        },
                        status=status.HTTP_201_CREATED)
            except serializers.ValidationError as err:
                handler400 = str(err)
                return Response(handler400, status=status.HTTP_400_BAD_REQUEST)
        elif place_lookup.status_code == 400:
            handler400 = f"BAD REQUEST! You sent a wrong value for an expected param. Kindly check and try again"
            return Response(handler400, status=status.HTTP_404_NOT_FOUND)
        elif place_lookup.status_code == 404:
            handler400 = f"No Place with id {place_id} was found"
            return Response(handler400, status=status.HTTP_404_NOT_FOUND)
        elif place_lookup.status_code == 503:
            handler500 = "SORRY, SERVICE IS CURRENTLY UNAVAILABLE! PLEASE TRY AGAIN SHORTLY"
            return Response(handler500,
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(
            {
                "message":
                "Sorry, but your request could not be processed. You can try again."
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(http_method_names=['GET'])
@permission_classes([])
def getBookings(request, PROPERTY_ID):
    """
    Returns the bookings for a property/place.\
    If no bookings found, returns empty list
    """
    queryset = Booking.objects.filter(place_id=PROPERTY_ID)
    base_url = "https://lookup.search.hereapi.com/v1/lookup"
    api_url = f"{base_url}?id={PROPERTY_ID}&apiKey={API_KEY}"
    place_lookup = req.get(api_url)
    if queryset:
        all_bookings = BookingSerializer(queryset, many=True)
        if all_bookings.errors:
            return Response({"error": all_bookings.errors},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"result": all_bookings.data},
                        status=status.HTTP_200_OK)
    elif place_lookup.status_code != 200:
        return Response(
            {
                "message":
                f"No booking was found! Seem that PROPERTY_ID is invalid."
            },
            status=status.HTTP_404_NOT_FOUND)
    return Response(
        {
            "message": f"No booking was found for the PROPERTY: {PROPERTY_ID}",
            "result": queryset.data
        },
        status=status.HTTP_200_OK)  # HTTP_204 can be used alternatively


class UserSignup(APIView):
    """
    API for new user signUp.
    """
    permission_classes = ()

    def post(self, request):
        user_serializer = UserSerializer(data=self.request.data)

        try:
            if user_serializer.is_valid(raise_exception=True):
                user_serializer.save()
                return Response(user_serializer.data,
                                status=status.HTTP_201_CREATED)
        except serializers.ValidationError:
            return Response(user_serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError:
            handler400 = 'Warning: That email already exist!'
            return Response(handler400, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            handler500 = "Something went wrong. Please try again"
            return Response(handler500,
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserLogin(APIView):
    """
    API for user login. Returns a user Token as result.
    """
    permission_classes = ()

    def post(self, request):
        email = self.request.data.get("email")
        password = self.request.data.get("password")
        user_serializer = UserSerializer(data={
            "email": email,
            "password": password
        })
        try:
            if user_serializer.is_valid(raise_exception=True):
                user = authenticate(
                    username=user_serializer.validated_data["email"],
                    password=password)
                if user:
                    return Response({"result": {
                        'token': user.auth_token.key
                    }},
                                    status=status.HTTP_200_OK)
                return Response({"error": "Invalid User Credentials"},
                                status=status.HTTP_404_NOT_FOUND)
        except serializers.ValidationError:
            return Response(user_serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)


@api_view(http_method_names=['POST'])
@permission_classes([])
def logoutUser(request):
    """
    Logout a current user. Returns "message"
    """
    logout(request)
    return Response({"message": "USER LOGGED OUT!"}, status=status.HTTP_200_OK)
