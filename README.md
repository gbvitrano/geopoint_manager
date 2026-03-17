# GeoPoint Manager v5.2 — Plugin QGIS

Plugin QGIS per creare **layer vettoriali di punti** a partire da sorgenti dati contenenti
campi di coordinate geografiche (latitudine/longitudine).

**Compatibilità:** QGIS 3.16+ / 4.x &nbsp;|&nbsp; **Licenza:** GPL-2.0+
**Autore:** [@gbvitrano](https://github.com/gbvitrano)

---

## Sorgenti dati supportate

| Sorgente | Note |
| --- | --- |
| **Google Sheets** | Download diretto via urllib, salvataggio in GeoPackage |
| **URL OGR/GDAL** | Fonti online generiche |
| **WFS** | Web Feature Services |
| **GeoJSON, Shapefile (ZIP), KML/KMZ, GPX, CSV** | File locali o remoti |
| **Layer QGIS esistenti** | Layer già caricati nel progetto corrente |

---

## Funzionalità principali

1. **Rilevamento automatico coordinate** — individua i campi lat/lon tramite keyword matching
   (es. `lat`, `latitude`, `y`, `northing`, `lon`, `lng`, `x`, `easting`…)
2. **Virtual Layer dinamico** — crea layer virtuali QGIS con query SQL:

   ```sql
   SELECT *, make_point(CAST(lon AS REAL), CAST(lat AS REAL)) as geometry
   FROM source WHERE lon IS NOT NULL AND lat IS NOT NULL
   ```

3. **Google Sheets integration** — salva i CSV scaricati in un GeoPackage locale,
   con registro persistente (`_geopoint_sources`) e refresh manuale on-demand.
4. **Gestione CRS flessibile** — auto-rilevamento o forzatura del sistema di riferimento
   (EPSG:4326, 3857, UTM e personalizzato).
5. **Export multiplo** — GeoPackage, Shapefile, GeoJSON, KML, CSV.
6. **Processing integration** — accessibile anche dal QGIS Processing Framework.

---

## Interfaccia utente

| Tab | Descrizione |
| --- | --- |
| **Tab 1 – Dati OGR/GDAL** | Caricamento da URL (OGR/GDAL, Google Sheets, WFS…). Include Opzioni Avanzate (autenticazione, parametri, layer, CRS override) e salvataggio GeoPackage. |
| **Tab 2 – Dati da layer QGIS** | Caricamento da layer già presenti nel progetto. Include la sezione *Configurazione campi e CRS* per selezione campi X/Y, CRS, nome layer virtuale e selezione colonne da includere. |
| **Tab 3 – Log** | Storico delle operazioni con timestamp. |
| **Tab 4 – Info / About** | Documentazione del plugin. |

La barra inferiore contiene: **Aggiungi layer vettoriale di punti**, **Esporta Layer…**, **Salva GPKG**, **🌐 IT/EN** e **Chiudi**.

---

## Workflow tipici

### Flusso base

1. Avvia il plugin (icona toolbar o menu Vettore).
2. Seleziona la sorgente dati (tab *Dati OGR/GDAL* o *Dati da layer QGIS*).
3. Inserisci l'URL o seleziona il layer.
4. I campi coordinate vengono rilevati automaticamente oppure si apre il dialogo
   *Seleziona Campi Coordinate e Colonne* per scegliere lat/lon e le colonne da includere nel layer virtuale.
5. Clicca **"Aggiungi layer virtuale di punti e la relativa tabella"**.
6. Esporta se necessario.

### Google Sheets

1. Condividi il foglio Google pubblicamente e copia l'URL di esportazione CSV.
2. Specifica il percorso del GeoPackage di destinazione.
3. Carica i dati; il plugin li salva localmente.
4. Per aggiornare: clicca **"↻ Aggiorna da Google Sheets"**.

---

## Novità v5.2

- **Interfaccia bilingue ITA / EN** — pulsante **🌐 IT/EN** nella barra inferiore per cambiare
  lingua al volo; preferenza salvata in `QSettings`.
- Nuovo modulo `i18n.py` con dizionario completo (~120 stringhe) per italiano e inglese.
- Tab *Info / About* con contenuto tradotto in entrambe le lingue.
- Fix `NameError: info_browser` in `setup_ui`.

## Novità v5.1

- Fix caricamento Google Sheets su QGIS 4 (*urllib* gestisce i redirect HTTP).
- Storage persistente basato su GeoPackage per i dati scaricati.
- Refresh manuale on-demand al posto dell'auto-fetch.
- Compatibilità Qt5/PyQt5 (QGIS 3) e Qt6/PyQt6 (QGIS 4) — fix enum `QSizePolicy`, `QFrame`, `Qt`.
- Nuova struttura a 4 tab: *Dati OGR/GDAL*, *Dati da layer QGIS*, *Log*, *Info / About*.
- Dialogo *Seleziona Campi Coordinate e Colonne*: permette di scegliere lat/lon **e** quali colonne
  includere nel layer virtuale, tutto in un unico passaggio.
- Sezione *Configurazione campi e CRS* integrata nel tab *Dati da layer QGIS*.
- Pulsanti *Esporta Layer* e *Salva GPKG* spostati nella barra inferiore, sempre visibili.
- Layout pulito: rimossi i frame ridondanti, lasciato solo il bordo del tab widget.
- Messaggi di errore e logging migliorati.

---

## Sviluppo tecnico

Script Python per QGIS sviluppato attraverso una collaborazione **human-Claude AI (Anthropic)** e **chatbot Z.ai**,
che hanno supportato la progettazione dell'architettura modulare, l'ottimizzazione del codice e l'implementazione
di funzionalità avanzate.

### v5.2 — Dettagli tecnici

- Modulo `i18n.py`: dizionari `STRINGS["it"]` e `STRINGS["en"]`, funzione `tr(key, *args)`,
  `set_language()` / `get_language()` con persistenza in `QSettings`.
- `retranslate_ui()`: lista `self._tr` di lambda che aggiornano tutti i widget al cambio lingua.
- Pulsante **🌐 IT/EN** integrato nella barra pulsanti principale, sempre visibile.

### v5.1 — Dettagli tecnici

- Download Google Sheets via *urllib* con gestione redirect HTTP (QGIS 4 compatibility).
- Dati salvati in **GeoPackage** scelto dall'utente, persistente tra le sessioni;
  registro sorgenti nella tabella `_geopoint_sources`.
- Aggiornamento **manuale on-demand**: il pulsante *↻ Aggiorna da Google Sheets* riscarica il foglio
  e sovrascrive il GeoPackage.
- Supporta entrambi i formati URL Google Sheets (`/pub?output=csv` e `/export?format=csv&gid=…`).
- Selezione colonne tramite `CheckableComboBox` nel dialogo coordinate — le colonne X/Y sono sempre incluse.
- Fix Qt6: enum `QSizePolicy.Policy`, `QFrame.Shape`, `Qt.ItemFlag`, `Qt.CheckState`.

---

## Installazione

### Metodo 1 — Da ZIP (consigliato)

1. In QGIS: **Plugin → Gestisci e installa plugin → Installa da ZIP**
2. Seleziona il file `geopoint_manager_v5.1.zip`
3. Clicca *Installa plugin*

### Metodo 2 — Manuale

1. Copia la cartella `geopoint_manager/` in:
   - **Windows**: `%APPDATA%\QGIS\QGIS4\profiles\default\python\plugins\`
   - **Linux/macOS**: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
2. Riavvia QGIS
3. Abilita il plugin da **Plugin → Gestisci e installa plugin**

---

## Utilizzo

- **Toolbar**: clicca l'icona del pin nella toolbar principale
- **Menu**: **Vettore → GeoPoint Manager → GeoPoint Manager**
- **Processing**: cerca "GeoPoint Manager" nel pannello Strumenti di elaborazione

---

## Struttura del plugin

```text
geopoint_manager/
├── __init__.py                  # Entry point QGIS (classFactory)
├── plugin.py                    # Classe principale: toolbar, menu, provider
├── geopoint_manager_dialog.py   # Logica principale, UI, algoritmo Processing
├── i18n.py                      # Modulo internazionalizzazione ITA/EN
├── metadata.txt                 # Metadati plugin (nome, versione, dipendenze)
├── icons/
│   └── icon.svg                 # Icona plugin
└── README.md                    # Questo file
```

---

## Licenza

GPL-2.0+

by [@gbvitrano](https://www.linkedin.com/in/gbvitrano/) — [@opendatasicilia](https://opendatasicilia.it/)


<img width="802" height="782" alt="2026-03-17_14h32_59" src="https://github.com/user-attachments/assets/775b7acd-fea9-4b32-b0f4-52205064f73b" /> <img width="802" height="782" alt="2026-03-17_14h33_15" src="https://github.com/user-attachments/assets/d3eedae1-395f-4cc3-8b5a-dbb669aebe14" /> <img width="802" height="782" alt="2026-03-17_14h33_50" src="https://github.com/user-attachments/assets/3eb6aedb-fa60-4829-b3d9-0869102b210c" /> <img width="802" height="782" alt="2026-03-17_14h33_37" src="https://github.com/user-attachments/assets/4c3d692f-a968-4565-b118-1b833013980e" />



