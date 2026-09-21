# Debitoo Group: prova pratica Junior Backend Developer

Questa repository contiene una piccola API REST per registrare clienti e gestire le relative pratiche debitorie.
L'applicazione usa Python, Django REST Framework e MySQL.
Docker Compose prepara l'ambiente, applica le migrazioni e avvia il server.

Per orientarsi nel codice sono disponibili due documenti:

- [Mappa del progetto](MAPPA_PROGETTO.md), con il flusso delle richieste e i principali collegamenti tra i file.
- [Metodo di sviluppo assistito da AI](LEGGIMI_METODO_DI_SVILUPPO_AI.md), con gli strumenti usati e il modo in cui ho verificato il lavoro.

## Requisiti e versioni

Per l'avvio con Docker servono:

- Docker Engine 24.0 o successivo.
- Docker Compose v2.

Le versioni usate nel progetto sono:

- Python 3.12.14, tramite l'immagine `python:3.12-slim`.
- Django 5.2.17 LTS.
- Django REST Framework 3.18.1.
- MySQL 8.4.11 LTS.
- PyMySQL 1.2.3.
- uv 0.12.10.

Il lockfile `uv.lock` fissa le dipendenze Python.
Il file `.env.example` contiene solo valori locali di esempio e non include credenziali reali.

## Struttura e scelte tecniche

Il progetto è diviso in due applicazioni Django:

- `customers` gestisce nome, cognome ed email del cliente.
- `pratiche` gestisce importo, descrizione, stato e data di apertura delle pratiche.

Una pratica appartiene a un cliente tramite una Foreign Key.
`on_delete=models.PROTECT` impedisce di eliminare un cliente che ha ancora pratiche associate.

Gli importi usano `DecimalField(max_digits=10, decimal_places=2)`.
In questo modo MySQL salva il valore come `DECIMAL(10, 2)` e non introduce gli errori di arrotondamento tipici dei `float`.
L'importo deve essere almeno `0.01` e il database applica anche un `CheckConstraint`.

Le viste che restituiscono le pratiche usano `select_related("cliente")`.
Django può così caricare pratica e cliente con una sola query invece di interrogare il database per ogni elemento della lista.

I serializer controllano i dati ricevuti e restituiscono in italiano gli errori previsti dalla traccia.

## Stati della pratica

Una pratica segue questo percorso:

```text
nuova -> in_lavorazione -> chiusa
```

Le regole sono:

1. Alla creazione lo stato è sempre `nuova`.
2. Non si può passare direttamente da `nuova` a `chiusa`.
3. Non si può tornare da `in_lavorazione` a `nuova`.
4. Una pratica `chiusa` non può essere riaperta.
5. La conferma dello stato corrente è accettata e non modifica il record.

## Avvio con Docker

Copiare la configurazione locale:

```bash
cp .env.example .env
```

Costruire e avviare i container:

```bash
docker compose up --build -d
```

Il container `db` avvia MySQL e aspetta che l'healthcheck sia positivo.
Il container `api` esegue `python manage.py migrate --noinput` e avvia Django su `http://127.0.0.1:8000`.
MySQL non espone porte verso l'host.

Per controllare lo stato:

```bash
docker compose ps
```

Per fermare i servizi:

```bash
docker compose down
```

Per eliminare anche il volume locale di MySQL:

```bash
docker compose down -v
```

## Dati di esempio

Il comando `seed_data` inserisce tre clienti e cinque pratiche fittizie:

```bash
docker compose run --rm api python manage.py seed_data
```

Può essere eseguito più volte senza duplicare i record previsti.
Per cancellare i dati presenti e ricaricare il seed:

```bash
docker compose run --rm api python manage.py seed_data --reset
```

## Test

La suite si esegue nel container:

```bash
docker compose run --rm api python manage.py test
```

I 19 test coprono:

- creazione del cliente e normalizzazione dell'email;
- email mancante, non valida o già utilizzata;
- creazione di una pratica con stato, data e identificativo automatici;
- importi negativi, nulli o non numerici;
- cliente inesistente;
- percorso valido da `nuova` a `chiusa`;
- salto di stato, retrocessione e riapertura;
- conferma idempotente dello stato;
- `PATCH` senza il campo `stato`;
- elenco, filtro, dettaglio e risposta 404.

## Esempi API

### Creare un cliente

Endpoint: `POST /api/customers/`.
È disponibile anche l'alias `POST /api/clienti/`.

```bash
curl -X POST http://127.0.0.1:8000/api/customers/ \
  -H 'Content-Type: application/json' \
  -d '{
    "first_name": "Mario",
    "last_name": "Rossi",
    "email": "mario.rossi@example.com"
  }'
```

Risposta `201 Created`:

```json
{
  "id": 1,
  "first_name": "Mario",
  "last_name": "Rossi",
  "email": "mario.rossi@example.com"
}
```

