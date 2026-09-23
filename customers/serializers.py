from django.db import IntegrityError, transaction
from rest_framework import serializers

from customers.models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    """
    Serializer per la validazione e deserializzazione dei dati del cliente.

    Funzionalità e controlli:
    1. Obbligatorietà di nome, cognome ed email con messaggi in italiano.
    2. Validazione sintattica dell'indirizzo email.
    3. Normalizzazione dell'email (strip degli spazi e conversione in minuscolo).
    4. Controllo esplicito di unicità case-insensitive prima del salvataggio nel database.
    """

    duplicate_email_message = "Esiste già un cliente con questa email."

    email = serializers.EmailField(
        max_length=Customer._meta.get_field("email").max_length,
        error_messages={
            "blank": "L'email è obbligatoria.",
            "invalid": "Inserisci un indirizzo email valido.",
            "required": "L'email è obbligatoria.",
        }
    )

    class Meta:
        model = Customer
        fields = ["id", "first_name", "last_name", "email"]
        read_only_fields = ["id"]
        extra_kwargs = {
            "first_name": {
                "error_messages": {
                    "blank": "Il nome è obbligatorio.",
                    "required": "Il nome è obbligatorio.",
                }
            },
            "last_name": {
                "error_messages": {
                    "blank": "Il cognome è obbligatorio.",
                    "required": "Il cognome è obbligatorio.",
                }
            },
        }

    def validate_email(self, value):
        """
        Pulisce e verifica l'unicità dell'email ignorando differenze di maiuscole/minuscole.
        Es: 'Mario.Rossi@example.com' e 'mario.rossi@example.com' collidono.
        """
        normalized_email = value.strip().lower()

        # Query di controllo su MySQL con predicato iexact (case-insensitive)
        if Customer.objects.filter(email__iexact=normalized_email).exists():
            raise serializers.ValidationError(
                self.duplicate_email_message
            )

        return normalized_email

    def create(self, validated_data):
        try:
            with transaction.atomic():
                return super().create(validated_data)
        except IntegrityError as exc:
            # MySQL 1062: another request may insert the email after validation.
            if exc.args[0] != 1062:
                raise
            raise serializers.ValidationError(
                {"email": [self.duplicate_email_message]}
            ) from exc
