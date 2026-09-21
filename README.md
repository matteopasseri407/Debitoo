# Debitoo Group — Prova Pratica Junior Backend Developer

API REST sviluppata in **Python** con **Django** e **Django REST Framework (DRF)**, con database relazionale **MySQL 8.4**, interamente containerizzata tramite **Docker** e **Docker Compose**.

Il sistema consente agli operatori di registrare clienti e gestire le relative pratiche debitorie, garantendo l'integrità dei dati contabili e imponendo una macchina a stati rigorosa a senso unico per il ciclo di vita delle posizioni debitorie.

> Per una consultazione rapida della struttura del codice e del flusso delle richieste:
> - **[Mappa Visuale e Concettuale del Progetto](MAPPA_PROGETTO.md)**: diagrammi di sequenza, metafora dei componenti Django e albero dei file.
> - **[Metodo di Sviluppo Assistito da AI](METODO_DI_SVILUPPO_AI.md)**: approfondimento sui principi di ingegneria adottati (fette verticali, regola Ponytail, scansione AST via MCP e revisione multi-modello).

---

## Indice

1. [Requisiti e Versioni](#requisiti-e-versioni)
2. [Scelte Architetturali e di Design](#scelte-architetturali-e-di-design)
3. [Macchina a Stati delle Pratiche](#macchina-a-stati-delle-pratiche)
4. [Avvio Rapido con Docker](#avvio-rapido-con-docker)
5. [Caricamento Dati di Prova (Seed)](#caricamento-dati-di-prova-seed)
6. [Esecuzione Test Automatici](#esecuzione-test-automatici)
7. [Specifiche e Esempi Chiamate API (cURL)](#specifiche-e-esempi-chiamate-api-curl)
8. [Gestione degli Errori in Italiano](#gestione-degli-errori-in-italiano)
9. [Miglioramenti Futuri](#miglioramenti-futuri)
10. [Tempo Dedicato](#tempo-dedicato)
11. [Dichiarazione Strumenti AI](#dichiarazione-strumenti-ai)

---

## Requisiti e Versioni

Il progetto è progettato per essere eseguito interamente in container isolati, senza necessità di installare Python o MySQL sul sistema host:

- **Docker Engine:** versione >= 24.0
- **Docker Compose:** versione v2
- **Python:** 3.12.14 (immagine `python:3.12-slim`)
- **Django:** 5.2.17 LTS
- **Django REST Framework (DRF):** 3.18.1
- **MySQL:** 8.4.11 LTS
- **PyMySQL:** 1.2.3
- **uv:** 0.12.10 (gestore di dipendenze e lockfile)

---

## Scelte Architetturali e di Design

### 1. Separazione Modulare delle Applicazioni
Il progetto è suddiviso in due app distinte:
- `customers`: gestisce l'anagrafica delle persone fisiche (nome, cognome, email univoca).
- `pratiche`: gestisce il ciclo di vita delle posizioni debitorie, l'importo economico, le date di apertura e le transizioni di stato.

### 2. Precisione Monetaria (`DecimalField`)
Per la gestione dell'importo debitorio è stato adottato tassativamente `models.DecimalField(max_digits=10, decimal_places=2)`.
*Motivazione tecnica:* L'uso dei tipi in virgola mobile (`float`) introduce imprecisioni binarie di arrotondamento (standard IEEE 754), inaccettabili in ambito finanziario e contabile. `DecimalField` mappa direttamente sul tipo SQL nativo `DECIMAL(10, 2)` di MySQL, garantendo calcoli esatti al centesimo di euro.

### 3. Integrità Referenziale (`on_delete=models.PROTECT`)
Il collegamento tra Pratica e Cliente è modellato tramite Foreign Key 1 a N con politica `models.PROTECT`. In questo modo si impedisce l'eliminazione accidentale di un cliente che ha ancora pratiche collegate nel database, prevenendo orfanezze di dati o perdite di tracciabilità contabile.

### 4. Ottimizzazione Query ORM (`select_related`)
Nella lettura delle pratiche (`PraticaListCreateView` e `PraticaDetailView`) viene applicato `.select_related('cliente')`.
*Motivazione tecnica:* Evita il celebre problema delle query N+1: con una singola `INNER JOIN` a livello di MySQL, Django estrae sia i dati della pratica sia quelli anagrafici del cliente associato in una sola interrogazione, abbattendo la latenza di rete e il carico sul database.

### 5. Gestione Centralizzata e Messaggi in Italiano
Tutti i messaggi di validazione (campi obbligatori, email malformata, importo negativo o nullo, violazione di transizione di stato, risorsa non trovata) sono esplicitati in lingua italiana chiara e immediatamente comprensibile.

---

## Macchina a Stati delle Pratiche

Il ciclo di vita di una pratica segue una sequenza rigorosa e irreversibile:

```text
[ nuova ]  ──────>  [ in_lavorazione ]  ──────>  [ chiusa ]
   │                       │                       │
   └── (conferma)          └── (conferma)          └── (conferma)
```

### Regole applicate:
1. **Creazione automatica:** Ogni nuova pratica nasce tassativamente nello stato `nuova`. L'operatore non deve né può impostare stati diversi alla creazione.
2. **Nessun salto di stato:** Da `nuova` non è consentito saltare direttamente a `chiusa`. La pratica deve prima essere presa in carico (`in_lavorazione`).
3. **Nessun ritorno al passato:** Non è consentito tornare da `in_lavorazione` a `nuova`.
4. **Nessuna riapertura:** Una volta che una pratica è `chiusa`, non può più essere portata a `in_lavorazione` o `nuova`.
5. **Idempotenza:** Se viene inviata una richiesta di modifica che conferma lo stato già attivo (es. da `in_lavorazione` a `in_lavorazione`), la richiesta viene accettata con HTTP `200 OK` senza generare errori o modifiche anomale.

---

## Avvio Rapido con Docker

### 1. Clonazione e configurazione variabili d'ambiente
```bash
cp .env.example .env
```

### 2. Avvio dei container
```bash
docker compose up --build -d
```
All'avvio:
- Il container `db` avvia MySQL 8.4 e attende il superamento dell'healthcheck.
- L'entrypoint del container `api` esegue in automatico `python manage.py migrate --noinput`.
- Il server di sviluppo Django risponde su `http://127.0.0.1:8000`.

### 3. Verifica dello stato dei servizi
```bash
docker compose ps
```

### 4. Arresto dei container
```bash
docker compose down
```
*Nota:* per eliminare anche il volume persistente dei dati MySQL: `docker compose down -v`.

---

## Caricamento Dati di Prova (Seed)

È disponibile un comando personalizzato Django per popolare il database con clienti e pratiche fittizie di esempio:

```bash
docker compose run --rm api python manage.py seed_data
```

Per resettare il database e ricaricare i dati puliti:
```bash
docker compose run --rm api python manage.py seed_data --reset
```

Il comando inserisce 3 clienti e 5 pratiche distribuite nei tre diversi stati (`nuova`, `in_lavorazione`, `chiusa`) con importi realistici.

---

## Esecuzione Test Automatici

I test automatici possono essere eseguiti direttamente all'interno dell'ambiente containerizzato con:

```bash
docker compose run --rm api python manage.py test
```

### Copertura dei test:
La suite include **19 test automatici** che coprono sia i test minimi richiesti dalla traccia sia tutti i casi limite:
1. **Creazione corretta di una pratica** (con stato iniziale `nuova`, timestamp automatico, importo a 2 decimali e ID auto-incrementante).
2. **Rifiuto di pratiche con importo non valido** (valori negativi, importo pari a zero, stringhe non numeriche).
3. **Rifiuto categorico di riaprire una pratica chiusa** (tentativi verso `in_lavorazione` e verso `nuova`).
4. **Rifiuto salto di passaggio** (da `nuova` direttamente a `chiusa`).
5. **Rifiuto retrocessione di stato** (da `in_lavorazione` a `nuova`).
6. **Verifica idempotenza** (conferma dello stesso stato accettata senza errori).
7. **Rifiuto payload vuoto o senza stato** (richieste `PATCH {}` intercettate con HTTP 400 invece di 500).
8. **Rifiuto cliente inesistente** (Foreign Key non valida intercettata con HTTP 400 e messaggio in italiano).
9. **Elenco e filtro pratiche per stato** (`?stato=nuova`, `?stato=in_lavorazione`, `?stato=chiusa`).
10. **Visualizzazione dettaglio e gestione 404** (su identificativi inesistenti).
11. **Suite clienti** (creazione valida, rifiuto email mancante, rifiuto formato email non valido, blocco duplicati case-insensitive).

---

## Specifiche e Esempi Chiamate API (cURL)

### 1. Creazione di un Cliente
- **Endpoint:** `POST /api/customers/` (disponibile anche alias `POST /api/clienti/`)
- **Request:**
```bash
curl -X POST http://127.0.0.1:8000/api/customers/ \
  -H 'Content-Type: application/json' \
  -d '{
    "first_name": "Mario",
    "last_name": "Rossi",
    "email": "mario.rossi@example.com"
  }'
```
- **Response (201 Created):**
```json
{
  "id": 1,
  "first_name": "Mario",
  "last_name": "Rossi",
  "email": "mario.rossi@example.com"
}
```

---

### 2. Creazione di una Pratica
- **Endpoint:** `POST /api/pratiche/`
- **Request:**
```bash
curl -X POST http://127.0.0.1:8000/api/pratiche/ \
  -H 'Content-Type: application/json' \
  -d '{
    "cliente": 1,
    "descrizione": "Finanziamento acquisto autovettura",
    "importo": "4500.00"
  }'
```
- **Response (201 Created):**
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

---

### 3. Elenco di tutte le Pratiche
- **Endpoint:** `GET /api/pratiche/`
- **Request:**
```bash
curl -X GET http://127.0.0.1:8000/api/pratiche/
```
- **Response (200 OK):**
```json
[
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
]
```

---

### 4. Filtro delle Pratiche per Stato
- **Endpoint:** `GET /api/pratiche/?stato=<stato>` (supporta anche `?status=<stato>`)
- **Esempi:**
```bash
# Pratiche appena aperte
curl -X GET "http://127.0.0.1:8000/api/pratiche/?stato=nuova"

# Pratiche in lavorazione
curl -X GET "http://127.0.0.1:8000/api/pratiche/?stato=in_lavorazione"

# Pratiche concluse
curl -X GET "http://127.0.0.1:8000/api/pratiche/?stato=chiusa"
```

---

### 5. Dettaglio di una Singola Pratica
- **Endpoint:** `GET /api/pratiche/<id>/`
- **Request:**
```bash
curl -X GET http://127.0.0.1:8000/api/pratiche/1/
```
- **Response (200 OK):**
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

---

### 6. Modifica dello Stato di una Pratica
- **Endpoint:** `PATCH /api/pratiche/<id>/`
- **Presa in carico (`nuova` -> `in_lavorazione`):**
```bash
curl -X PATCH http://127.0.0.1:8000/api/pratiche/1/ \
  -H 'Content-Type: application/json' \
  -d '{"stato": "in_lavorazione"}'
```
- **Chiusura pratica (`in_lavorazione` -> `chiusa`):**
```bash
curl -X PATCH http://127.0.0.1:8000/api/pratiche/1/ \
  -H 'Content-Type: application/json' \
  -d '{"stato": "chiusa"}'
```
- **Response (200 OK):** restituisce l'oggetto aggiornato con il nuovo stato e il timestamp `aggiornata_il`.

---

## Gestione degli Errori in Italiano

Gli errori di dominio e di validazione previsti dalla traccia restituiscono codici HTTP appropriati e payload JSON leggibili:

### 1. Dati obbligatori mancanti o importo errato (400 Bad Request)
```json
{
  "importo": ["L'importo del debito deve essere positivo e maggiore di zero (almeno 0.01 €)."]
}
```

### 2. Email duplicata (400 Bad Request)
```json
{
  "email": ["Esiste già un cliente con questa email."]
}
```

### 3. Cliente inesistente (400 Bad Request)
```json
{
  "cliente": ["Il cliente specificato non esiste."]
}
```

### 4. Salto di passaggio non consentito (400 Bad Request)
```json
{
  "stato": ["Transizione non consentita: non è possibile saltare passaggi passando direttamente da 'nuova' a 'chiusa'. La pratica deve prima essere presa in lavorazione."]
}
```

### 5. Tentativo di riaprire una pratica chiusa (400 Bad Request)
```json
{
  "stato": ["Transizione non consentita: non è possibile riaprire una pratica già chiusa."]
}
```

### 6. Pratica non trovata (404 Not Found)
```json
{
  "detail": "Pratica non trovata."
}
```

---

## Miglioramenti Futuri

In un'ottica di evoluzione a prodotto enterprise, i passi naturali successivi comprenderebbero:
1. **Autenticazione e Autorizzazione:** integrazione di token JWT o OAuth2 con differenziazione dei ruoli (es. operatore junior, supervisore autorizzato alla chiusura o riapertura straordinaria).
2. **Paginazione dei risultati:** introduzione di `PageNumberPagination` su `/api/pratiche/` per supportare volumi da centinaia di migliaia di pratiche senza decadimento prestazionale.
3. **Audit Log delle transizioni:** tabella storica per tracciare chi, quando e con quale motivazione ha modificato lo stato di ciascuna pratica.
4. **Filtri avanzati:** filtro per data di apertura (`creata_il__gte`, `creata_il__lte`) e per range di debito.

## Tempo Dedicato

La prima versione completa ha richiesto circa un'ora e mezza di lavoro effettivo tra analisi della traccia, implementazione assistita, test, revisione e documentazione.
Lo studio del progetto continua in preparazione alla presentazione tecnica.

## Dichiarazione Strumenti AI

Durante lo sviluppo ho usato **Codex** e **Gemini 3.8 Flash** come assistenti di analisi, pair programming e studio.
Anche le logiche di business e le scelte implementative sono state discusse con il supporto dell'AI, non soltanto la documentazione finale.

Il supporto AI ha riguardato:

- analisi dei requisiti e modellazione della macchina a stati;
- impostazione dei modelli Django, dei serializer e dell'ambiente Docker Compose;
- scrittura e revisione dei test, compresi i casi limite;
- revisione del codice, messaggi di errore e documentazione tecnica.

Per lo stress-test del piano ho usato **AI Council**, una funzione di **NeXgen Engine** che consulta altri modelli tramite le rispettive CLI e li usa come revisori indipendenti.
Per analizzare la struttura del repository ho usato **`code-intel`**, un tool MCP di NeXgen Engine che legge l'AST, genera la mappa dei simboli e individua le dipendenze tra le parti del codice.

Questa prova è anche un percorso di studio.
Sto ripercorrendo il repository file per file, dal routing HTTP fino all'ORM e a MySQL, per comprendere, spiegare e manutenere ogni parte del progetto.
Il comportamento è stato verificato eseguendo l'intera suite di 19 test nei container Docker su MySQL 8.4.
