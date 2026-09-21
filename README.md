# Debitoo API

Prima fetta verticale della prova pratica Junior Backend Developer.

Questa versione permette soltanto di creare un cliente.

## Flusso da osservare

```text
POST /api/customers/
    -> config/urls.py
    -> customers/urls.py
    -> CustomerCreateView
    -> CustomerSerializer
    -> Customer
    -> MySQL
    -> risposta JSON
```

## Requisiti

- Docker.
- Docker Compose.

Python, Django, uv e MySQL vengono eseguiti nei container.

Non devono essere installati direttamente sul computer.

## Avvio locale

```bash
cp .env.example .env
docker compose up --build
```

L'API risponde su `http://127.0.0.1:8000/api/customers/`.

La porta accetta connessioni soltanto dal computer locale.

Il server di sviluppo non deve essere esposto direttamente sulla rete aziendale o su Internet.

Il container `api` applica automaticamente le migration prima di avviare Django.

Il container `db` conserva i dati in un volume Docker dedicato.

MySQL non espone porte verso il computer e comunica soltanto con il container dell'API.

## Prima richiesta

```bash
curl -X POST http://127.0.0.1:8000/api/customers/ \
  -H 'Content-Type: application/json' \
  -d '{"first_name":"Mario","last_name":"Rossi","email":"mario.rossi@example.com"}'
```

La risposta attesa ha stato HTTP `201 Created`.

```json
{
  "id": 1,
  "first_name": "Mario",
  "last_name": "Rossi",
  "email": "mario.rossi@example.com"
}
```

## Test

```bash
docker compose run --rm api python manage.py test
```

I test usano un database MySQL temporaneo chiamato `test_debitoo`.

## Arresto

```bash
docker compose down
```

Questo comando arresta e rimuove i container, ma conserva i dati MySQL nel volume.

Per eliminare anche i dati locali bisogna richiederlo esplicitamente con `docker compose down --volumes`.

## Pulizia completa dal computer

```bash
docker compose down --volumes --rmi local --remove-orphans
```

Questo comando rimuove i container, il volume MySQL, la rete e l'immagine costruita per il progetto.

Rimane soltanto la cartella del repository aperta nell'IDE.

## Cosa studiare in questa fetta

1. `urls.py` decide quale view riceve la richiesta.
2. La view coordina la creazione della risorsa.
3. Il serializer controlla e normalizza i dati JSON.
4. Il model descrive la tabella e i vincoli del cliente.
5. La migration applica quella struttura a MySQL.
6. I test dimostrano i comportamenti accettati e rifiutati.

Non passare ancora alle pratiche di debito.

Prima bisogna saper seguire e spiegare questo flusso senza saltare livelli.

## Uso degli strumenti AI

Codex è stato usato per preparare lo scheletro iniziale, la configurazione Docker, l'endpoint di creazione cliente e i relativi test.

Il comportamento è stato verificato eseguendo le migration e i test automatici su MySQL all'interno dei container.
