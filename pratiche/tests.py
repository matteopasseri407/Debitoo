from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from customers.models import Customer
from pratiche.models import Pratica, StatoPratica


class PraticheApiTests(APITestCase):
    """
    Suite di test automatizzati per l'API delle pratiche debitorie.
    Copre tutti i requisiti obbligatori del PDF e i casi limite (edge cases).
    """

    def setUp(self):
        # Creazione di un cliente valido su MySQL per i test di collegamento foreign key
        self.cliente = Customer.objects.create(
            first_name="Mario",
            last_name="Rossi",
            email="mario.rossi@example.com",
        )
        self.list_create_url = reverse("pratica-list-create")

    # =========================================================================
    # REQUISITO OBBLIGATORIO 1: Creazione corretta di una pratica
    # =========================================================================
    def test_creazione_corretta_di_una_pratica(self):
        """
        Verifica che una richiesta POST valida:
        - Crei il record nel database.
        - Assegni automaticamente lo stato iniziale 'nuova'.
        - Assegni automaticamente la data di apertura (creata_il).
        - Generi un identificativo univoco (id).
        - Risponda con HTTP 201 Created.
        """
        payload = {
            "cliente": self.cliente.id,
            "descrizione": "Finanziamento auto non saldato",
            "importo": "1500.50",
        }

        response = self.client.post(self.list_create_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Pratica.objects.count(), 1)

        pratica = Pratica.objects.first()
        self.assertEqual(pratica.cliente, self.cliente)
        self.assertEqual(pratica.descrizione, "Finanziamento auto non saldato")
        self.assertEqual(pratica.importo, Decimal("1500.50"))
        # Verifica assegnazione automatica stato iniziale
        self.assertEqual(pratica.stato, StatoPratica.NUOVA)
        # Verifica timestamp apertura presente
        self.assertIsNotNone(pratica.creata_il)
        # Verifica payload di risposta
        self.assertEqual(response.data["stato"], "nuova")
        self.assertEqual(response.data["importo"], "1500.50")
        self.assertEqual(response.data["cliente"]["id"], self.cliente.id)

    # =========================================================================
    # REQUISITO OBBLIGATORIO 2: Rifiuto di una pratica con importo non valido
    # =========================================================================
    def test_rifiuto_pratica_con_importo_negativo(self):
        """
        Verifica che un importo negativo venga respinto con HTTP 400 Bad Request
        e messaggio di errore comprensibile in italiano.
        """
        payload = {
            "cliente": self.cliente.id,
            "descrizione": "Debito errato",
            "importo": "-50.00",
        }

        response = self.client.post(self.list_create_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Pratica.objects.count(), 0)
        self.assertIn("importo", response.data)
        self.assertEqual(
            response.data["importo"][0],
            "L'importo del debito deve essere positivo e maggiore di zero (almeno 0.01 €).",
        )

    def test_rifiuto_pratica_con_importo_zero(self):
        """
        Verifica che un importo pari a 0.00 venga respinto.
        """
        payload = {
            "cliente": self.cliente.id,
            "descrizione": "Debito nullo",
            "importo": "0.00",
        }

        response = self.client.post(self.list_create_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Pratica.objects.count(), 0)
        self.assertIn("importo", response.data)

    def test_rifiuto_pratica_con_importo_non_numerico(self):
        """
        Verifica che una stringa non numerica nell'importo venga respinta.
        """
        payload = {
            "cliente": self.cliente.id,
            "descrizione": "Debito testo",
            "importo": "mille-euro",
        }

        response = self.client.post(self.list_create_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Pratica.objects.count(), 0)

    # =========================================================================
    # REQUISITO OBBLIGATORIO 3: Rifiuto del tentativo di riaprire una pratica chiusa
    # =========================================================================
    def test_rifiuto_tentativo_di_riaprire_pratica_chiusa(self):
        """
        Verifica che tentando di portare una pratica 'chiusa' a 'nuova' o 'in_lavorazione'
        la richiesta venga respinta con HTTP 400 Bad Request e messaggio esplicativo in italiano.
        """
        pratica_chiusa = Pratica.objects.create(
            cliente=self.cliente,
            descrizione="Pratica archiviata",
            importo=Decimal("800.00"),
            stato=StatoPratica.CHIUSA,
        )

        url_modifica = reverse("pratica-detail", kwargs={"pk": pratica_chiusa.id})

        # Tentativo 1: passaggio a 'in_lavorazione'
        response_in_lav = self.client.patch(
            url_modifica,
            {"stato": "in_lavorazione"},
            format="json",
        )
        self.assertEqual(response_in_lav.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "Transizione non consentita: non è possibile riaprire una pratica già chiusa.",
            response_in_lav.data["stato"][0],
        )

        # Tentativo 2: passaggio a 'nuova'
        response_nuova = self.client.patch(
            url_modifica,
            {"stato": "nuova"},
            format="json",
        )
        self.assertEqual(response_nuova.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "Transizione non consentita: non è possibile riaprire una pratica già chiusa.",
            response_nuova.data["stato"][0],
        )

        # Lo stato sul database deve rimanere tassativamente 'chiusa'
        pratica_chiusa.refresh_from_db()
        self.assertEqual(pratica_chiusa.stato, StatoPratica.CHIUSA)

    # =========================================================================
    # TEST MACCHINA A STATI: Transizioni lecite e illecite
    # =========================================================================
    def test_transizione_valida_da_nuova_a_in_lavorazione_e_poi_a_chiusa(self):
        """
        Verifica il percorso felice completo: nuova -> in_lavorazione -> chiusa.
        """
        pratica = Pratica.objects.create(
            cliente=self.cliente,
            descrizione="Percorso regolare",
            importo=Decimal("250.00"),
            stato=StatoPratica.NUOVA,
        )
        url = reverse("pratica-detail", kwargs={"pk": pratica.id})

        # Passo 1: presa in carico (nuova -> in_lavorazione)
        res1 = self.client.patch(url, {"stato": "in_lavorazione"}, format="json")
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        pratica.refresh_from_db()
        self.assertEqual(pratica.stato, StatoPratica.IN_LAVORAZIONE)

        # Passo 2: chiusura (in_lavorazione -> chiusa)
        res2 = self.client.patch(url, {"stato": "chiusa"}, format="json")
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        pratica.refresh_from_db()
        self.assertEqual(pratica.stato, StatoPratica.CHIUSA)

    def test_rifiuto_salto_passaggio_da_nuova_a_chiusa(self):
        """
        Non è consentito saltare passaggi (nuova -> chiusa direttamente è vietato).
        """
        pratica = Pratica.objects.create(
            cliente=self.cliente,
            descrizione="Tentativo salto",
            importo=Decimal("100.00"),
            stato=StatoPratica.NUOVA,
        )
        url = reverse("pratica-detail", kwargs={"pk": pratica.id})

        response = self.client.patch(url, {"stato": "chiusa"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non è possibile saltare passaggi", response.data["stato"][0])
        pratica.refresh_from_db()
        self.assertEqual(pratica.stato, StatoPratica.NUOVA)

    def test_rifiuto_ritorno_a_fase_precedente(self):
        """
        Non è consentito tornare a una fase precedente (in_lavorazione -> nuova è vietato).
        """
        pratica = Pratica.objects.create(
            cliente=self.cliente,
            descrizione="Tentativo retrocessione",
            importo=Decimal("300.00"),
            stato=StatoPratica.IN_LAVORAZIONE,
        )
        url = reverse("pratica-detail", kwargs={"pk": pratica.id})

        response = self.client.patch(url, {"stato": "nuova"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non è possibile tornare a una fase precedente", response.data["stato"][0])
        pratica.refresh_from_db()
        self.assertEqual(pratica.stato, StatoPratica.IN_LAVORAZIONE)

    def test_conferma_stato_gia_presente_accettata_senza_modifiche(self):
        """
        Specifica: 'Una richiesta che conferma lo stato già presente può essere accettata senza apportare modifiche.'
        """
        pratica = Pratica.objects.create(
            cliente=self.cliente,
            descrizione="Idempotenza stato",
            importo=Decimal("400.00"),
            stato=StatoPratica.IN_LAVORAZIONE,
        )
        url = reverse("pratica-detail", kwargs={"pk": pratica.id})

        response = self.client.patch(url, {"stato": "in_lavorazione"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pratica.refresh_from_db()
        self.assertEqual(pratica.stato, StatoPratica.IN_LAVORAZIONE)

    def test_rifiuto_stato_non_esistente(self):
        """
        Verifica il rifiuto di una stringa di stato non censita nel sistema.
        """
        pratica = Pratica.objects.create(
            cliente=self.cliente,
            descrizione="Stato fittizio",
            importo=Decimal("150.00"),
            stato=StatoPratica.NUOVA,
        )
        url = reverse("pratica-detail", kwargs={"pk": pratica.id})

        response = self.client.patch(url, {"stato": "in_sospeso"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("stato", response.data)

    # =========================================================================
    # TEST ELENCO, FILTRI E DETTAGLIO
    # =========================================================================
    def test_elenco_pratiche_e_filtro_per_stato(self):
        """
        Verifica l'elenco generale e il corretto funzionamento del filtro query param '?stato='.
        """
        p1 = Pratica.objects.create(
            cliente=self.cliente,
            descrizione="Pratica 1",
            importo=Decimal("100.00"),
            stato=StatoPratica.NUOVA,
        )
        p2 = Pratica.objects.create(
            cliente=self.cliente,
            descrizione="Pratica 2",
            importo=Decimal("200.00"),
            stato=StatoPratica.IN_LAVORAZIONE,
        )

        # Elenco completo senza filtri
        res_all = self.client.get(self.list_create_url)
        self.assertEqual(res_all.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_all.data), 2)

        # Filtro per stato 'nuova'
        res_nuove = self.client.get(self.list_create_url, {"stato": "nuova"})
        self.assertEqual(res_nuove.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_nuove.data), 1)
        self.assertEqual(res_nuove.data[0]["id"], p1.id)

        # Filtro per stato 'in_lavorazione'
        res_lav = self.client.get(self.list_create_url, {"stato": "in_lavorazione"})
        self.assertEqual(res_lav.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_lav.data), 1)
        self.assertEqual(res_lav.data[0]["id"], p2.id)

    def test_dettaglio_pratica_esistente_e_404_inesistente(self):
        """
        Verifica visualizzazione singola pratica e messaggio 404 in italiano se inesistente.
        """
        pratica = Pratica.objects.create(
            cliente=self.cliente,
            descrizione="Pratica singola",
            importo=Decimal("500.00"),
            stato=StatoPratica.NUOVA,
        )
        url_esistente = reverse("pratica-detail", kwargs={"pk": pratica.id})
        res_ok = self.client.get(url_esistente)
        self.assertEqual(res_ok.status_code, status.HTTP_200_OK)
        self.assertEqual(res_ok.data["id"], pratica.id)

        # Pratica non trovata (ID inesistente)
        url_inesistente = reverse("pratica-detail", kwargs={"pk": 99999})
        res_404 = self.client.get(url_inesistente)
        self.assertEqual(res_404.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(res_404.data["detail"], "Pratica non trovata.")

    def test_rifiuto_creazione_con_cliente_inesistente(self):
        """
        Verifica che tentando di associare una pratica a un cliente inesistente,
        venga restituito 400 Bad Request con messaggio in italiano.
        """
        payload = {
            "cliente": 99999,
            "descrizione": "Debito fantasma",
            "importo": "100.00",
        }
        response = self.client.post(self.list_create_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["cliente"][0], "Il cliente specificato non esiste.")
