from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class StatoPratica(models.TextChoices):
    """
    Rappresenta il ciclo di vita formale di una pratica debitoria.
    
    Usiamo TextChoices di Django:
    - Il primo valore ('nuova') è il valore salvato nel database MySQL (VARCHAR).
    - Il secondo valore ('Nuova') è l'etichetta leggibile per l'interfaccia/admin.
    """
    NUOVA = "nuova", "Nuova"
    IN_LAVORAZIONE = "in_lavorazione", "In lavorazione"
    CHIUSA = "chiusa", "Chiusa"


class Pratica(models.Model):
    """
    Modello per la gestione di una pratica di debito.

    Regole di business implementate:
    1. Collegamento a un cliente registrato (Foreign Key 1 a N: un cliente può avere più pratiche).
    2. Descrizione breve obbligatoria di cosa si tratta.
    3. Importo debitorio positivo con precisione di 2 cifre decimali (DecimalField).
    4. Identificativo univoco auto-incrementante generato dal database.
    5. Data e ora di apertura registrate in modo automatico (auto_now_add).
    6. Ciclo di vita a senso unico: nuova -> in_lavorazione -> chiusa.
    """

    # Mappa delle transizioni di stato consentite.
    # Da ogni stato è consentito transitare solo allo stato successivo o confermare lo stesso (idempotenza).
    TRANSIZIONI_PERMESSE = {
        StatoPratica.NUOVA: {StatoPratica.NUOVA, StatoPratica.IN_LAVORAZIONE},
        StatoPratica.IN_LAVORAZIONE: {StatoPratica.IN_LAVORAZIONE, StatoPratica.CHIUSA},
        StatoPratica.CHIUSA: {StatoPratica.CHIUSA},
    }

    # Relazione con il cliente:
    # - on_delete=models.PROTECT impedisce l'eliminazione accidentale di un cliente
    #   se esistono ancora pratiche collegate a suo nome (integrità referenziale).
    # - related_name="pratiche" permette di fare cliente.pratiche.all()
    cliente = models.ForeignKey(
        "customers.Customer",
        on_delete=models.PROTECT,
        related_name="pratiche",
        verbose_name="Cliente intestatario",
    )

    # Descrizione sintetica della situazione debitoria
    descrizione = models.CharField(
        max_length=255,
        verbose_name="Descrizione sintetica del debito",
    )

    # L'importo del debito deve essere monetario esatto.
    # DecimalField evita i problemi di arrotondamento tipici dei float (standard IEEE 754).
    # MinValueValidator impone che l'importo sia strettamente positivo (minimo 1 centesimo di euro).
    importo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(
                Decimal("0.01"),
                message="L'importo del debito deve essere maggiore di zero.",
            )
        ],
        verbose_name="Importo debito (€)",
    )

    # Stato corrente della pratica: parte sempre da 'nuova' alla creazione
    stato = models.CharField(
        max_length=20,
        choices=StatoPratica.choices,
        default=StatoPratica.NUOVA,
        verbose_name="Stato pratica",
    )

    # Timestamp di apertura generato automaticamente all'INSERT
    creata_il = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data e ora apertura",
    )

    # Timestamp aggiornato automaticamente a ogni salvataggio/modifica
    aggiornata_il = models.DateTimeField(
        auto_now=True,
        verbose_name="Data e ora ultimo aggiornamento",
    )

    class Meta:
        verbose_name = "Pratica"
        verbose_name_plural = "Pratiche"
        ordering = ["-creata_il"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(importo__gt=Decimal("0.00")),
                name="pratica_importo_positivo",
            ),
        ]

    def clean(self):
        super().clean()
        if self.importo is not None and self.importo <= Decimal("0.00"):
            raise ValidationError(
                {"importo": "L'importo del debito deve essere maggiore di zero."}
            )

    def __str__(self):
        return f"Pratica #{self.pk} - {self.cliente} [{self.stato}]"

    def puo_transitare_a(self, nuovo_stato: str) -> bool:
        """
        Verifica se il passaggio dallo stato corrente a 'nuovo_stato' è consentito.
        """
        stati_validi = self.TRANSIZIONI_PERMESSE.get(self.stato, set())
        return nuovo_stato in stati_validi

    def valida_transizione(self, nuovo_stato: str):
        """
        Valida la transizione di stato e solleva una ValidationError con
        un messaggio dettagliato e comprensibile in lingua italiana se non valida.
        """
        stati_esistenti = set(StatoPratica.values)
        if nuovo_stato not in stati_esistenti:
            raise ValidationError(
                f"Lo stato '{nuovo_stato}' non è valido. "
                f"Gli stati ammessi sono: {', '.join(sorted(stati_esistenti))}."
            )

        if not self.puo_transitare_a(nuovo_stato):
            # Dettaglio motivazione rifiuto per guidare l'operatore
            if self.stato == StatoPratica.CHIUSA:
                raise ValidationError(
                    "Transizione non consentita: non è possibile riaprire una pratica già chiusa."
                )
            if self.stato == StatoPratica.NUOVA and nuovo_stato == StatoPratica.CHIUSA:
                raise ValidationError(
                    "Transizione non consentita: non è possibile saltare passaggi "
                    "passando direttamente da 'nuova' a 'chiusa'. La pratica deve prima essere presa in lavorazione."
                )
            if self.stato == StatoPratica.IN_LAVORAZIONE and nuovo_stato == StatoPratica.NUOVA:
                raise ValidationError(
                    "Transizione non consentita: non è possibile tornare a una fase precedente ('in_lavorazione' -> 'nuova')."
                )
            raise ValidationError(
                f"Transizione non consentita dallo stato '{self.stato}' allo stato '{nuovo_stato}'."
            )
