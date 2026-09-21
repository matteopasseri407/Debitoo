from rest_framework import serializers

from customers.models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
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
        normalized_email = value.strip().lower()

        if Customer.objects.filter(email__iexact=normalized_email).exists():
            raise serializers.ValidationError(
                "Esiste già un cliente con questa email."
            )

        return normalized_email
