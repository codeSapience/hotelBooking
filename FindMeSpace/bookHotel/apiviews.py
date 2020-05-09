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
from .serializers import BookingSerializer, UserSerializer, CoordinateSerializer
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

    req_param = ('at', )  # TUPLE OF REQUIRED API PARAMETERS

    handler400 = f"All expected GET fields = {req_param}. \n"

    try:  # VALIDATION TO CHECK THAT REQ FIELD(s) VALUE ARE SUPPLIED
        for each in req_param:
            assert each in request.query_params.keys(
            ), f" But '{each}' wasn't found!"
    except AssertionError as errAssert:
        handler400 += str(errAssert)
        return Response({"message": handler400},
                        status=status.HTTP_400_BAD_REQUEST)
    # ENSURE ONLY EXPECTED PARAM IS SUPPLIED
    if len(request.query_params) > len(req_param):
        handler400 = {
            "message":
            "ERROR! Please supply valid value for ONLY the 'at' param, NO OTHER PARAM IS EXPECTED BESIDES 'at'",
        }
        return Response(handler400, status=status.HTTP_400_BAD_REQUEST)

    position = request.query_params.get("at", None)
    coordinate = position.split(",")
    if position and (len(coordinate) == 2):
        # CHECK IF EITHER COORDINATE CONTAINS INVALID/UNEXPECTED CHARACTER
        check_list = [
            '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.', '-'
        ]
        for coord in coordinate:
            if any([x not in check_list for x in coord]):
                handler400 = {
                    "message":
                    f"Supplied value '{coord}' contains Invalid character(s)"
                }
                return Response(handler400, status=status.HTTP_400_BAD_REQUEST)
        coord_serializer = CoordinateSerializer(data={
            "lat": coordinate[0],
            "lon": coordinate[1],
        })
        # TRY / EXCEPT TO CATCH POSSIBLE ERROR(S) WITH INPUT VALIDATION
        try:
            coord_serializer.is_valid(
                raise_exception=True
            )  # check if valid coordinate values were supplied; LAT,LONG
            api_url = "https://discover.search.hereapi.com/v1/discover?at={LAT},{LONG}&limit={LIM}&q={KEYWORD}&apiKey={API_KEY}".format(
                LAT=coord_serializer.validated_data["lat"],
                LONG=coord_serializer.validated_data["lon"],
                LIM=PLACES_QUERY_LIM,
                KEYWORD=PROPERTY_TYPE,
                API_KEY=API_KEY)
            fetch_places = req.get(api_url)  # API CALL TO GET PLACE(s)
            json_res = json.loads(fetch_places.content)
            if fetch_places.status_code == 200:
                return Response(
                    {
                        "message": {
                            "coordinate": {
                                'lat': coordinate[0],
                                'lon': coordinate[1]
                            },
                            "queryLimit": PLACES_QUERY_LIM
                        },
                        "result": json_res
                    },
                    status=status.HTTP_200_OK)  # RETURNING RESPONSE
            elif 400 <= fetch_places.status_code < 500:
                handler400 = {
                    "message":
                    dict(json_res).get(
                        "action",
                        "INVALID VALUE! Check your supplied value for 'at' and try again."
                    )
                }
                return Response(
                    handler400,
                    status=status.HTTP_400_BAD_REQUEST)  # RETURNING RESPONSE
            elif fetch_places.status_code >= 500:
                handler500 = {
                    "message":
                    "A third-party error occured! Please retry shortly."
                }
                return Response(handler500,
                                status=status.HTTP_504_GATEWAY_TIMEOUT
                                )  # RETURNING RESPONSE

        except serializers.ValidationError:  # HANDLING VALIDATION ERROR WITH LAT,LONG VALUES
            return Response(coord_serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        except req.ConnectionError:
            handler500 = {
                "message":
                "Failed to establish a new connection. Please retry shortly"
            }
            return Response(handler500, status=status.HTTP_502_BAD_GATEWAY)

    # IMPLICITLY HANDLE OTHER UNCAUGHT ERRORS WITH SUPPLIED INPUT
    handler400 = {
        "message":
        "ERROR! Please supply VALID value for 'at' param like this ?at=LAT,LONG \
                \n 1. Be sure to seperate both values (LAT and LONG) with a comma (,) \
                \n2. LATITUDE must be a number between -90 and 90 (inclusive) \
                \n3. LONGITUDE must be a number between -180 and 180 (inclusive)"
    }
    return Response(handler400,
                    status=status.HTTP_400_BAD_REQUEST)  # RETURNING RESPONSE


class MakeBooking(APIView):
    """
    Creates a booking for a property/place. \
    REQUIRES place_id param in payload
    """
    permission_classes = (permissions.IsAuthenticated, )

    def post(self, request):
        req_param = ('place_id', )  # TUPLE OF REQUIRED API PARAMETERS

        input_list_dict = dict(self.request.data)
        handler400 = f"All expected fields = {req_param}. \n"

        try:  # VALIDATION TO CHECK THAT REQ FIELDS VALUE ARE SUPPLIED, AND NOT AS EMPTY
            for each in req_param:
                assert each in input_list_dict.keys(
                ), f" But {each} wasn't found!"
                assert input_list_dict[each] != [
                    ""
                ], f" NO VALUE SUPPLIED FOR {each}!"
        except AssertionError as errAssert:
            handler400 += str(errAssert)
            return Response({"message": handler400},
                            status=status.HTTP_400_BAD_REQUEST)
        place_id = self.request.data["place_id"]
        base_url = "https://lookup.search.hereapi.com/v1/lookup"
        api_url = f"{base_url}?id={place_id}&apiKey={API_KEY}"
        try:
            place_lookup = req.get(api_url)  # API CALL TO LOOKUP A PLACE
        except req.ConnectionError:
            handler500 = {
                "message":
                "Failed to establish a new connection. Please retry shortly"
            }
            return Response(
                handler500,
                status=status.HTTP_502_BAD_GATEWAY)  # RETURNING RESPONSE
        if place_lookup.status_code == 200:  # ONLY IF THE PLACE EXIST/IS VALID
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
                        status=status.HTTP_201_CREATED)  # RETURNING RESPONSE
            except serializers.ValidationError as err:  # HANDLE VALIDATION ERROR(s) WITH SUPPLIED INPUT(s)
                handler400 = {"message": str(err)}
                return Response(
                    handler400,
                    status=status.HTTP_400_BAD_REQUEST)  # RETURNING RESPONSE
            except Exception:  # CATCH ANY OTHER UNCAUGHT EXCEPTION(s)
                return Response(
                    {
                        "message":
                        "Sorry, but your request could not be processed. You can try again."
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )  # RETURNING RESPONSE
        elif place_lookup.status_code == 400:
            handler400 = {
                "message":
                f"BAD REQUEST! You sent a wrong value for an expected param in {req_param}. Kindly check and try again"
            }
            return Response(
                handler400,
                status=status.HTTP_404_NOT_FOUND)  # RETURNING RESPONSE
        elif place_lookup.status_code == 404:
            handler400 = {"message": f"No Place with id {place_id} was found"}
            return Response(
                handler400,
                status=status.HTTP_404_NOT_FOUND)  # RETURNING RESPONSE
        elif place_lookup.status_code == 503:
            handler500 = {
                "message":
                "SORRY, SERVICE IS CURRENTLY UNAVAILABLE! PLEASE TRY AGAIN SHORTLY"
            }
            return Response(
                handler500,
                status=status.HTTP_504_GATEWAY_TIMEOUT)  # RETURNING RESPONSE


@api_view(http_method_names=['GET'])
@permission_classes([])
def getBookings(request, PROPERTY_ID):
    """
    Returns the bookings for a given property/place.\
    If no bookings found, returns empty list
    """
    queryset = Booking.objects.filter(
        place_id=PROPERTY_ID)  # SEARCH FOR BOOKINGS WITH SUPPLIED PROPERTY_ID
    base_url = "https://lookup.search.hereapi.com/v1/lookup"
    api_url = f"{base_url}?id={PROPERTY_ID}&apiKey={API_KEY}"
    try:
        place_lookup = req.get(
            api_url)  # API CALL TO CHECK IF PROPERTY/PLACE ACTUALLY EXIST
    except req.ConnectionError:
        handler500 = {
            "message":
            "Failed to establish a new connection. Please retry shortly"
        }
        return Response(
            handler500,
            status=status.HTTP_502_BAD_GATEWAY)  # RETURNING RESPONSE
    if queryset:
        all_bookings = BookingSerializer(queryset, many=True)
        return Response({"result": all_bookings.data},
                        status=status.HTTP_200_OK)  # RETURNING RESPONSE
    elif place_lookup.status_code != 200:
        return Response(
            {
                "message":
                f"No booking was found! Seem the given PROPERTY_ID is invalid."
            },
            status=status.HTTP_404_NOT_FOUND)  # RETURNING RESPONSE
    return Response(
        {
            "message": f"No booking was found for the PROPERTY: {PROPERTY_ID}",
            "result": queryset.data
        },
        status=status.HTTP_200_OK)  # RETURNING RESPONSE


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
                return Response(
                    user_serializer.data,
                    status=status.HTTP_201_CREATED)  # RETURNING RESPONSE
        except serializers.ValidationError:
            return Response(
                user_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST)  # RETURNING RESPONSE
        except IntegrityError:
            handler400 = {"message": "Warning: That email already exist!"}
            return Response(
                handler400,
                status=status.HTTP_400_BAD_REQUEST)  # RETURNING RESPONSE
        except Exception:
            handler500 = {"message": "Something went wrong. Please try again"}
            return Response(handler500,
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                            )  # RETURNING RESPONSE


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
                    return Response(
                        {"result": {
                            'token': user.auth_token.key
                        }},
                        status=status.HTTP_200_OK)  # RETURNING RESPONSE
                return Response(
                    {"message": "Invalid User Credentials"},
                    status=status.HTTP_404_NOT_FOUND)  # RETURNING RESPONSE
        except serializers.ValidationError:
            return Response(
                user_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST)  # RETURNING RESPONSE


@api_view(http_method_names=['POST'])
@permission_classes([])
def logoutUser(request):
    """
    Logout a current user. Returns "message"
    """
    logout(request)
    return Response({"message": "USER LOGGED OUT!"},
                    status=status.HTTP_200_OK)  # RETURNING RESPONSE
