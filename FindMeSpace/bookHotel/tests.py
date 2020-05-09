# django module
from django.test import TestCase, tag
from django.urls import reverse
from django.contrib.auth import get_user_model

# rest_framework module
from rest_framework.test import APIRequestFactory, APITestCase, APIClient, api_settings
from rest_framework import status, serializers
from rest_framework import exceptions
from rest_framework.authtoken.models import Token

# custom module
from bookHotel import apiviews, urls, models, serializers

# helper functions


@tag('get_property')
class TestGetProperty(APITestCase):
    """
    Test suite for GET endpoint: api/properties
    """
    def setUp(self):
        self.factory = APIRequestFactory()
        # self.client = APIClient()
        self.view = apiviews.getNearbyPlaces
        self.uri = reverse('bookHotel:get_nearby_places')

    @tag('GET')
    def test_with_param_not_supplied(self):
        """
        TEST 1: Test with no param supplied, including required param
        """
        get_param = {}
        get_req = self.factory.get(self.uri, data=get_param)
        test_response = self.view(get_req)

        self.assertEqual(
            test_response.status_code, status.HTTP_400_BAD_REQUEST,
            f'Expected Response Code {status.HTTP_400_BAD_REQUEST}, received {test_response.status_code} instead.'
        )
        self.assertRaises(
            AssertionError,
            msg=
            f"Expected {AssertionError} received {test_response.exception} instead."
        )

    @tag('GET')
    def test_with_empty_value_for_param(self):
        """ 
        TEST 2: Test with empty lat,long values for the required 'at' GET param
        """
        get_param = {'at': ""}
        get_req = self.factory.get(self.uri, data=get_param)
        test_response = self.view(get_req)

        self.assertEqual(
            test_response.status_code, status.HTTP_400_BAD_REQUEST,
            f'Expected Response Code {status.HTTP_400_BAD_REQUEST}, received {test_response.status_code} instead.'
        )

    @tag('GET')
    def test_with_invalid_char_in_param(self):
        """ 
        TEST 3: Test with invalid lat,long values for the required 'at' GET param
        """
        invalid_params = [
            {
                'at': "7sse,88"
            },  # (LAT) value containing alpha character
            {
                'at': "34.488, 84.49"
            },  # value containing space character
            {
                'at': ".,88"
            },  # value containing invalid . char
            {
                'at': "37.93,5erf"
            },  # (LON) value containing alpha character
            {
                'at': "37,**"
            },  # value containing special character
        ]
        for param in invalid_params:
            get_req = self.factory.get(self.uri, data=param)
            test_response = self.view(get_req)

            self.assertRaises(
                exceptions.ValidationError,
                msg=
                f"Expected {exceptions.ValidationError}, received {test_response.exception} instead."
            )

            self.assertEqual(
                test_response.status_code, status.HTTP_400_BAD_REQUEST,
                f"Expected Response Code 400, received {test_response.status_code} instead."
            )

    @tag('GET')
    def test_with_more_param_than_required(self):
        """
        TEST 4: Supply of more than expected/required number of param should return a BAD_REQUEST res
        """
        get_param = {'at': "45.393,2.92", 'extra': 'I am not needed'}
        get_req = self.factory.get(self.uri, data=get_param)
        test_response = self.view(get_req)

        self.assertEqual(
            test_response.status_code, status.HTTP_400_BAD_REQUEST,
            f'Expected Response Code {status.HTTP_400_BAD_REQUEST}, received {test_response.status_code} instead.'
        )

    @tag('GET')
    def test_correct_values(self):
        """
        TEST 5: A check to get response with a 200 when correct values are supplied
        """
        valid_params = [{
            'at': '-90,57.938'
        }, {
            'at': '90,-180'
        }, {
            'at': '-45.939,180.00'
        }]

        for param in valid_params:
            get_req = self.factory.get(self.uri, data=param)
            test_response = self.view(get_req)

            self.assertEqual(
                test_response.status_code, status.HTTP_200_OK,
                f"Expected Response Code {status.HTTP_200_OK}, received {test_response.status_code} instead."
            )
            self.assertContains(test_response, "result")


