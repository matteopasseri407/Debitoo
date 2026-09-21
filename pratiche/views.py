from django.http import Http404
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView

from pratiche.models import Pratica, StatoPratica
from pratiche.serializers import (
    PraticaCreateSerializer,
    PraticaReadSerializer,
    PraticaStatoUpdateSerializer,
)


class PraticaListCreateView(ListCreateAPIView):
    """
    Endpoint per:
    1. GET  /api/pratiche/ -> Elenco pratiche con supporto filtro '?stato=<stato>'
    2. POST /api/pratiche/ -> Creazione di una nuova pratica debitoria

    Ottimizzazioni:
    - select_related('cliente') esegue una INNER JOIN SQL su MySQL, evitando il
      problema delle query N+1 quando serializziamo i dati del cliente collegato.
    """

    def get_queryset(self):
        # Queryset di base con JOIN sul cliente per ottimizzare le prestazioni
        queryset = Pratica.objects.select_related("cliente").all()

        # Supporto filtro per stato: accetta '?stato=' (italiano) o '?status=' (inglese)
        filtro_stato = (
            self.request.query_params.get("stato")
            or self.request.query_params.get("status")
        )

        if filtro_stato:
            filtro_normalizzato = filtro_stato.strip().lower()
            stati_validi = set(StatoPratica.values)
            if filtro_normalizzato not in stati_validi:
                raise ValidationError(
                    {
                        "stato": [
                            f"Valore di filtro non valido: '{filtro_stato}'. "
                            f"Gli stati ammessi sono: {', '.join(sorted(stati_validi))}."
                        ]
                    }
                )
            queryset = queryset.filter(stato=filtro_normalizzato)

        return queryset

    def get_serializer_class(self):
        """
        Usa PraticaCreateSerializer per le richieste POST di scrittura
        e PraticaReadSerializer per le richieste GET di lettura.
        """
        if self.request.method == "POST":
            return PraticaCreateSerializer
        return PraticaReadSerializer


class PraticaDetailView(RetrieveUpdateAPIView):
    """
    Endpoint per:
    1. GET   /api/pratiche/<id>/ -> Visualizzazione dettagliata di una singola pratica
    2. PATCH /api/pratiche/<id>/ -> Modifica controllata dello stato della pratica
    """

    queryset = Pratica.objects.select_related("cliente").all()
    http_method_names = ["get", "patch", "head", "options"]

    def get_object(self):
        """
        Recupera la pratica richiesta o solleva un errore 404 con messaggio
        comprensibile in lingua italiana.
        """
        try:
            return super().get_object()
        except Http404:
            raise NotFound(detail="Pratica non trovata.")

    def get_serializer_class(self):
        if self.request.method in ["PATCH", "PUT"]:
            return PraticaStatoUpdateSerializer
        return PraticaReadSerializer
