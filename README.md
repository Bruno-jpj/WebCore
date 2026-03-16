# WebCore
## Introduzione
Questo progetto è iniziato dalla richiesta di creare un manuale utente iterattivo riguardo gli allarmi macchina; con la possbilità di integrare chiamate API per il passaggio di dati tra client e server.

In seguito è stata aggiunta la possibilità di eseguire operazioni di modifica, aggiunta ed eliminazione dei titoli, testi, foto e video; questo ovviamente solo per utenti autorizzati.

## Cosa manca
> WebApp
> 1. Divisione della pagina allarmi tra utente e gestore [ Basta creare una pagina copia e separare le logiche nell'HTML ].
> 2. Miglioramento della pagina allarmi [ Separare le logiche di inserimento, cancellazione e aggiornamento dalla pagina principale, magari con una finestra pop-up ].
> 3. Utilizzo di framework JavaScript per sistemare le mancaze come scritto al punto [ 2 ].

> API
> 1. Sistema di autenticazione e permessi di chi fa le richieste 
> 2. Miglioramento API per il passaggio di dati [ Riscrivere logica per passare oltre che il testo della soluzione, per lingua, anche il video e immagine giusti]

## Logica

### Divisione Cartelle

- .venv: è un ambiente virtuale che contiene una versione di python specifica che si desidera, cosi da poter installare i moduli che si vuole senza avere confilitti di compatibilità; inoltre in caso di errore del venv è possibile eliminarlo e creare tutto da capo senza toccare il sistema operativo


<pre>
# Creare l'ambiente virtuale
python -m venv .venv
python -m module_name dir_name

# Attivare l'ambiente virtuale
Windows: .venv/Script/activate
Linux: source .venv/bin/activate

# Comando per installare i moduli
pip install module_name
</pre>

- project: questa cartella viene creata dopo aver installato il framework di django ed eseguito il comando per creare il progetto, crea anche una sottocartella con lo stesso nome con i file del sistema, poi dopo va utilizzato il comando per creare l'app o le app

<pre>
    # Creare il progetto
    django-admin startproject project_name
    django-admin startproject project

    # Creare l'app
    python manage.py startapp app_name
    python manage.py startapp api
    python manage.py startapp core

    root_dir
    |-> .venv 
    |-> project
    &emsp;&emsp;    |-> api 
    &emsp;&emsp;    |-> core
</pre>

- api: questa app serve per gestire la logica degli endpoint e della comunicazione esterna, tratta solo il passaggio di dati e non di pagine web.
- core: questa app serve per gestire la logica interna, quindi della comunicazine tra le pagine web e tutti gli eventi possibili.
- database: questa cartella contiene la logica del Database e tutti gli script SQL per la sua gestione e/o creazione
- media: contiene gli elementi (img e video) da fornire e/o ricevere durante le richieste della pagina allarmi e degli endpoint
- static: continene gli script utili per il frontend come CSS e JS, utilizzati durante lo sviluppo
- staticfiles: contiente gli script utili per il frontend, utilizzati per dopo lo sviluppo si usa il comando
            <pre>
            python manage.py collectstatic
            </pre>
- templates: contiene tutti i file HTML
  
### API App
### Core App