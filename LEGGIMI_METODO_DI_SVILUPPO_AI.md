# Metodo di sviluppo assistito da AI

Gran parte dell'implementazione tecnica di questa prova è stata prodotta con assistenza AI.
Ho usato i modelli per analizzare la traccia, discutere le logiche, scrivere codice e test, cercare errori e preparare la documentazione.
La responsabilità di verificare, capire e spiegare il risultato resta mia.

Terminata la prima versione, ho già preparato un notebook di studio in NotebookLM con Gemini.
Lo sto usando per ripercorrere il flusso tra URL, view, serializer, model, ORM e MySQL.

## Cassetta degli attrezzi

NeXgen Engine raccoglie strumenti e regole che mi sono costruito per rendere ripetibili review e analisi della codebase.

| Strumento | Uso in questa prova |
|---|---|
| Antigravity IDE con Gemini 3.8 Flash | Implementazione assistita. |
| Codex con GPT-5.6 Sol | Revisione dei casi limite e controllo finale. |
| AI Council | Stress test del piano con revisori indipendenti eseguiti tramite le rispettive CLI. |
| `code-intel` | Analisi AST, mappa dei simboli e ricerca dei chiamanti. |
| Ponytail e YAGNI | Preferenza per funzioni native e codice necessario. |
| Docker Compose | Ambiente riproducibile con Django e MySQL. |
| NotebookLM con Gemini | Studio successivo del progetto e dei concetti usati. |

## Flusso seguito

| Passo | Attività |
|---:|---|
| 1 | Estrarre dalla traccia requisiti obbligatori e parti facoltative. |
| 2 | Sottoporre il piano ad AI Council in modalità `challenge`. |
| 3 | Usare un modello rapido per il lavoro meccanico e uno più adatto alla revisione. |
| 4 | Procedere per fette complete, iniziando dalla creazione del cliente. |
| 5 | Eseguire applicazione e database in Docker fin dal primo commit. |
| 6 | Preferire gli strumenti Django già disponibili prima di aggiungere codice o dipendenze. |
| 7 | Far rivedere l'implementazione a un modello diverso da quello usato per scriverla. |
| 8 | Eseguire i test su MySQL e aggiungere i casi di regressione trovati durante la review. |
| 9 | Usare `repo_map` e `find_callers` di `code-intel` per controllare struttura e dipendenze. |
| 10 | Salvare fasi circoscritte in commit descrittivi e firmati. |

La review ha individuato il caso `PATCH {}`, che ora restituisce `400 Bad Request`.
Ha portato anche al `CheckConstraint` sull'importo, così il vincolo esiste nel serializer e nel database.
La suite finale contiene 19 test.

La [mappa della codebase](MAPPA_PROGETTO.md) e il relativo [export AST](docs/code_intel_graph.json) documentano l'analisi svolta con `code-intel`.

## Uso in un team

Su una codebase aziendale partirei dalle regole del team e dagli strumenti AI autorizzati.
Per ogni ticket userei un branch dedicato, leggerei il flusso coinvolto, limiterei il diff, eseguirei i test e aprirei una pull request con le verifiche svolte.
Porterei in review le decisioni oltre la mia esperienza invece di nasconderle dietro una risposta generata.