### Creare una pratica

Endpoint: `POST /api/pratiche/`.

```bash
curl -X POST http://127.0.0.1:8000/api/pratiche/ \
  -H 'Content-Type: application/json' \
  -d '{
    "cliente": 1,
    "descrizione": "Finanziamento acquisto autovettura",
    "importo": "4500.00"
  }'
```

Risposta `201 Created`:

```json
{
  "id": 1,
  "cliente_id": 1,
  "cliente": {
    "id": 1,
    "first_name": "Mario",
    "last_name": "Rossi",
    "email": "mario.rossi@example.com"
  },
  "descrizione": "Finanziamento acquisto autovettura",
  "importo": "4500.00",
  "stato": "nuova",
  "creata_il": "2026-09-21T15:19:32.405951+02:00",
  "aggiornata_il": "2026-09-21T15:19:32.405982+02:00"
}
```

### Elencare e filtrare le pratiche

```bash
curl http://127.0.0.1:8000/api/pratiche/
curl "http://127.0.0.1:8000/api/pratiche/?stato=nuova"
curl "http://127.0.0.1:8000/api/pratiche/?stato=in_lavorazione"
curl "http://127.0.0.1:8000/api/pratiche/?stato=chiusa"
```

Il filtro accetta anche il parametro `status`.

### Visualizzare una pratica

```bash
curl http://127.0.0.1:8000/api/pratiche/1/
```

### Modificare lo stato

Presa in carico:

```bash
curl -X PATCH http://127.0.0.1:8000/api/pratiche/1/ \
  -H 'Content-Type: application/json' \
  -d '{"stato": "in_lavorazione"}'
```

Chiusura:

```bash
curl -X PATCH http://127.0.0.1:8000/api/pratiche/1/ \
  -H 'Content-Type: application/json' \
  -d '{"stato": "chiusa"}'
```

La risposta `200 OK` contiene la pratica aggiornata.

## Errori

Gli errori di validazione e di dominio restituiscono JSON e un codice HTTP coerente.

Importo non valido, `400 Bad Request`:

```json
{
  "importo": ["L'importo del debito deve essere positivo e maggiore di zero (almeno 0.01 €)."]
}
```

Email già utilizzata, `400 Bad Request`:

```json
{
  "email": ["Esiste già un cliente con questa email."]
}
```

Cliente inesistente, `400 Bad Request`:

```json
{
  "cliente": ["Il cliente specificato non esiste."]
}
```

Transizione non consentita, `400 Bad Request`:

```json
{
  "stato": ["Transizione non consentita: non è possibile riaprire una pratica già chiusa."]
}
```

Pratica inesistente, `404 Not Found`:

```json
{
  "detail": "Pratica non trovata."
}
```

## Cosa non è incluso

Le funzionalità richieste dalla traccia sono complete.
Autenticazione, cancellazione, paginazione e deploy non sono stati aggiunti perché erano esplicitamente fuori dal perimetro.

In un progetto destinato alla produzione valuterei:

- autenticazione e permessi per ruolo;
- uno storico delle transizioni di stato;
- paginazione e filtri per data o importo;
- logging, monitoraggio e configurazione separata per ambiente.

## Tempo dedicato

La prima versione completa ha richiesto circa un'ora e mezza di lavoro effettivo.
Il tempo comprende analisi della traccia, implementazione assistita, test, revisione e documentazione.
Sto continuando a studiare il repository in preparazione alla presentazione tecnica.

## Assistenza AI e cassetta degli attrezzi

Ho sviluppato la prova in Antigravity IDE con l'assistenza di Gemini 3.8 Flash e Codex con GPT-5.6 Sol.
Ho usato i modelli per discutere i requisiti, implementare le parti Django, preparare i test e rivedere codice e documentazione.
Le logiche di business sono state discusse con l'AI e poi verificate eseguendo il progetto e i test su MySQL.

Nel tempo mi sono costruito NeXgen Engine come cassetta degli attrezzi per lavorare con gli assistenti AI in modo controllato.
In questa prova ho usato due componenti:

- AI Council ha sottoposto il piano a revisori indipendenti eseguiti tramite le rispettive CLI.
- `code-intel`, un tool MCP, ha analizzato l'AST e le dipendenze della codebase.

Ho usato anche alcune regole e skill operative:

- Ponytail e YAGNI per evitare codice non necessario;
- `verification-before-completion` per rieseguire test e controlli prima della consegna;
- `humanizer` per ripulire la documentazione da formulazioni artificiali senza cambiarne il contenuto tecnico.

Questa prova fa parte del mio percorso di studio.
Sto ripercorrendo il flusso completo, dal routing HTTP fino all'ORM e a MySQL, per poter spiegare e mantenere ciò che ho consegnato.
