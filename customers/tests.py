from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from customers.models import Customer


class CustomerCreateApiTests(APITestCase):
    def setUp(self):
        self.url = reverse("customer-create")

    def test_creates_customer_with_valid_data(self):
        response = self.client.post(
            self.url,
            {
                "first_name": "Mario",
                "last_name": "Rossi",
                "email": "Mario.Rossi@example.com",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Customer.objects.count(), 1)
        self.assertEqual(Customer.objects.get().email, "mario.rossi@example.com")
        self.assertIn("id", response.data)

    def test_rejects_missing_email(self):
        response = self.client.post(
            self.url,
            {"first_name": "Mario", "last_name": "Rossi"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Customer.objects.count(), 0)
        self.assertEqual(response.data["email"][0], "L'email è obbligatoria.")

    def test_rejects_duplicate_email_ignoring_case(self):
        Customer.objects.create(
            first_name="Mario",
            last_name="Rossi",
            email="mario.rossi@example.com",
        )

        response = self.client.post(
            self.url,
            {
                "first_name": "Maria",
                "last_name": "Verdi",
                "email": "MARIO.ROSSI@example.com",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Customer.objects.count(), 1)
        self.assertEqual(
            response.data["email"][0],
            "Esiste già un cliente con questa email.",
        )

    def test_rejects_invalid_email(self):
        response = self.client.post(
            self.url,
            {
                "first_name": "Mario",
                "last_name": "Rossi",
                "email": "indirizzo-non-valido",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Customer.objects.count(), 0)
        self.assertEqual(
            response.data["email"][0],
            "Inserisci un indirizzo email valido.",
        )
