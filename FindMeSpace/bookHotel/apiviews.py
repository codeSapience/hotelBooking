import requests as req

# django module
from django.contrib.auth import authenticate
from django.conf import settings
from django.shortcuts import get_object_or_404

# rest_framework module
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from .serializers import BookingSerializer, PlaceSerializer, UserSerializer, HotelSerializer


@api_view(http_method_names=['GET'])
def getNearbyPlaces(request):
    PLACES_QUERY_LIM = 20
    PROPERTY_TYPE = 'hotel'

    position = request.query_params.get("at", 'None')
    if position:
        try:
            coordinate = [item.strip(' ') for item in position.split(",")]
            query_place = PlaceSerializer(data={
                "lat": float(coordinate[0]),
                "lon": float(coordinate[1]),
            })
        except Exception:
            handler400 = "Error! Please supply VALID value for 'at' param like this ?at=LAT,LONG \
                \n 1. Be sure to seperate both values (LAT and LONG) with a comma (,) \
                \n2. And that they (LAT and LONG) are both valid numbers."

            return Response(handler400, status=status.HTTP_400_BAD_REQUEST)

        if len(request.query_params) > 1:
            handler400 = "Error! Please supply valid value for ONLY the 'at' param, NO OTHER PARAM IS EXPECTED BESIDES 'at'"
            return Response(handler400,
                            status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        elif query_place.is_valid(raise_exception=True):
            # headers = {}
            api_url = "https://discover.search.hereapi.com/v1/discover?at={LAT},{LONG}&limit={LIM}&q={KEYWORD}&apiKey={API_KEY}".format(
                LAT=query_place.validated_data['lat'],
                LONG=query_place.validated_data['lon'],
                LIM=PLACES_QUERY_LIM,
                KEYWORD=PROPERTY_TYPE,
                API_KEY=getattr(settings, "HERE_API_KEY")
            )
            fetch_places = req.get(api_url)
            if fetch_places.status_code == 200:
                return Response({
                    "coordinate": [
                        'LAT: ' + str(query_place.validated_data['lat']),
                        'LONG: ' + str(query_place.validated_data['lon']),
                    ],
                    "queryLimit":
                    PLACES_QUERY_LIM,
                    "result":
                    fetch_places.content
                })
            elif 400 <= fetch_places.status_code < 500:
                handler400 = "INVALID VALUE! Check your supplied value for 'at' and try again."
                return Response(handler400,
                                status=status.HTTP_424_FAILED_DEPENDENCY)
            elif fetch_places.status_code >= 500:
                handler500 = "A third-party error occured! Please retry shortly."
                return Response(handler500,
                                status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(query_place.errors, status=status.HTTP_400_BAD_REQUEST)
    handler400 = "ERROR! Please supply a value for 'at' param in your URL as in format ?at=LAT,LONG"
    return Response(handler400, status=status.HTTP_400_BAD_REQUEST)


class MakeBooking(APIView):
    def post(self, request):
        