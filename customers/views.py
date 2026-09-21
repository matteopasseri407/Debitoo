from rest_framework.generics import CreateAPIView

from customers.models import Customer
from customers.serializers import CustomerSerializer


class CustomerCreateView(CreateAPIView):
    """
    Endpoint per la registrazione di un nuovo cliente.

    POST /api/customers/ (o alias /api/clienti/)
    - Riceve i dati in formato JSON: first_name, last_name, email.
    - Se i dati sono validi, crea il record su MySQL e restituisce HTTP 201 Created.
    - In caso di dati mancanti, email errata o duplicata, restituisce HTTP 400 Bad Request
      con spiegazione dell'errore in italiano.
    """

    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
