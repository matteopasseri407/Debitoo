"""
Comando personalizzato Django per caricare dati di esempio realistici nel database MySQL.

Esecuzione:
    python manage.py seed_data
    oppure via Docker:
    docker compose run --rm api python manage.py seed_data
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction

from customers.models import Customer
from pratiche.models import Pratica, StatoPratica


class Command(BaseCommand):
    help = "Carica dati fittizi di esempio (clienti e pratiche debitorie) nel database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Elimina i dati esistenti prima di caricare i dati di esempio.",
        )

    def handle(self, *args, **options):
        reset = options.get("reset", False)

        with transaction.atomic():
            if reset:
                self.stdout.write(self.style.WARNING("Rimozione dati esistenti in corso..."))
                Pratica.objects.all().delete()
                Customer.objects.all().delete()
                self.stdout.write(self.style.WARNING("Dati precedenti rimossi con successo."))

            self.stdout.write("Caricamento clienti di esempio...")

            # Creazione o recupero clienti fittizi
            mario, _ = Customer.objects.get_or_create(
                email="mario.rossi@example.com",
                defaults={"first_name": "Mario", "last_name": "Rossi"},
            )
            laura, _ = Customer.objects.get_or_create(
                email="laura.bianchi@example.com",
                defaults={"first_name": "Laura", "last_name": "Bianchi"},
            )
            giuseppe, _ = Customer.objects.get_or_create(
                email="giuseppe.verdi@example.com",
                defaults={"first_name": "Giuseppe", "last_name": "Verdi"},
            )

            self.stdout.write(self.style.SUCCESS("✓ 3 clienti registrati."))

            self.stdout.write("Caricamento pratiche debitorie di esempio...")

            # Pratiche di prova con diversi stati e importi
            dati_pratiche = [
                {
                    "cliente": mario,
                    "descrizione": "Finanziamento acquisto autovettura",
                    "importo": Decimal("4500.00"),
                    "stato": StatoPratica.NUOVA,
                },
                {
                    "cliente": mario,
                    "descrizione": "Scoperto di conto corrente bancario",
                    "importo": Decimal("1250.50"),
                    "stato": StatoPratica.IN_LAVORAZIONE,
                },
                {
                    "cliente": laura,
                    "descrizione": "Residuo carta di credito revolving",
                    "importo": Decimal("850.00"),
                    "stato": StatoPratica.NUOVA,
                },
                {
                    "cliente": laura,
                    "descrizione": "Prestito personale accordato e saldato",
                    "importo": Decimal("3200.00"),
                    "stato": StatoPratica.CHIUSA,
                },
                {
                    "cliente": giuseppe,
                    "descrizione": "Sollecito pagamento utenze luce e gas",
                    "importo": Decimal("340.75"),
                    "stato": StatoPratica.IN_LAVORAZIONE,
                },
            ]

            pratiche_create = 0
            for item in dati_pratiche:
                pratica, created = Pratica.objects.get_or_create(
                    cliente=item["cliente"],
                    descrizione=item["descrizione"],
                    defaults={
                        "importo": item["importo"],
                        "stato": item["stato"],
                    },
                )
                if created:
                    pratiche_create += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Caricamento completato con successo! ({pratiche_create} nuove pratiche caricate, "
                    f"totale pratiche nel DB: {Pratica.objects.count()})."
                )
            )
