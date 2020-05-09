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

