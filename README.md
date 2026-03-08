# WebCore
Creation of an API service with Django to fetch data from a WebApp, made with php &amp; js, and from Ignition. The service have to take data from both or only one and return the response to the one requesting.

### Cose da fare
1. Creare DB (MySQL - MariDB)
2. Creare progetto Django
3. Test progetto Django tramite script php per simulare il passaggio di dati JSON
4. Creare container del progetto con Docker cosi da poterlo spostare su Unix/Linux
5. Portare il progetto su Nginx e Gunicorn
6. Test totale del progett
7. Aggiungere misure di sicurezza
   
### Logica Progetto

WebCore - API Distribution

Richiesta:
1° step: creare un manuale utente riguardo gli allarmi delle macchine
2° step: far diventare il manuale interattivo
3° step: rendere accessibile il manuale sia dalla piattaforma Ignition e dal sito web

### Mappa:

PLC and User -> Ignition <--> WebCore <--> Website <--> User

### Componenti
1. Ignition avrà una pagina dove l'utente può visionare le pagine del manuale in base a:

    -- piano produzione; es. pp23240 <br>
    -- categoria della macchina; es. TR, DR, etc <br>
    -- tipo della macchina; es. 200, 400, 600, 800 <br>
    -- componente della macchina; es. sensore, spatola, etc.. <br>
    -- codice dell'allarme; es. allarme_temperatura

    l'utente può scegliere se cercare solo il componente e visionare i tipi di errori e le manutenzioni collegate oppure cercare in base a categoria + codice e/o allarme della macchina per visionare la pagina del manuale con più o meno dettagli. Mentre il tecnico avrà accesso anche alla ricerca per piano produzione

2. WebCore è il centro della logica di instradamento delle info, l'unico lavoro che deve fare è ricevere le richieste (es. categoria + codice + allarme macchina) e restituire il testo con la soluzione all'allarme oppure delle info riguardo il pezzo, delle immagini e/o video (almeno il percorso di dove andare a pescare le foto e video).
Il WebCore deve anche dare la possibilità di accedere a delle pagine in locale o distanza in caso di fallback di Ignition ma questo si vedrà nel futuro.

3. WebApp + creata con PHP e appoggia su Drupal; farà richieste HTTP al WebCore così come Ignition

### Database
#### Tabelle
1. Macchinari: id, piano_produzione, categoria, tipo
2. Allarmi: id, titolo
3. Componenti: id, descrizione_pezzo
4. Informazioni: id, id_macchinario, id_allarme, id_componente, soluzione_problema, path_img, path_video