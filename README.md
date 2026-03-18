# GeoPoint Manager v5.2 — QGIS Plugin

🇮🇹 [Italiano](#italiano) &nbsp;|&nbsp; 🇬🇧 [English](#english)

![GeoPoint Manager v5.2](https://raw.githubusercontent.com/gbvitrano/geopoint_manager/master/docs/geopoint_manager_v5.2_screenshot.png)

---

<a name="italiano"></a>
# 🇮🇹 Italiano

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
4. **Interfaccia bilingue ITA / EN** — pulsante **🌐 IT/EN** per cambiare lingua al volo;
   preferenza salvata in `QSettings`.
5. **Gestione CRS flessibile** — auto-rilevamento o forzatura del sistema di riferimento
   (EPSG:4326, 3857, UTM e personalizzato).
6. **Export multiplo** — GeoPackage, Shapefile, GeoJSON, KML, CSV.
7. **Processing integration** — accessibile anche dal QGIS Processing Framework.

---

## Interfaccia utente

| Tab | Descrizione |
| --- | --- |
| **Dati OGR/GDAL** | Caricamento da URL (OGR/GDAL, Google Sheets, WFS…). Include Opzioni Avanzate (autenticazione, parametri, layer, CRS override) e salvataggio GeoPackage. |
| **Dati da layer QGIS** | Caricamento da layer già presenti nel progetto. Include la sezione *Configurazione campi e CRS* per selezione campi X/Y, CRS, nome layer virtuale e selezione colonne. |
| **Log** | Storico delle operazioni con timestamp. |
| **Info / About** | Documentazione del plugin (ITA/EN). |

La barra inferiore contiene: **Aggiungi layer vettoriale di punti**, **Esporta Layer…**, **Salva GPKG**, **🌐 IT/EN** e **Chiudi**.

---

## Workflow tipici

### Flusso base

1. Avvia il plugin (icona toolbar o menu Vettore).
2. Seleziona la sorgente dati (tab *Dati OGR/GDAL* o *Dati da layer QGIS*).
3. Inserisci l'URL o seleziona il layer.
4. I campi coordinate vengono rilevati automaticamente oppure si apre il dialogo
   *Seleziona Campi Coordinate e Colonne* per scegliere lat/lon e le colonne da includere.
5. Clicca **"Aggiungi layer vettoriale di punti"**.
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
- Compatibilità Qt5/PyQt5 (QGIS 3) e Qt6/PyQt6 (QGIS 4).
- Nuova struttura a 4 tab.
- Dialogo *Seleziona Campi Coordinate e Colonne*: lat/lon e selezione colonne in un unico passaggio.
- Pulsanti *Esporta Layer* e *Salva GPKG* nella barra inferiore, sempre visibili.

---

## Installazione

### Metodo 1 — Da ZIP (consigliato)

1. In QGIS: **Plugin → Gestisci e installa plugin → Installa da ZIP**
2. Seleziona il file `geopoint_manager_v5.2.zip`
3. Clicca *Installa plugin*

### Metodo 2 — Manuale

1. Copia la cartella `geopoint_manager/` in:
   - **Windows**: `%APPDATA%\QGIS\QGIS4\profiles\default\python\plugins\`
   - **Linux/macOS**: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
2. Riavvia QGIS
3. Abilita il plugin da **Plugin → Gestisci e installa plugin**

---

## Utilizzo

- **Toolbar**: clicca l'icona nella toolbar principale
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

by [@gbvitrano](https://github.com/gbvitrano) — [@opendatasicilia](https://opendatasicilia.it/)

---

<a name="english"></a>
# 🇬🇧 English

QGIS plugin to create **point vector layers** from data sources containing geographic coordinate fields (latitude/longitude).

**Compatibility:** QGIS 3.16+ / 4.x &nbsp;|&nbsp; **License:** GPL-2.0+
**Author:** [@gbvitrano](https://github.com/gbvitrano)

---

## Supported data sources

| Source | Notes |
| --- | --- |
| **Google Sheets** | Direct download via urllib, saved to GeoPackage |
| **OGR/GDAL URL** | Generic online sources |
| **WFS** | Web Feature Services |
| **GeoJSON, Shapefile (ZIP), KML/KMZ, GPX, CSV** | Local or remote files |
| **Existing QGIS layers** | Layers already loaded in the current project |

---

## Key features

1. **Automatic coordinate detection** — identifies lat/lon fields via keyword matching
   (e.g. `lat`, `latitude`, `y`, `northing`, `lon`, `lng`, `x`, `easting`…)
2. **Dynamic Virtual Layer** — creates QGIS virtual layers with SQL queries:

   ```sql
   SELECT *, make_point(CAST(lon AS REAL), CAST(lat AS REAL)) as geometry
   FROM source WHERE lon IS NOT NULL AND lat IS NOT NULL
   ```

3. **Google Sheets integration** — downloads CSV and saves to a local GeoPackage,
   with a persistent source registry (`_geopoint_sources`) and manual on-demand refresh.
4. **Bilingual ITA / EN interface** — **🌐 IT/EN** button to switch language on the fly;
   preference saved in `QSettings`.
5. **Flexible CRS management** — auto-detection or override of the reference system
   (EPSG:4326, 3857, UTM and custom).
6. **Multiple export formats** — GeoPackage, Shapefile, GeoJSON, KML, CSV.
7. **Processing integration** — also accessible from the QGIS Processing Framework.

---

## User interface

| Tab | Description |
| --- | --- |
| **OGR/GDAL Data** | Load from URL (OGR/GDAL, Google Sheets, WFS…). Includes Advanced Options (auth, params, layer, CRS override) and GeoPackage saving. |
| **QGIS layer data** | Load from layers already in the project. Includes the *Field and CRS configuration* section for X/Y fields, CRS, virtual layer name and column selection. |
| **Log** | Operation history with timestamps. |
| **Info / About** | Plugin documentation (ITA/EN). |

The bottom bar contains: **Add vector points layer**, **Export Layer…**, **Save GPKG**, **🌐 IT/EN** and **Close**.

---

## Typical workflows

### Basic flow

1. Launch the plugin (toolbar icon or Vector menu).
2. Select the data source (*OGR/GDAL Data* or *QGIS layer data* tab).
3. Enter the URL or select the layer.
4. Coordinate fields are detected automatically, or the *Select Coordinate Fields and Columns*
   dialog opens to choose lat/lon and which columns to include.
5. Click **"Add vector points layer"**.
6. Export if needed.

### Google Sheets

1. Share the Google Sheet publicly and copy the CSV export URL.
2. Specify the destination GeoPackage path.
3. Load the data; the plugin saves it locally.
4. To update: click **"↻ Update from Google Sheets"**.

---

## What's new in v5.2

- **Bilingual ITA / EN interface** — **🌐 IT/EN** button in the bottom bar to switch language on the fly;
  preference saved in `QSettings`.
- New `i18n.py` module with a complete dictionary (~120 strings) for Italian and English.
- *Info / About* tab content translated in both languages.
- Fix `NameError: info_browser` in `setup_ui`.

## What's new in v5.1

- Fixed Google Sheets loading on QGIS 4 (*urllib* handles HTTP redirects).
- Persistent GeoPackage-based storage for downloaded data.
- Manual on-demand refresh instead of auto-fetch.
- Qt5/PyQt5 (QGIS 3) and Qt6/PyQt6 (QGIS 4) compatibility.
- New 4-tab structure.
- *Select Coordinate Fields and Columns* dialog: lat/lon and column selection in a single step.
- *Export Layer* and *Save GPKG* buttons moved to the bottom bar, always visible.

---

## Installation

### Method 1 — From ZIP (recommended)

1. In QGIS: **Plugins → Manage and Install Plugins → Install from ZIP**
2. Select the file `geopoint_manager_v5.2.zip`
3. Click *Install Plugin*

### Method 2 — Manual

1. Copy the `geopoint_manager/` folder to:
   - **Windows**: `%APPDATA%\QGIS\QGIS4\profiles\default\python\plugins\`
   - **Linux/macOS**: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
2. Restart QGIS
3. Enable the plugin from **Plugins → Manage and Install Plugins**

---

## Usage

- **Toolbar**: click the icon in the main toolbar
- **Menu**: **Vector → GeoPoint Manager → GeoPoint Manager**
- **Processing**: search for "GeoPoint Manager" in the Processing Toolbox

---

## Plugin structure

```text
geopoint_manager/
├── __init__.py                  # QGIS entry point (classFactory)
├── plugin.py                    # Main class: toolbar, menu, provider
├── geopoint_manager_dialog.py   # Main logic, UI, Processing algorithm
├── i18n.py                      # ITA/EN internationalization module
├── metadata.txt                 # Plugin metadata (name, version, dependencies)
├── icons/
│   └── icon.svg                 # Plugin icon
└── README.md                    # This file
```

---

## License

GPL-2.0+

by [@gbvitrano](https://github.com/gbvitrano) — [@opendatasicilia](https://opendatasicilia.it/)

<img width="802" height="782" alt="2026-03-17_14h32_59" src="https://github.com/user-attachments/assets/775b7acd-fea9-4b32-b0f4-52205064f73b" /> <img width="802" height="782" alt="2026-03-17_14h33_15" src="https://github.com/user-attachments/assets/d3eedae1-395f-4cc3-8b5a-dbb669aebe14" /> <img width="802" height="782" alt="2026-03-17_14h33_50" src="https://github.com/user-attachments/assets/3eb6aedb-fa60-4829-b3d9-0869102b210c" /> <img width="802" height="782" alt="2026-03-17_14h33_37" src="https://github.com/user-attachments/assets/4c3d692f-a968-4565-b118-1b833013980e" />
