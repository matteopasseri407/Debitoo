# Il Mio Metodo di Sviluppo con Intelligenza Artificiale

Questo documento descrive esattamente come ragiono, come progetto e come costruisco software assistito da modelli di intelligenza artificiale. 

Non si tratta di "vibecoding", ovvero di delegare ciecamente la scrittura del codice a una chat sperando che funzioni. È un processo ingegnerizzato, disciplinato e scandito da passaggi precisi, in cui mantengo la regia e il controllo su ogni singola scelta architetturale.

---

## Il Workflow in 10 Passi

### 1. Requisiti chiari e piano dettagliato
Nessuna riga di codice viene scritta finché i requisiti non sono stati sviscerati. Si parte dalla specifica (nel caso di Debitoo, la traccia del colloquio), si estraggono i vincoli non negoziabili e si elabora un piano di implementazione dettagliato diviso in blocchi atomici.

### 2. Stress-test del piano con review incrociata di modelli frontier
Prima di toccare l'editor, il piano viene sottoposto a stress-test incrociato tra modelli di frontiera diversi (ad esempio Claude, GPT, Gemini). Se un modello evidenzia una falla logica, una vulnerabilità o un'incongruenza nella gestione dei dati, il piano viene corretto prima che l'errore contamini la codebase.

### 3. Routing intelligente dei modelli (Frontier per il giudizio, Flash per il bulk)
Non tutti i compiti richiedono la stessa potenza di calcolo:
- **Modelli Frontier (grandi, lenti, costosi):** dedicati esclusivamente alle decisioni architetturali critiche, all'analisi dei requisiti, al debug difficile e alla validazione della macchina a stati.
- **Modelli Flash (leggeri, veloci, economici):** dedicati alla stesura meccanica in bulk, boilerplate, conversioni di formato e compiti a basso rischio logico.
Questo approccio ottimizza sia la qualità del risultato sia il consumo dei token e i costi computazionali.

### 4. Architettura modulare, espandibile dal giorno 0 e codice commentato in italiano
Pretendo dal primo momento una struttura modulare (come la netta separazione tra l'anagrafica `customers` e la gestione delle posizioni in `pratiche`). 
Tutto il codice deve essere ampiamente commentato e spiegato in lingua italiana chiara. Questa scelta serve a me in primo luogo per avere la padronanza assoluta di ogni linea, ma rende anche il codice immediatamente leggibile e manutenibile da chiunque subentri nel team.

### 5. Isolamento e riproducibilità immediata con Docker
Nessun "sul mio computer funzionava". L'intero ambiente (interprete Python, pacchetti e database relazionale MySQL 8.4) viene containerizzato tramite Docker Compose fin dal primo commit. Chiunque riceva il repository deve poter avviare l'applicazione e il database con un unico comando senza dover installare dipendenze sul proprio sistema.

### 6. Stesura guidata da vincoli di sobrietà (Regola Ponytail / YAGNI)
Durante la scrittura del codice restano attive regole rigide di anti-overengineering (ispirate alla scala Ponytail):
- Usare prima la libreria standard di Python (`decimal.Decimal` per i calcoli monetari esatti).
- Usare le funzioni native del framework (`TextChoices`, `MinValueValidator`, `CheckConstraint`, `PrimaryKeyRelatedField`, `select_related`).
- Vietato aggiungere librerie esterne non indispensabili. 
Questo approccio riduce i token sprecati in output, elimina il codice superfluo e produce una codebase pulita e solida.

### 7. Stress-test avversario ed edge-cases con un modello differente
Chi scrive il codice non deve essere chi lo collauda. A implementazione completata, la codebase viene passata al setaccio da un modello differente a ragionamento profondo (es. GPT-5.6 Sol con effort `xhigh` su Codex) con il ruolo esplicito di trovare difetti e casi limite. È grazie a questa review avversaria che è stato scovato il bug del payload parziale vuoto (`PATCH {}`) su DRF ed è stato introdotto il `CheckConstraint` nativo sul database MySQL prima della consegna.

### 8. Suite di test automatici anti-regressione
Nessuna feature è considerata completata senza test automatizzati eseguiti nell'ambiente reale. Invece dei 3 minimi richiesti, sono stati implementati 19 test di integrazione eseguiti su MySQL in Docker che coprono il flusso corretto, gli importi negativi, i valori nulli, i salti di stato, le retrocessioni, l'idempotenza e i payload anomali.

### 9. Mappatura della codebase con tool MCP dedicato (`code-intel`)
Ho integrato un server MCP costruito appositamente per analizzare l'AST (Abstract Syntax Tree) del progetto. Questo strumento genera la mappa concettuale dei simboli (`repo_map`), calcola il numero di chiamanti per ogni funzione e ne misura il raggio d'impatto (`find_callers`). Serve sia a me per visualizzare il grafo delle relazioni, sia a futuri agenti AI per orientarsi istantaneamente nel codice senza allucinare percorsi inesistenti.

### 10. Tracciabilità e controllo di versione su Git
Ogni fetta di lavoro viene verificata, isolata e fissata con commit atomici e descrittivi su Git, garantendo una cronologia trasparente, reversibile e pronta per il repository remoto.

---

## Come Lavorerei sulla Vostra Codebase Aziendale dal Giorno 1

Se domani dovessi iniziare a lavorare sui progetti interni di Debitoo Group, il mio comportamento operativo seguirebbe questo protocollo a danno zero:

1. **Isolamento preventivo (Branch dedicato / Fork):**
   Non si tocca mai direttamente il branch principale o di staging. Ogni ticket viene sviluppato su un branch isolato (`feature/ticket-xyz`), garantendo che l'ambiente stabile del team non venga mai compromesso.

2. **Mappatura preventiva prima di toccare il codice:**
   Prima di modificare una riga, uso gli strumenti di analisi del grafo e dell'AST per capire chi chiama quel metodo, quali tabelle del database sono coinvolte e quali dipendenze esistono. Muoversi al buio in una codebase sconosciuta è la prima causa di bug collaterali.

3. **Contenimento del raggio di danno (Blast Radius minimo):**
   L'intervento viene confinato strettamente al singolo componente oggetto del ticket. Niente refactoring selvaggi fuori perimetro, niente modifiche a file contigui "perché scritti male", e massimo rigore nel circoscrivere il raggio d'impatto della patch.

4. **Verifica e test locali prima di coinvolgere il team:**
   La modifica viene scritta, collaudata ed eseguita nei container locali con i relativi test di regressione. Non porto all'attenzione del team codice che non abbia già superato la verifica automatica in locale.

5. **Pull Request chiara e diff leggibile per la review del senior:**
   Consegno il lavoro con una richiesta di merge (Pull Request) corredata da una spiegazione sintetica: cosa cambia, perché, quali test sono stati eseguiti e quale comportamento è stato verificato. In questo modo chi ha più esperienza può fare la review in pochi minuti su un diff pulito, senza dover perdere tempo a decifrare il codice.
