# Debitoo Group: prova pratica Junior Backend Developer

API REST in Python, Django REST Framework e MySQL per registrare clienti e gestire pratiche debitorie.
L'ambiente gira con Docker Compose.

Documentazione collegata:

- [Mappa della codebase](MAPPA_PROGETTO.md).
- [Metodo di sviluppo assistito da AI](LEGGIMI_METODO_DI_SVILUPPO_AI.md).

## Verifica rapida

```bash
cp .env.example .env
docker compose up --build --wait
docker compose run --rm api python manage.py seed_data
docker compose run --rm api python manage.py test
```

Il container `api` applica le migrazioni prima di ogni comando.
La suite contiene 26 test e usa MySQL.
L'API risponde su `http://127.0.0.1:8000`.

Per fermare i servizi:

```bash
docker compose down
```

## Stack e configurazione

| Componente | Versione |
|---|---|
| Python | 3.12.14, immagine `python:3.12-slim` |
| Django | 5.2.17 LTS |
| Django REST Framework | 3.18.1 |
| MySQL | 8.4.11 LTS |
| PyMySQL | 1.2.3 |
| uv | 0.12.10 |
| Docker Engine | 24.0 o successivo |
| Docker Compose | v2 |

`uv.lock` fissa le dipendenze Python.
`.env.example` contiene valori locali di esempio, senza credenziali reali.
MySQL non espone porte verso l'host.

## Modello dati e scelte tecniche

| Scelta | Motivo |
|---|---|
| App `customers` e `pratiche` separate | Anagrafica e gestione delle pratiche restano distinte. |
| Email normalizzata e univoca | Evita duplicati anche con maiuscole diverse. |
| Foreign Key con `PROTECT` | Un cliente con pratiche associate non può essere eliminato per errore. |
| `DecimalField(10, 2)` | Gli importi restano esatti al centesimo. |
| `MinValueValidator` e `CheckConstraint` | L'importo deve essere almeno `0.01`, sia nell'API sia nel database. |
| `select_related("cliente")` | Lista e dettaglio caricano pratica e cliente con una sola query. |
| Serializer distinti | Creazione, lettura e cambio di stato accettano solo i campi previsti. |

Identificativi e data di apertura sono generati automaticamente.
I messaggi relativi ai casi richiesti dalla traccia sono in italiano.

## Stati della pratica

```text
nuova -> in_lavorazione -> chiusa
```

- Alla creazione lo stato è `nuova`.
- Non si possono saltare passaggi o tornare indietro.
- Una pratica `chiusa` non può essere riaperta.
- Confermare lo stato corrente restituisce `200 OK` senza modificare il record.

## Endpoint

Tutte le richieste e le risposte usano JSON.

| Metodo | Percorso | Funzione |
|---|---|---|
| `POST` | `/api/customers/` | Crea un cliente. |
| `POST` | `/api/clienti/` | Alias italiano per la creazione del cliente. |
| `POST` | `/api/pratiche/` | Crea una pratica nello stato `nuova`. |
| `GET` | `/api/pratiche/` | Elenca le pratiche. |
| `GET` | `/api/pratiche/?stato=nuova` | Filtra per stato. Accetta anche `status`. |
| `GET` | `/api/pratiche/<id>/` | Restituisce una pratica. |
| `PATCH` | `/api/pratiche/<id>/` | Modifica soltanto lo stato. |

### Esempi

Creazione cliente:

```bash
curl -X POST http://127.0.0.1:8000/api/customers/ \
  -H 'Content-Type: application/json' \
  -d '{"first_name":"Mario","last_name":"Rossi","email":"mario.rossi@example.com"}'
```

Creazione pratica:

```bash
curl -X POST http://127.0.0.1:8000/api/pratiche/ \
  -H 'Content-Type: application/json' \
  -d '{"cliente":1,"descrizione":"Finanziamento auto","importo":"4500.00"}'
```

