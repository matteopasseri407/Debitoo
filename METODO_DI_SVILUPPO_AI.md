# Metodo di Sviluppo Assistito da AI (Oltre il Vibecoding)

Questo documento illustra la metodologia di ingegneria del software adottata per la realizzazione del progetto. 

Nel panorama attuale, l'uso dell'Intelligenza Artificiale nello sviluppo software si divide in due approcci antitetici:
1. **Il "Vibecoding":** delegare ciecamente la scrittura di blocchi di codice a un modello LLM, accettando passivamente le risposte senza comprenderne i limiti, senza verificare gli edge-case e accumulando debito tecnico o architetture sovradimensionate.
2. **Lo Sviluppo AI-First Ingegnerizzato:** utilizzare i modelli AI come amplificatori di produttività all'interno di un processo rigoroso e governato, dove lo sviluppatore mantiene il controllo totale su requisiti, architettura, vincoli di sicurezza e verifica empirica.

Per questa prova è stato applicato rigorosamente il secondo approccio.

---

## I Pilastri del Metodo Operativo

### 1. Decomposizione a Fette Verticali (Slice Architecture)
Invece di chiedere all'AI di generare l'intero progetto in una sola passata, il lavoro è stato suddiviso in fette verticali atomiche e autoconsistenti:
- **Fetta 1:** Anagrafica clienti (`Customer`), persistenza su MySQL, validazione unicità case-insensitive e test dedicati. Solo dopo la verifica completa si è proceduto oltre.
- **Fetta 2:** Modello delle pratiche debitorie (`Pratica`), relazione con il cliente (`ForeignKey` protetta) e macchina a stati.
- **Fetta 3:** Endpoints REST, filtri e hardening degli errori in lingua italiana.
- **Fetta 4:** Dati di seed e suite di test automatizzati estesa.

Questo garantisce che ogni livello sia compreso, testato e solido prima di introdurre nuova complessità.

---

### 2. Principio di Sobrietà (Regola Ponytail / Anti-Overengineering)
Una delle trappole tipiche del codice generato da AI è la tendenza a inserire pattern ridondanti o librerie esterne non necessarie. Per evitare questo fenomeno è stata applicata una scala di rigore a gradini decrescenti:
- **Gradino 1:** *Questa cosa deve davvero esistere?* Se non è richiesta dalla specifica (es. cancellazione clienti o aggiornamento anagrafica), non viene scritta.
- **Gradino 2:** *È già presente nella codebase?* Il serializer delle pratiche riutilizza direttamente il serializer del cliente senza duplicare logiche.
- **Gradino 3:** *La libreria standard di Python lo fa?* Per gli importi finanziari è stato utilizzato il modulo nativo `decimal.Decimal` per evitare imprecisioni dei numeri floating point (IEEE 754).
- **Gradino 4:** *Esiste una funzionalità nativa del framework?* Utilizzati `models.TextChoices` per gli stati, `models.BigAutoField` per le chiavi primarie, `auto_now_add` per i timestamp, `MinValueValidator` e `CheckConstraint` per l'integrità del database.
- **Gradino 5:** *Dipendenze esterne:* nessuna libreria esterna aggiunta oltre allo stack richiesto (Django, DRF, PyMySQL).

Il risultato è un'applicazione snella, lineare e priva di sovrastrutture enterprise fittizie.

---

### 3. Mappatura della Codebase via MCP (`code-intel`)
Per evitare di ragionare a tentativi su file sparsi, è stato integrato uno strumento MCP (Model Context Protocol) dedicato all'analisi statica e all'albero sintattico (AST):
- **Estrazione del grafo dei simboli:** prima di ogni modifica sostanziale, lo strumento genera la mappa concettuale (`repo_map`), riducendo il rumore e concentrando l'attenzione sulle firme dei metodi e sui modelli.
- **Analisi del raggio d'impatto (Blast Radius):** tramite `find_callers` è possibile verificare quali componenti dipendono da una determinata classe o funzione prima di alterarla, azzerando le regressioni silenziose.

Questo flusso consente allo sviluppatore di padroneggiare le relazioni tra i componenti anche senza dover tenere a memoria migliaia di righe di codice.

---

### 4. Verifica Empirica e Isolamento in Ambiente Reale (Docker + MySQL)
Nessuna riga di codice è considerata valida sulla fiducia:
- I test non sono stati eseguiti su SQLite in memoria, ma all'interno di container Docker su un database **MySQL 8.4 reale**, verificando il comportamento effettivo dei tipi dati SQL (`DECIMAL`, indici `UNIQUE`, vincoli di foreign key `ON DELETE RESTRICT/PROTECT` e `CheckConstraint`).
- La suite di **19 test automatici** copre non solo il flusso principale (happy path), ma soprattutto le condizioni limite: importi negativi, importi zero, stringhe alfabetiche, salti di stato, arretramenti, tentativi di riapertura di pratiche concluse e payload vuoti.

---

### 5. Revisione Critica Incrociata Multi-Modello (Council Review)
Per stressare l'implementazione e individuare eventuali punti ciechi, al termine dello sviluppo è stata eseguita una code review autonoma con un modello di frontiera specializzato in reasoning profondo (**GPT-5.6 Sol** con effort `xhigh` via Codex):
- **La scoperta del bug limite:** il revisore ha scovato un comportamento non banale: inviando un `PATCH` con payload vuoto `{}` a `/api/pratiche/<id>/`, la natura parziale di DRF disattivava l'obbligatorietà del campo `stato`, provocando un crash `IntegrityError` (HTTP 500) a livello MySQL.
- **Il fix tempestivo:** il problema è stato immediatamente neutralizzato aggiungendo la validazione esplicita della presenza di `stato` nel serializer e implementando due test automatici di regressione specifici.
- **L'irrobustimento del database:** su suggerimento della review è stato aggiunto un `CheckConstraint` esplicito a livello di tabella MySQL (`pratica_importo_positivo`), garantendo che l'importo debitorio positivo sia un vincolo insuperabile anche bypassando l'ORM di Django.

---

## Sintesi per il Colloquio

Questo metodo dimostra che l'uso dell'Intelligenza Artificiale, se inserito in una disciplina ingegneristica fatta di test, verifica dell'ambiente reale, rispetto delle convenzioni native e revisione critica, non sostituisce la responsabilità dello sviluppatore, ma ne eleva la capacità di consegnare codice robusto, manutenibile e privo di difetti nascosti.
