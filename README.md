# Integrazione Home Assistant

Dispensa include un'integrazione personalizzata, locale e in sola lettura. Non richiede MQTT né il token Home Assistant usato per le notifiche in uscita. L'integrazione interroga `/api/home-assistant` ogni 5 minuti; i cambiamenti di menu possono comparire entro il successivo aggiornamento. Le date sono quelle del server Dispensa: configurare lo stesso fuso orario su Dispensa e Home Assistant.

## Installazione con HACS

HACS può scaricare soltanto repository GitHub pubblici. Il componente richiede Home Assistant 2024.5 o successivo; la versione effettivamente installata deve ancora essere verificata sul proprio impianto.

1. Aggiornare il servizio Dispensa con questa versione tramite la procedura abituale. Non creare una seconda istanza dello stack.
2. In HACS aprire il menu **⋮ → Repository personalizzati**. Inserire `https://github.com/giuseppe99barchetta/dispensa-home-assistant`, scegliere la categoria **Integrazione** e aggiungerlo.
3. Cercare **Dispensa** in HACS e scaricare l'integrazione. Se la versione proposta non contiene ancora queste modifiche, selezionare il ramo predefinito dopo la pubblicazione del codice su GitHub. HACS installa solo il componente Home Assistant: il server Dispensa si aggiorna separatamente.
4. Riavviare Home Assistant. Andare in **Impostazioni → Dispositivi e servizi → Aggiungi integrazione**, cercare **Dispensa** e inserire l'indirizzo HTTP o HTTPS raggiungibile da Home Assistant, ad esempio `http://192.168.1.10:9284`. Non usare `localhost` se Dispensa è in un altro container o dispositivo. L'indirizzo può includere un percorso di base del proxy.
5. Aprire il dispositivo Dispensa creato dall'integrazione e aggiungere le entità desiderate alla dashboard. I nomi effettivi degli ID sono visibili nella pagina di ciascuna entità.

L'integrazione si aggiunge come repository personalizzato: non è automaticamente presente nel catalogo predefinito di HACS. Il repository e le modifiche devono essere disponibili su GitHub per poter essere scaricati. In alternativa si può copiare manualmente `custom_components/dispensa` in `<configurazione Home Assistant>/custom_components/dispensa`, mantenendo tutti i file e le sottocartelle, e poi riavviare Home Assistant.

Come per la dashboard, l'API non richiede password: renderla raggiungibile solo dalla rete fidata o proteggerla sul proxy. Se si usa HTTPS con una CA privata, Home Assistant deve considerare attendibile il certificato. Le immagini mostrate con `entity_picture` sono caricate dal browser o dalla Companion App: l'indirizzo configurato deve essere raggiungibile anche dal dispositivo che visualizza la dashboard. Con HTTPS evitare immagini servite in HTTP, che il browser potrebbe bloccare.

## Entità

- **Pranzo di oggi** e **Cena di oggi**: titolo e immagine, con data, stato, stato del menu, inclusione, porzioni, ingredienti, istruzioni, tempo stimato e nutrizione stimata per porzione negli attributi. Un pasto singolo scelto sostituisce quello del menu. Il menu in bozza è indicato come tale; uno slot escluso risulta «Non previsto». Gli stati `done`, `skipped`, `prepared`, `applying` e `needs-review` conservano il significato registrato da Dispensa.
- **Prodotti in dispensa**, **Lotti in scadenza**, **Lotti scaduti**, **Lotti con scadenza sconosciuta** e **Prodotti sotto il minimo**: conteggi aggiornati da Grocy. La finestra di scadenza comprende oggi e i tre giorni successivi; le liste dei lotti e dei prodotti sotto il minimo sono negli attributi. La scadenza sconosciuta non è trattata come scaduta. Se Grocy non risponde, i sensori interessati diventano non disponibili, senza mostrare uno zero fittizio.
- **Preparazioni disponibili** e **Operazioni da verificare**: preparazioni con porzioni residue e righe di operazioni sospese o in corso. Il secondo conteggio è quello delle righe rilevate dalle categorie dello stato di Dispensa, non necessariamente di operazioni distinte.
- **Articoli da acquistare**: numero di righe non spuntate e lista negli attributi, ricalcolata per il menu corrente con le scorte aggiornate. Senza menu corrente o se Grocy non risponde il sensore è non disponibile; la consultazione non modifica la lista.

L'immagine usa quella scelta nella ricetta, quella già trovata nella cache di Dispensa, oppure una foto indicativa del catalogo incluso nell'app, scelta in base al nome del piatto. La ricerca remota delle foto non viene avviata dal polling. Gli attributi riportano autore, licenza e fonte quando disponibili; le immagini indicative non certificano l'aspetto del piatto.

Ad esempio, sostituendo gli ID con quelli effettivamente creati, una scheda della dashboard può usare:

```yaml
type: vertical-stack
cards:
  - type: picture-entity
    entity: sensor.dispensa_pranzo_di_oggi
    show_state: true
  - type: picture-entity
    entity: sensor.dispensa_cena_di_oggi
    show_state: true
  - type: entities
    entities:
      - sensor.dispensa_lotti_in_scadenza
      - sensor.dispensa_prodotti_sotto_il_minimo
      - sensor.dispensa_articoli_da_acquistare
      - sensor.dispensa_operazioni_da_verificare
```

Gli attributi sono utilizzabili anche nei template e nelle automazioni. L'integrazione non approva menu, non spunta la lista della spesa e non modifica Grocy. La revisione delle scorte e le conferme rimangono in Dispensa.
