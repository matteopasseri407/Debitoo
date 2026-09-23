"""Regressioni su MySQL: richieste concorrenti e vincoli del dominio."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event
from unittest.mock import patch

from django.db import connections
from rest_framework.test import APIClient, APITransactionTestCase

from customers.models import Customer
from customers.serializers import CustomerSerializer
from pratiche.models import Pratica
from pratiche.serializers import PraticaStatoUpdateSerializer


def api_request(method, path, payload):
    try:
        response = getattr(APIClient(), method)(path, payload, format="json")
        return response.status_code
    finally:
        connections.close_all()


class ConcurrentRequestsTests(APITransactionTestCase):
    def test_duplicate_email_concorrenti_restituiscono_201_e_400(self):
        barrier = Barrier(2, timeout=5)
        original = CustomerSerializer.validate_email

        def validate(serializer, value):
            result = original(serializer, value)
            barrier.wait()
            return result

        payload = {"first_name": "Mario", "last_name": "Rossi",
                   "email": "concurrent@example.com"}
        with patch.object(CustomerSerializer, "validate_email", validate):
            with ThreadPoolExecutor(max_workers=2) as pool:
                requests = [pool.submit(api_request, "post", "/api/customers/", payload)
                            for _ in range(2)]
                codes = [request.result(timeout=10) for request in requests]
        self.assertEqual(sorted(codes), [201, 400])
        self.assertEqual(Customer.objects.filter(email=payload["email"]).count(), 1)

    def test_chiusura_attende_transizione_in_corso(self):
        customer = Customer.objects.create(first_name="Mario", last_name="Rossi",
                                           email="state@example.com")
        case = Pratica.objects.create(cliente=customer, descrizione="Concorrenza",
                                       importo="10.00")
        path = f"/api/pratiche/{case.pk}/"
        validated, resume, closing_started, closing_finished = (Event() for _ in range(4))
        original = PraticaStatoUpdateSerializer.update

        def delayed_update(serializer, instance, data):
            if data["stato"] == "in_lavorazione":
                validated.set()
                if not resume.wait(5):
                    raise RuntimeError("Timeout della richiesta sospesa dal test")
            return original(serializer, instance, data)

        def close_case():
            closing_started.set()
            try:
                return api_request("patch", path, {"stato": "chiusa"})
            finally:
                closing_finished.set()

        with patch.object(PraticaStatoUpdateSerializer, "update", delayed_update):
            with ThreadPoolExecutor(max_workers=2) as pool:
                first = pool.submit(api_request, "patch", path, {"stato": "in_lavorazione"})
                try:
                    self.assertTrue(validated.wait(5))
                    second = pool.submit(close_case)
                    self.assertTrue(closing_started.wait(5))
                    self.assertFalse(closing_finished.wait(0.3))
                finally:
                    resume.set()
                self.assertEqual(first.result(timeout=10), 200)
                self.assertEqual(second.result(timeout=10), 200)
        case.refresh_from_db()
        self.assertEqual(case.stato, "chiusa")
