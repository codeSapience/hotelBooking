from django.db import models
from django.contrib.auth.models import User


class Booking(models.Model):
    """
    Model for user booking, per hotel.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    place_id = models.CharField(max_length=100,
                                null=False,
                                verbose_name="A standard HERE place id")
    place_title = models.CharField(max_length=255,
                                   verbose_name="Title of Place",
                                   null=True)
    time_booked = models.DateTimeField(verbose_name="Exact bookng time",
                                       auto_now=True)
    cost = models.FloatField(verbose_name="Amount for booking place",
                             null=True)  # optional field

    def __str__(self):
        return "Booking {booking_id}; User {user} Booked {place}".format(
            booking_id=self.id,
            user=self.user.username,
            place=self.place_title,
        )


# class Place(models.Model):
#     """
#     Model for any given location point aka place, on the map
#     """
#     title = models.CharField(max_length=150, verbose_name="Place Title", null=True)
#     address = models.CharField(max_length=255, verbose_name="Location Address", null=True)
#     lat = models.FloatField(verbose_name="Latitude point", null=False)
#     lon = models.FloatField(verbose_name="Longitude point", null=False)

#     def __str__(self):
#         return self.title + " -> LAT,LONG: " + str((self.lat, self.lon))

# class Hotel(models.Model):
#     """
#     Model to represent a hotel, specifying hotel location/place, hotel name,
#     hotel star-rating, standard price, and other relevant detail for each hotel
#     """
#     location = models.ForeignKey(Place, on_delete=models.CASCADE)
#     name = models.CharField(max_length=150, verbose_name="Hotel Name", null=True)
#     rating = models.IntegerField(verbose_name="Star rating from 1 to 5", null=True)
#     price = models.FloatField(verbose_name="Booking amount", null=True)