from django.db import models


class Customer(models.Model):
    """
    Modello per la registrazione e persistenza dei clienti di Debitoo Group.

    Regole di business implementate:
    1. Nome e cognome obbligatori per l'identificazione della persona fisica.
    2. Indirizzo email univoco nel sistema (unique=True crea un indice UNIQUE su MySQL).
    3. Identificativo numerico univoco generato automaticamente (BigAutoField primario).
    """

    first_name = models.CharField(
        max_length=100,
        verbose_name="Nome",
    )
    last_name = models.CharField(
        max_length=100,
        verbose_name="Cognome",
    )
    # unique=True garantisce sia la validazione applicativa sia il vincolo UNIQUE a livello di tabella MySQL.
    email = models.EmailField(
        unique=True,
        verbose_name="Indirizzo Email",
    )

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clienti"
        ordering = ["id"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