@tag('book_place')
class TestPlaceBooking(APITestCase):
    """
    Test suite for POST endpoint: api/bookings
    < API endpoint req user sign-in >
    """
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = apiviews.MakeBooking.as_view()
        self.uri = reverse('bookHotel:book_a_property')
        self.user = self.setup_user()
        self.token = Token.objects.create(user=self.user)
        self.token.save()

    @staticmethod
    def setup_user():
        User = get_user_model()
        return User.objects.create_user('testuser@test.com',
                                        email='testuser@test.com',
                                        password='test')

    @tag('POST')
    def test_with_param_not_supplied(self):
        """
        TEST 1: Test with required param not supplied, place_id
        
        < place_id is a valid HERE API place id > 
        """
        invalid_params = [
            {},  # req key wasn't supplied
            {
                "place_id": ""
            }  # req key was supplied but empty
        ]
        for param in invalid_params:
            post_req = self.factory.post(
                self.uri,
                data=param,
                HTTP_AUTHORIZATION=f'Token {self.token.key}')
            post_req.user = self.user
            test_response = self.view(post_req)

            self.assertRaises(
                AssertionError,
                msg=
                f"Expected {AssertionError}, received {test_response.exception} instead."
            )

            self.assertEqual(
                test_response.status_code, status.HTTP_400_BAD_REQUEST,
                f"Expected Response Code {status.HTTP_400_BAD_REQUEST}, received {test_response.status_code} instead."
            )

    @tag('POST')
    def test_with_invalid_param_value(self):
        """
        TEST 2: supplied invalid value for required param place_id, i.e. supplied value is wrong OR no place with such id exist
        """
        invalid_params = [
            {
                "place_id": "JARGON-dkdiqe8:87383839293 ods"
            },  # req key was supplied but has a wrong value
            {
                "place_id":
                "here:pds:place:643vc7xv-ee75ed96f6d349e1b2dfcaXXXXXXXXXX"
            }  # req key was supplied but no such place exist
        ]
        for param in invalid_params:
            post_req = self.factory.post(
                self.uri,
                data=param,
                HTTP_AUTHORIZATION=f'Token {self.token.key}')
            post_req.user = self.user
            test_response = self.view(post_req)

            self.assertEqual(
                test_response.status_code, status.HTTP_404_NOT_FOUND,
                f"Expected Response Code {status.HTTP_404_NOT_FOUND}, received {test_response.status_code} instead."
            )

    @tag('POST')
    def test_with_user_not_signed_in(self):
        """
        TEST 3: API endpoint req user login, now testing without user login
        """
        all_params = [
            {
                "place_id":
                "here:pds:place:643vc7xv-ee75ed96f6d349e1b2dfca1e86682044"
            },  # req key was supplied and valid
            {
                "place_id":
                "here:pds:place:643vc7xv-ee75ed96f6d349e1b2dfcaXXXXXXXXXX"
            },  # req key was supplied but invalid
        ]
        for param in all_params:
            post_req = self.factory.post(self.uri, data=param)
            test_response = self.view(post_req)

            self.assertEqual(
                test_response.status_code, status.HTTP_401_UNAUTHORIZED,
                f"Expected Response Code {status.HTTP_401_UNAUTHORIZED}, received {test_response.status_code} instead."
            )

    @tag('POST')
    def test_with_correct_param(self):
        """
        TEST 4: a valid place_id was supplied and an authenticated user token
        """
        param = {
            "place_id":
            "here:pds:place:643vc7xv-ee75ed96f6d349e1b2dfca1e86682044"
        }  # a valid place_id
        post_req = self.factory.post(
            self.uri, data=param, HTTP_AUTHORIZATION=f'Token {self.token.key}')
        post_req.user = self.user
        test_response = self.view(post_req)
        self.assertEqual(
            test_response.status_code, status.HTTP_201_CREATED,
            f"Expected Response Code {status.HTTP_201_CREATED}, received {test_response.status_code} instead."
        )


@tag('list_bookings')
class TestListBookings(APITestCase):
    """
    Test suite for GET endpoint: api/properties/PROPERTY_ID/bookings
    < PROPERTY_ID is also place_id >
    """
    def setUp(self):
        self.factory = APIRequestFactory()

    @tag('GET')
    def test_with_invalid_param(self):
        """
        TEST 1: attempt to get/list all bookings for a place/property, supplying incorrect PROPERTY_ID
        """
        invalid_params = [{
            "PROPERTY_ID": "here:pds:place:YYYYYYYY-XXXXXXXXXX",
        }, {
            "PROPERTY_ID":
            "here:pds:place:643vc7xv-ee75ed96f6d349e1b2dfcaXXXXXXXXXX",
        }]
        for prop_id in invalid_params:
            uri = reverse('bookHotel:get_bookings',
                          kwargs={"PROPERTY_ID": f"{prop_id['PROPERTY_ID']}"})
            get_req = self.factory.get(uri)
            test_response = apiviews.getBookings(
                get_req, PROPERTY_ID=prop_id['PROPERTY_ID'])
            self.assertEqual(
                test_response.status_code, status.HTTP_404_NOT_FOUND,
                f'Expected Response Code {status.HTTP_404_NOT_FOUND}, received {test_response.status_code} instead.'
            )

    @tag('GET')
    def test_with_valid_value_in_url(self):
        """
        TEST 2: Using a correct url, containing a valid PROPERTY_ID, a HTTP_200 response should be returned
        """
        new_user_ser = serializers.UserSerializer(data={
            "email": 'test@test.com',
            "password": 'testPassword'
        })
        if new_user_ser.is_valid():
            test_user = new_user_ser.save()
        prop_id = "here:pds:place:643vc7xv-ee75ed96f6d349e1b2dfca1e86682044"
        new_booking_ser = serializers.BookingSerializer(
            data={
                "place_id": prop_id,
                "place_title": "Test Place"
            })
        new_booking_ser.user = serializers.UserSerializer(instance=test_user)
        if new_booking_ser.is_valid():
            new_booking_ser.save()

        uri = reverse('bookHotel:get_bookings',
                      kwargs={"PROPERTY_ID": prop_id})
        get_req = self.factory.get(uri)
        test_response = apiviews.getBookings(get_req, PROPERTY_ID=prop_id)
        self.assertEqual(
            test_response.status_code, status.HTTP_200_OK,
            f'Expected Response Code {status.HTTP_200_OK}, received {test_response.status_code} instead.'
        )
