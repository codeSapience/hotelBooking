from rest_framework import serializers
from rest_framework.authtoken.models import Token
from .models import Booking, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "password"]
        extra_kwargs = {
            'username': {
                'required': False,
            },
            'email': {
                'required': True,
                'allow_blank': False,
                'allow_null': False
            },
            'password': {
                'required': True,
                'write_only': True
            },
        }

    def create(self, validated_data):
        new_user = User(
            email=str(validated_data['email']).lower(
            ),  # set email to lower case e.g. you@xyz.co
            username=str(
                validated_data['email']).lower(),  # USERNAME DEFAULTS TO EMAIL
            first_name=str(validated_data.get(
                'first_name',
                "")).title(),  # set first_name to title case e.g. John
            last_name=str(validated_data.get(
                'last_name',
                "")).title(),  # set last_name to title case e.g. Doe-Lee
        )

        new_user.set_password(validated_data["password"])

        try:  # Handling possible exception in user creation
            new_user.save()
            Token.objects.create(user=new_user)
            return new_user
        except Exception as exc:
            raise exc


class BookingSerializer(serializers.ModelSerializer):
    user = UserSerializer(required=False)

    class Meta:
        model = Booking
        fields = "__all__"
        extra_kwargs = {"place_id": {"write_only": True}}

    def create(self, validated_data):
        new_booking = Booking(user=self.user.instance,
                              place_id=self.validated_data["place_id"],
                              place_title=self.validated_data["place_title"])

        new_booking.save()
        return new_booking


# class PlaceSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Place
#         fields = "__all__"

#     def create(self, validated_data):
#         the_place = Place(
#             title = validated_data.get('title', ""),
#             address = validated_data.get("address", ""),
#             lat = float(validated_data["lat"]),
#             lon = float(validated_data["lon"]),
#         )

#         the_place.save()
#         return the_place

# class HotelSerializer(serializers.ModelSerializer):
#     location = PlaceSerializer(many=False)
#     class Meta:
#         model = Hotel
#         fields = "__all__"

#     def create(self, validated_data):
#         hotel = Hotel(
#             name = validated_data.get("name", ""),
#             location = self.location.instance,
#             rating = self.validate_data.get("rating", ""),
#             price = self.validate_data.get("rating", ""),
#         )

#         hotel.save()
#         return hotel
