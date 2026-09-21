# Come ho sviluppato la prova con l'assistenza AI

Non ho scritto questa prova senza aiuto.
Ho usato modelli AI per discutere i requisiti, produrre una prima implementazione, cercare errori e preparare la documentazione.
Le decisioni di dominio, come la sequenza degli stati e i vincoli sugli importi, sono state ragionate insieme agli assistenti e verificate nel codice e nei test.

Questo documento descrive il metodo che ho seguito.
Non vuole dimostrare una padronanza che sto ancora costruendo.
La responsabilità di capire, verificare e spiegare il risultato resta mia.

## La mia cassetta degli attrezzi

Nel tempo mi sono costruito NeXgen Engine per riunire strumenti e regole che uso quando lavoro con l'AI.
Non è un sostituto delle competenze tecniche.
Mi serve per rendere ripetibili operazioni che altrimenti farei a mano ogni volta, come chiedere una seconda revisione o ricostruire le dipendenze di una codebase.

In questa prova ho usato soprattutto:

- AI Council, che consulta modelli tramite le rispettive CLI e li usa come revisori indipendenti.
- `code-intel`, un tool MCP che analizza l'AST e mostra simboli, chiamanti e dipendenze.
- Antigravity IDE con Gemini 3.8 Flash per l'implementazione assistita.
- Codex con GPT-5.6 Sol per la revisione dei casi più delicati.

## Il flusso di lavoro

### 1. Estraggo i requisiti

Parto dalla traccia e separo ciò che è obbligatorio da ciò che è facoltativo.
Per questa prova i vincoli principali erano MySQL, le sei operazioni API, la sequenza degli stati, i tre test minimi e la documentazione di consegna.

### 2. Faccio contestare il piano

Prima di implementare, uso AI Council in modalità `challenge`.
I revisori cercano passaggi mancanti, regole ambigue e casi limite.
Correggo il piano prima che quei problemi finiscano nel codice.

### 3. Scelgo lo strumento in base al compito

Uso un modello rapido per il lavoro meccanico e uno con maggiore capacità di ragionamento per decisioni, debug e revisione.
In questa prova Gemini 3.8 Flash ha seguito gran parte dell'implementazione assistita.
Codex con GPT-5.6 Sol è stato usato per la revisione finale e per i casi limite.

### 4. Procedo per fette piccole

La prima fetta completa è stata la creazione del cliente.
Solo dopo averne verificato routing, serializer, model, migrazione e test sono passato alle pratiche.
Questo rende più facile capire dove nasce un errore.

### 5. Eseguo tutto in Docker

Docker Compose avvia Django e MySQL con le stesse dipendenze dichiarate nel repository.
L'applicazione non dipende dalla configurazione Python o MySQL della macchina di chi la esegue.

### 6. Preferisco ciò che Django offre già

Ho seguito Ponytail e YAGNI come regole di sobrietà.
Prima di aggiungere codice o dipendenze ho cercato una funzione già disponibile nel framework.
`TextChoices`, `DecimalField`, `MinValueValidator`, `CheckConstraint`, `PrimaryKeyRelatedField` e `select_related` coprivano già le necessità del progetto.

I commenti spiegano le regole di business e i passaggi che sto studiando.
Non servono a trasformare ogni riga di Python in una parafrasi.

### 7. Separo implementazione e revisione

Dopo l'implementazione ho chiesto a un modello diverso di cercare difetti e input anomali.
Questa revisione ha individuato il caso `PATCH {}`, che doveva restituire `400` invece di accettare una richiesta priva di stato.
Ha portato anche all'aggiunta del `CheckConstraint` sull'importo, così il vincolo esiste nel database oltre che nel serializer.

### 8. Verifico con test automatici

La traccia richiedeva tre test.
La suite ne contiene 19 e gira sul database MySQL avviato da Docker.
Copre il percorso normale, la validazione degli importi, le transizioni vietate, l'idempotenza, i filtri e gli errori principali.

### 9. Uso la mappa del codice

`code-intel` fa parte di NeXgen Engine e analizza l'AST del repository.
`repo_map` restituisce simboli e struttura.
`find_callers` mostra dove viene usata una funzione prima di modificarla.

La [mappa del progetto](MAPPA_PROGETTO.md) deriva da questa analisi.
Il relativo export è disponibile in [docs/code_intel_graph.json](docs/code_intel_graph.json).

### 10. Lascio una cronologia leggibile

Ogni fase verificata viene salvata in un commit circoscritto e descrittivo.
Questo permette di leggere l'evoluzione del progetto e di isolare più facilmente una regressione.

## Come userei lo stesso metodo in un team

Su una codebase aziendale partirei dalle regole del team, compresi gli strumenti AI autorizzati e i dati che non possono essere condivisi con servizi esterni.

Per un ticket:

1. Creerei un branch dedicato.
2. Leggerei il flusso interessato e le sue dipendenze prima di modificare il codice.
3. Limiterei il diff al comportamento richiesto.
4. Eseguirei i test esistenti e aggiungerei il caso di regressione necessario.
5. Aprirei una pull request con una spiegazione breve del cambiamento e delle verifiche eseguite.

Se una decisione supera la mia esperienza, la porterei in review invece di nasconderla dietro una risposta prodotta dall'AI.