Elenco, filtro e dettaglio:

```bash
curl http://127.0.0.1:8000/api/pratiche/
curl "http://127.0.0.1:8000/api/pratiche/?stato=in_lavorazione"
curl http://127.0.0.1:8000/api/pratiche/1/
```

Cambio di stato:

```bash
curl -X PATCH http://127.0.0.1:8000/api/pratiche/1/ \
  -H 'Content-Type: application/json' \
  -d '{"stato":"in_lavorazione"}'
```

Una pratica restituisce `id`, `cliente_id`, dati del cliente, `descrizione`, `importo`, `stato`, `creata_il` e `aggiornata_il`.

## Errori gestiti

| Caso | HTTP | Risposta |
|---|---:|---|
| Campi mancanti o non validi | 400 | Errore associato al campo. |
| Email già utilizzata | 400 | `Esiste già un cliente con questa email.` |
| Cliente inesistente | 400 | `Il cliente specificato non esiste.` |
| Stato sconosciuto | 400 | Elenco degli stati ammessi. |
| Transizione vietata | 400 | Motivo del rifiuto. |
| Pratica inesistente | 404 | `Pratica non trovata.` |

## Seed e test

`seed_data` inserisce tre clienti e cinque pratiche nei tre stati disponibili.
Può essere eseguito più volte senza duplicare i record previsti.

```bash
docker compose run --rm api python manage.py seed_data
```

Per cancellare i dati locali e ricaricare il seed:

```bash
docker compose run --rm api python manage.py seed_data --reset
```

I 26 test coprono clienti, email, creazione delle pratiche, importi non validi, cliente inesistente, transizioni, idempotenza, `PATCH` incompleti, elenco, filtri, dettaglio e 404.
Le regressioni includono email troppo lunghe, identificativi frazionari, precisione monetaria, campi automatici, richieste da browser e richieste concorrenti su MySQL.
L'aggiornamento dello stato blocca la riga in una transazione fino al salvataggio.

## Perimetro

Le funzionalità richieste sono complete.
Frontend, autenticazione, cancellazione, paginazione, deploy e integrazioni esterne non sono inclusi perché esclusi dalla traccia.

Per un uso in produzione valuterei permessi per ruolo, storico delle transizioni, paginazione, filtri aggiuntivi, logging e configurazioni separate per ambiente.

## Tempo

La prima versione completa ha richiesto circa un'ora e mezza di lavoro effettivo, compresi analisi, implementazione assistita, test, revisione e documentazione.
Sto continuando a studiare il repository in preparazione alla presentazione tecnica.

## Strumenti AI

| Strumento | Uso |
|---|---|
| Antigravity IDE con Gemini 3.8 Flash | Implementazione assistita. |
| Codex con GPT-5.6 Sol | Revisione, casi limite e verifica finale. |
| AI Council di NeXgen Engine | Stress test del piano tramite revisori indipendenti. |
| `code-intel` di NeXgen Engine | Analisi AST, simboli e dipendenze. |
| Ponytail e YAGNI | Contenimento del codice non necessario. |
| `verification-before-completion` | Ripetizione dei controlli prima della consegna. |
| `humanizer` | Revisione della documentazione senza modificare il contenuto tecnico. |
| NotebookLM con Gemini | Studio del repository e dei concetti Django dopo l'implementazione. |

l'implementazione tecnica è stata prodotta con assistenza AI.
Le logiche di business e le scelte implementative sono state discusse con i modelli e poi verificate eseguendo codice e test su MySQL.
NeXgen Engine è la cassetta degli attrezzi che ho costruito per rendere ripetibili review e analisi della codebase.
Terminata la prima versione, ho già preparato un notebook di studio in NotebookLM con Gemini per ripercorrere il progetto dal routing HTTP all'ORM e a MySQL.
L'obiettivo è poter spiegare e mantenere ciò che ho consegnato, non presentare il codice assistito come lavoro svolto senza aiuto.
