from django.urls import path

from customers.views import CustomerCreateView


urlpatterns = [
    path("customers/", CustomerCreateView.as_view(), name="customer-create"),
    path("clienti/", CustomerCreateView.as_view(), name="cliente-create"),
]
