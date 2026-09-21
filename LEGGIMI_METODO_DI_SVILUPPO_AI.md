# Metodo di sviluppo assistito da AI

L'implementazione tecnica di questa prova è stata prodotta con assistenza AI.
Ho usato i modelli per analizzare la traccia, discutere le logiche, scrivere codice e test, cercare errori e preparare la documentazione.
Quanto scritto qua sotto, sono le mie logiche, non corrette di proposito per massima trasparenza nei vostri confronti sulle mie capacità.

Terminata questa versione, ho già preparato un notebook di studio in NotebookLM con Gemini.
Lo sto usando per ripercorrere il flusso tra URL, view, serializer, model, ORM e MySQL e consolidare le basi per potermi assumere la responsabilità di quanto scritto.

## Cassetta degli attrezzi

NeXgen Engine raccoglie strumenti e regole che mi sono costruito per rendere ripetibili review e analisi della codebase.

| Strumento | Uso in questa prova |
|---|---|
| Antigravity IDE con Gemini 3.8 Flash per la stesura |
| Codex con GPT-5.6 Sol | Revisione dei casi limite e controllo finale. |
| AI Council | Stress test del piano con revisori indipendenti eseguiti tramite le rispettive CLI. |
| `code-intel` | Analisi AST, mappa dei simboli e ricerca dei chiamanti. |
| Ponytail e YAGNI | Preferenza per funzioni native e codice necessario. |
| Docker Compose | Ambiente riproducibile con Django e MySQL. |
| NotebookLM con Gemini per studio successivo del progetto e dei concetti usati. |

## Come sviluppo normalmente 

| Passo | Attività |
|---:|---|
| 1 | Estrarre requisiti obbligatori e parti facoltative. |
| 2 | Elaborare e sottoporre un piano di implementazione con AI Council in modalità `challenge`. |
| 3 | Usare un modello rapido per il lavoro meccanico e uno più adatto alla revisione. |
| 4 | Procedere alla scrittura del codice con AI con modularità e espandibilità futura in mente sin dal giorno 1. |
| 5 | Eseguire applicazione e database in Docker fin dal primo commit. |
| 6 | Preferire gli strumenti Django / python già disponibili prima di aggiungere codice o dipendenze. |
| 7 | Far rivedere l'implementazione a un modello diverso da quello usato per scriverla. |
| 8 | Eseguire i test su MySQL e aggiungere i casi di regressione trovati durante la review. |
| 9 | Usare `repo_map` e `find_callers` di `code-intel` per controllare struttura e dipendenze. serve sia agli agenti AI per evitare allucinazioni ma credo sia utile anche per dev umani, specie magari in codebase molto più complesse. |
| 10 | Salvare fasi circoscritte in commit descrittivi e firmati. |

La review ha individuato il caso `PATCH {}`, che ora restituisce `400 Bad Request` un bug che era sfuggito a una prima stesura del modello flash.
Ha portato anche al `CheckConstraint` sull'importo, così il vincolo esiste nel serializer e nel database.
La suite finale contiene 19 test.

La [mappa della codebase](MAPPA_PROGETTO.md) e il relativo [export AST](docs/code_intel_graph.json) documentano l'analisi svolta con `code-intel`.

## Uso in un team

Su una codebase aziendale partirei dalle regole del team e dagli strumenti AI autorizzati.
In generale, NON scriverei mai sul Main, ma mi farei il mio fork e lavorerei su quello, prima di ripassarlo eventualmente e mergiarlo in produzione. 
