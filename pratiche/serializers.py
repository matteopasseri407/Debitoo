from decimal import Decimal
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from customers.models import Customer
from customers.serializers import CustomerSerializer
from pratiche.models import Pratica, StatoPratica


class PraticaReadSerializer(serializers.ModelSerializer):
    """
    Serializer di visualizzazione (output) per le pratiche.
    
    Restituisce sia l'ID del cliente sia l'oggetto cliente completo annidato,
    in modo che il consumatore dell'API abbia tutte le informazioni senza dover
    effettuare chiamate HTTP aggiuntive.
    """
    cliente_id = serializers.IntegerField(source="cliente.id", read_only=True)
    cliente = CustomerSerializer(read_only=True)

    class Meta:
        model = Pratica
        fields = [
            "id",
            "cliente_id",
            "cliente",
            "descrizione",
            "importo",
            "stato",
            "creata_il",
            "aggiornata_il",
        ]
        read_only_fields = fields


class PraticaCreateSerializer(serializers.ModelSerializer):
    """
    Serializer per la creazione di una nuova pratica.
    
    Regole implementate:
    - L'operatore deve inviare soltanto: cliente, descrizione e importo.
    - Lo stato nasce sempre come 'nuova' in automatico e non può essere impostato alla creazione.
    - L'identificativo e la data di apertura sono generati automaticamente dal database.
    - Tutti i messaggi di errore di validazione sono in lingua italiana chiara.
    """

    # PrimaryKeyRelatedField verifica che l'ID fornito esista nella tabella Customer.
    # In caso contrario, solleva un errore 400 Bad Request con messaggio esplicativo.
    cliente = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(),
        error_messages={
            "does_not_exist": "Il cliente specificato non esiste.",
            "incorrect_type": "L'identificativo del cliente deve essere un numero intero.",
            "null": "Il campo cliente non può essere nullo.",
            "required": "Il cliente è obbligatorio.",
        },
    )

    descrizione = serializers.CharField(
        max_length=255,
        error_messages={
            "blank": "La descrizione della pratica è obbligatoria.",
            "required": "La descrizione della pratica è obbligatoria.",
            "max_length": "La descrizione non può superare i 255 caratteri.",
        },
    )

    # Validazione monetaria rigorosa:
    # - min_value=Decimal("0.01") garantisce che l'importo sia strettamente positivo.
    # - max_digits=10 e decimal_places=2 controllano la precisione decimale.
    importo = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
        error_messages={
            "blank": "L'importo è obbligatorio.",
            "required": "L'importo è obbligatorio.",
            "invalid": "Inserisci un importo numerico valido con al massimo due cifre decimali.",
            "min_value": "L'importo del debito deve essere positivo e maggiore di zero (almeno 0.01 €).",
            "max_digits": "L'importo supera il numero massimo di cifre consentite.",
            "max_decimal_places": "L'importo non può avere più di due cifre decimali.",
        },
    )

    class Meta:
        model = Pratica
        fields = [
            "id",
            "cliente",
            "descrizione",
            "importo",
            "stato",
            "creata_il",
        ]
        read_only_fields = ["id", "stato", "creata_il"]

    def create(self, validated_data):
        """
        Forza lo stato iniziale della pratica a 'nuova', rispettando il vincolo di business.
        """
        validated_data["stato"] = StatoPratica.NUOVA
        return super().create(validated_data)

    def to_representation(self, instance):
        """
        Al termine della creazione, restituisce la rappresentazione completa e arricchita
        usando PraticaReadSerializer per coerenza con le GET.
        """
        return PraticaReadSerializer(instance, context=self.context).data


class PraticaStatoUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer per la modifica controllata dello stato di una pratica.
    
    Valida la macchina a stati del dominio:
    1. Lo stato deve essere uno tra 'nuova', 'in_lavorazione', 'chiusa'.
    2. Non è consentito saltare passaggi ('nuova' -> 'chiusa' vietato).
    3. Non è consentito tornare indietro ('in_lavorazione' -> 'nuova' vietato).
    4. Non è consentito riaprire pratiche chiuse ('chiusa' -> altro vietato).
    5. La riconferma dello stato corrente è idempotente (accettata senza modifiche).
    """

    stato = serializers.ChoiceField(
        choices=StatoPratica.choices,
        error_messages={
            "invalid_choice": (
                "Stato non valido. Gli stati consentiti sono: "
                f"{', '.join(sorted(StatoPratica.values))}."
            ),
            "required": "Il campo 'stato' è obbligatorio per questa operazione.",
            "blank": "Il campo 'stato' non può essere vuoto.",
        },
    )

    class Meta:
        model = Pratica
        fields = ["id", "stato"]
        read_only_fields = ["id"]

    def validate(self, attrs):
        """
        DRF nelle richieste PATCH attiva partial=True, rendendo i campi opzionali.
        Per questo endpoint lo 'stato' è l'unico scopo della chiamata: deve essere presente.
        """
        if "stato" not in attrs or not attrs["stato"]:
            raise serializers.ValidationError(
                {"stato": ["Il campo 'stato' è obbligatorio."]}
            )
        return attrs

    def validate_stato(self, nuovo_stato):
        """
        Invoca il metodo di business sul modello per validare la transizione di stato.
        Se la transizione viola le regole, converte l'eccezione Django in un errore DRF 400.
        """
        pratica = self.instance
        try:
            pratica.valida_transizione(nuovo_stato)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)

        return nuovo_stato

    def update(self, instance, validated_data):
        nuovo_stato = validated_data.get("stato")
        # Se lo stato è uguale a quello attuale, non facciamo nulla (idempotenza)
        if instance.stato != nuovo_stato:
            instance.stato = nuovo_stato
            instance.save(update_fields=["stato", "aggiornata_il"])
        return instance

    def to_representation(self, instance):
        return PraticaReadSerializer(instance, context=self.context).data
