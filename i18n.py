# -*- coding: utf-8 -*-
"""
GeoPoint Manager - Internationalization module
Supports Italian (it) and English (en)
"""

from qgis.PyQt.QtCore import QSettings

_LANG = None  # lazy init from QSettings


def get_language():
    settings = QSettings()
    return settings.value("GeoPointManager/language", "it")


def set_language(lang):
    global _LANG
    if lang in STRINGS:
        _LANG = lang
        settings = QSettings()
        settings.setValue("GeoPointManager/language", lang)


def tr(key, *args, **kwargs):
    global _LANG
    if _LANG is None:
        _LANG = get_language()
    s = STRINGS.get(_LANG, STRINGS["it"]).get(key)
    if s is None:
        s = STRINGS["it"].get(key, key)
    if args:
        try:
            return s.format(*args)
        except Exception:
            return s
    if kwargs:
        try:
            return s.format(**kwargs)
        except Exception:
            return s
    return s


# ---------------------------------------------------------------------------
# About / Info HTML
# ---------------------------------------------------------------------------

_INFO_HTML_IT = """
<html><body style="font-family: sans-serif; font-size: 13px; padding: 8px;">
<h2 style="color:#2196F3;">GeoPoint Manager v5.3</h2>
<p>Plugin QGIS per creare <b>layer vettoriali di punti</b> a partire da sorgenti dati contenenti
campi di coordinate geografiche (latitudine/longitudine).</p>
<p><b>Compatibilità:</b> QGIS 3.16+ / 4.x &nbsp;|&nbsp; <b>Licenza:</b> GPL-2.0+<br>
<b>Autore:</b> <a href="https://github.com/gbvitrano">@gbvitrano</a></p>
<hr>
<h3>Sorgenti dati supportate</h3>
<table border="1" cellspacing="0" cellpadding="4" style="border-collapse:collapse; width:100%;">
  <tr style="background:#e3f2fd;"><th>Sorgente</th><th>Note</th></tr>
  <tr><td><b>Google Sheets</b></td><td>Download diretto via urllib, salvataggio in GeoPackage</td></tr>
  <tr><td><b>URL OGR/GDAL</b></td><td>Fonti online generiche</td></tr>
  <tr><td><b>WFS</b></td><td>Web Feature Services</td></tr>
  <tr><td><b>GeoJSON, Shapefile (ZIP), KML/KMZ, GPX, CSV</b></td><td>File locali o remoti</td></tr>
  <tr><td><b>Layer QGIS esistenti</b></td><td>Layer già caricati nel progetto corrente</td></tr>
</table>
<hr>
<h3>Funzionalità principali</h3>
<ol>
  <li><b>Rilevamento automatico coordinate</b> — individua i campi lat/lon tramite keyword matching
      (es. <code>lat</code>, <code>latitude</code>, <code>y</code>, <code>northing</code>,
      <code>lon</code>, <code>lng</code>, <code>x</code>, <code>easting</code>…)</li>
  <li><b>Virtual Layer dinamico</b> — crea layer virtuali QGIS con query SQL.</li>
  <li><b>Google Sheets integration</b> — salva i CSV scaricati in un GeoPackage locale,
      con registro persistente (<code>_geopoint_sources</code>) e refresh manuale on-demand.</li>
  <li><b>Gestione CRS flessibile</b> — auto-rilevamento o forzatura del sistema di riferimento.</li>
  <li><b>Separatore CSV personalizzato</b> — virgola, punto e virgola, tab, pipe o carattere custom.</li>
  <li><b>Opzioni Record e Campi CSV</b> — righe da saltare, virgola come separatore decimale, tronca campi, scarta campi vuoti.</li>
  <li><b>Export multiplo</b> — GeoPackage, Shapefile, GeoJSON, KML, CSV.</li>
  <li><b>Processing integration</b> — accessibile anche dal QGIS Processing Framework.</li>
</ol>
<hr>
<h3>Interfaccia utente</h3>
<table border="1" cellspacing="0" cellpadding="4" style="border-collapse:collapse; width:100%;">
  <tr style="background:#e3f2fd;"><th>Tab</th><th>Descrizione</th></tr>
  <tr><td><b>Dati OGR/GDAL</b></td><td>Caricamento da URL. Include separatore CSV, opzioni record/campi, Opzioni Avanzate e salvataggio GeoPackage.</td></tr>
  <tr><td><b>Dati da layer QGIS</b></td><td>Caricamento da layer già presenti nel progetto.</td></tr>
  <tr><td><b>Log</b></td><td>Storico delle operazioni con timestamp.</td></tr>
  <tr><td><b>Info / About</b></td><td>Documentazione del plugin.</td></tr>
</table>
<hr>
<h3>Novità v5.3</h3>
<ul>
  <li><b>Separatore CSV personalizzato</b> — selettore virgola / punto e virgola / tab / pipe / personalizzato.</li>
  <li><b>Opzioni Record e Campi</b> — righe da saltare, la virgola è il separatore decimale (es. <code>38,126112</code> → <code>38.126112</code>), tronca campi, scarta campi vuoti.</li>
  <li>Opzioni applicate anche al refresh Google Sheets.</li>
</ul>
<h3>Novità v5.2</h3>
<ul>
  <li><b>Interfaccia bilingue ITA / EN</b> — pulsante <b>🌐 IT/EN</b> nella barra inferiore per cambiare lingua al volo.</li>
  <li>Nuovo modulo <code>i18n.py</code> con ~120 stringhe tradotte.</li>
  <li>Fix <code>NameError: info_browser</code> in <code>setup_ui</code>.</li>
</ul>
<h3>Novità v5.1</h3>
<ul>
  <li>Fix caricamento Google Sheets su QGIS 4 (<i>urllib</i> gestisce i redirect HTTP).</li>
  <li>Storage persistente basato su GeoPackage per i dati scaricati.</li>
  <li>Refresh manuale on-demand.</li>
  <li>Compatibilità Qt5/PyQt5 (QGIS 3) e Qt6/PyQt6 (QGIS 4).</li>
</ul>
<hr>
<p>by <a href="https://github.com/gbvitrano">@gbvitrano</a> —
<a href="https://opendatasicilia.it/">@opendatasicilia</a></p>
<p style="color:#888888; font-size:10px; font-style:italic;">
Repository: <a href="https://github.com/gbvitrano/geopoint_manager">github.com/gbvitrano/geopoint_manager</a></p>
</body></html>
"""

_INFO_HTML_EN = """
<html><body style="font-family: sans-serif; font-size: 13px; padding: 8px;">
<h2 style="color:#2196F3;">GeoPoint Manager v5.3</h2>
<p>QGIS plugin to create <b>point vector layers</b> from data sources containing
geographic coordinate fields (latitude/longitude).</p>
<p><b>Compatibility:</b> QGIS 3.16+ / 4.x &nbsp;|&nbsp; <b>License:</b> GPL-2.0+<br>
<b>Author:</b> <a href="https://github.com/gbvitrano">@gbvitrano</a></p>
<hr>
<h3>Supported data sources</h3>
<table border="1" cellspacing="0" cellpadding="4" style="border-collapse:collapse; width:100%;">
  <tr style="background:#e3f2fd;"><th>Source</th><th>Notes</th></tr>
  <tr><td><b>Google Sheets</b></td><td>Direct download via urllib, saved to GeoPackage</td></tr>
  <tr><td><b>OGR/GDAL URL</b></td><td>Generic online sources</td></tr>
  <tr><td><b>WFS</b></td><td>Web Feature Services</td></tr>
  <tr><td><b>GeoJSON, Shapefile (ZIP), KML/KMZ, GPX, CSV</b></td><td>Local or remote files</td></tr>
  <tr><td><b>Existing QGIS layers</b></td><td>Layers already loaded in the current project</td></tr>
</table>
<hr>
<h3>Key features</h3>
<ol>
  <li><b>Automatic coordinate detection</b> — identifies lat/lon fields via keyword matching
      (e.g. <code>lat</code>, <code>latitude</code>, <code>y</code>, <code>northing</code>,
      <code>lon</code>, <code>lng</code>, <code>x</code>, <code>easting</code>…)</li>
  <li><b>Dynamic Virtual Layer</b> — creates QGIS virtual layers with SQL queries.</li>
  <li><b>Google Sheets integration</b> — downloads CSV and saves to a local GeoPackage,
      with a persistent source registry (<code>_geopoint_sources</code>) and manual on-demand refresh.</li>
  <li><b>Flexible CRS management</b> — auto-detection or override of the reference system.</li>
  <li><b>Custom CSV separator</b> — comma, semicolon, tab, pipe or custom character.</li>
  <li><b>CSV Record and Field Options</b> — skip rows, comma as decimal separator, trim fields, discard empty fields.</li>
  <li><b>Multiple export formats</b> — GeoPackage, Shapefile, GeoJSON, KML, CSV.</li>
  <li><b>Processing integration</b> — also accessible from the QGIS Processing Framework.</li>
</ol>
<hr>
<h3>User interface</h3>
<table border="1" cellspacing="0" cellpadding="4" style="border-collapse:collapse; width:100%;">
  <tr style="background:#e3f2fd;"><th>Tab</th><th>Description</th></tr>
  <tr><td><b>OGR/GDAL Data</b></td><td>Load from URL. Includes CSV separator, record/field options, Advanced Options and GeoPackage saving.</td></tr>
  <tr><td><b>QGIS layer data</b></td><td>Load from layers already present in the project.</td></tr>
  <tr><td><b>Log</b></td><td>Operation history with timestamps.</td></tr>
  <tr><td><b>Info / About</b></td><td>Plugin documentation.</td></tr>
</table>
<hr>
<h3>What's new in v5.3</h3>
<ul>
  <li><b>Custom CSV separator</b> — comma / semicolon / tab / pipe / custom selector.</li>
  <li><b>Record and Field Options</b> — skip header rows, comma as decimal separator (e.g. <code>38,126112</code> → <code>38.126112</code>), trim fields, discard empty fields.</li>
  <li>All options also apply when refreshing Google Sheets data.</li>
</ul>
<h3>What's new in v5.2</h3>
<ul>
  <li><b>Bilingual ITA / EN interface</b> — <b>🌐 IT/EN</b> button in the bottom bar to switch language on the fly.</li>
  <li>New <code>i18n.py</code> module with ~120 translated strings.</li>
  <li>Fix <code>NameError: info_browser</code> in <code>setup_ui</code>.</li>
</ul>
<h3>What's new in v5.1</h3>
<ul>
  <li>Fixed Google Sheets loading on QGIS 4 (<i>urllib</i> handles HTTP redirects).</li>
  <li>Persistent GeoPackage-based storage for downloaded data.</li>
  <li>Manual on-demand refresh.</li>
  <li>Qt5/PyQt5 (QGIS 3) and Qt6/PyQt6 (QGIS 4) compatibility.</li>
</ul>
<hr>
<p>by <a href="https://github.com/gbvitrano">@gbvitrano</a> —
<a href="https://opendatasicilia.it/">@opendatasicilia</a></p>
<p style="color:#888888; font-size:10px; font-style:italic;">
Repository: <a href="https://github.com/gbvitrano/geopoint_manager">github.com/gbvitrano/geopoint_manager</a></p>
</body></html>
"""

# ---------------------------------------------------------------------------
# String dictionaries
# ---------------------------------------------------------------------------

STRINGS = {
    "it": {
        # Window titles
        "main_title":             "GeoPoint Manager - v5.3",
        "coord_dialog_title":     "Seleziona Campi Coordinate e Colonne",
        "refresh_dialog_title":   "Aggiorna sorgenti Google Sheets",
        "gs_help_dialog_title":   "Guida Google Sheets CSV",
        "crs_dialog_title":       "Seleziona CRS",
        "export_dialog_title":    "Esporta layer punti",
        "quick_save_dialog_title":"Salvataggio Rapido GeoPackage",
        "browse_gpkg_title":      "Salva GeoPackage",
        "open_gpkg_title":        "Apri GeoPackage esistente",
        # Common buttons
        "ok":      "OK",
        "cancel":  "Annulla",
        "close":   "Chiudi",
        "browse":  "Sfoglia...",
        # CoordinateFieldsDialog
        "coord_select_title":    "Seleziona i campi per le coordinate:",
        "coord_available_fields":"Campi disponibili: {}",
        "coord_lat_field":       "Campo Latitudine (Y):",
        "coord_lon_field":       "Campo Longitudine (X):",
        "coord_decimal_note":    "I valori devono essere coordinate decimali (es: 45.123, 12.456)",
        "coord_columns_title":   "Colonne da includere nel layer virtuale:",
        "coord_columns_note":    "Deseleziona le colonne che non ti servono. I campi coordinate sono sempre inclusi.",
        "select_all":            "Seleziona tutte",
        "col_count":             "{} colonne selezionate",
        "auto_detect_btn":       "Auto-detect coordinate",
        # RefreshSourcesDialog
        "refresh_header_1":    "<b>1 sorgente registrata nel GeoPackage.</b><br>Seleziona i layer da risincronizzare con Google Sheets:",
        "refresh_header_n":    "<b>{} sorgenti registrate nel GeoPackage.</b><br>Seleziona i layer da risincronizzare con Google Sheets:",
        "last_updated_tooltip":"URL: {}\nUltimo aggiornamento: {}",
        "select_all_btn":      "Seleziona tutti",
        "deselect_all_btn":    "Deseleziona tutti",
        "update_selected_btn": "↻  Aggiorna selezionati",
        # CheckableComboBox
        "combo_n_cols":         "{} colonne selezionate  ▾",
        "combo_n_cols_label":   "{} Colonne selezionate",
        "deselect_all_tooltip": "Deseleziona tutte",
        "close_popup_tooltip":  "Chiudi",
        # Main dialog – OGR tab
        "url_source_label":              "URL sorgente dati:",
        "url_placeholder":               "Link tipo per Google Sheets - https://docs.google.com/spreadsheets/d/[ID_DEL_FILE]/export?format=csv&gid=[ID_DEL_FOGLIO]",
        "gs_help_btn":                   "Google Sheets",
        "gs_help_tooltip":               "Guida per Google Sheets CSV",
        "format_label":                  "Formato:",
        "name_label":                    "Nome:",
        "layer_custom_name_placeholder": "Nome layer personalizzato",
        "layer_custom_name_tooltip":     "Nome personalizzato per il layer (opzionale)",
        "table_only_radio":              "Solo tabella dati",
        "table_only_tooltip":            "Scarica i dati come layer tabellare senza mappatura automatica",
        "direct_points_radio":           "Aggiungi tabella dati e layer virtuale",
        "direct_points_tooltip":         "Crea automaticamente il layer di punti mappando i campi coordinate",
        "csv_sep_label":                 "Separatore CSV:",
        "csv_sep_tooltip":               "Separatore di campo usato nel file CSV",
        "csv_sep_comma":                 "Virgola (,)",
        "csv_sep_semicolon":             "Punto e virgola (;)",
        "csv_sep_tab":                   "Tab (\\t)",
        "csv_sep_pipe":                  "Pipe (|)",
        "csv_sep_custom":                "Personalizzato",
        "csv_sep_custom_placeholder":    "Inserisci il separatore",
        "csv_opts_group":                "Opzioni Record e Campi",
        "csv_skip_rows_label":           "Righe intestazione da saltare:",
        "csv_skip_rows_tooltip":         "Numero di righe iniziali da ignorare prima dell'intestazione",
        "csv_has_header":                "Il primo record ha i nomi dei campi",
        "csv_has_header_tooltip":        "La prima riga (dopo le righe saltate) contiene i nomi delle colonne",
        "csv_decimal_comma":             "La virgola è il separatore decimale",
        "csv_decimal_comma_tooltip":     "I valori numerici usano la virgola come separatore decimale (es. 38,126112)",
        "csv_trim_fields":               "Tronca campi",
        "csv_trim_fields_tooltip":       "Rimuove gli spazi iniziali e finali da ogni valore",
        "csv_discard_empty":             "Scarta i campi vuoti",
        "csv_discard_empty_tooltip":     "Ignora i campi vuoti alla fine di ogni riga",
        "advanced_options_title":        "Opzioni Avanzate",
        "gpkg_save_label":               "Salva dati come GeoPackage (richiesto per Google Sheets):",
        "gpkg_path_placeholder":         "Percorso file .gpkg — lascia vuoto per scegliere al caricamento",
        "gpkg_path_tooltip":             "Percorso GeoPackage in cui salvare i dati scaricati da Google Sheets",
        "load_ogr_btn":                  "Carica dati OGR/GDAL",
        "open_gpkg_btn":                 "📂  Apri GeoPackage esistente",
        "open_gpkg_tooltip":             "Seleziona un GeoPackage già esistente per aggiornarne i layer",
        "refresh_gs_btn":                "↻  Aggiorna da Google Sheets",
        "refresh_gs_tooltip":            "Legge la registry dal GeoPackage e aggiorna i layer registrati",
        "tab_ogr":                       "Dati OGR/GDAL",
        "tab_layer":                     "Dati da layer QGIS",
        "tab_log":                       "Log",
        "tab_info":                      "Info / About",
        # Main dialog – Layer tab
        "select_layer_label":     "Seleziona un layer vettoriale dal progetto:",
        "fields_crs_group":       "Configurazione campi e CRS",
        "x_lon_label":            "X (Lon):",
        "y_lat_label":            "Y (Lat):",
        "refresh_fields_tooltip": "Aggiorna campi",
        "crs_label":              "CRS:",
        "custom_crs_btn":         "CRS...",
        "custom_crs_tooltip":     "Seleziona CRS personalizzato",
        "crs_current":            "CRS: EPSG:4326 - WGS 84",
        "layer_name_label":       "Nome Layer virtuale:",
        "layer_name_default":     "Punti_virtuali",
        "columns_label":          "Colonne:",
        "columns_no_layer":       "— nessun layer caricato —",
        "columns_btn_tooltip":    "Modifica le colonne incluse nel layer virtuale",
        "columns_n_of_m":         "{} / {} colonne selezionate  ✎",
        # Bottom bar
        "create_points_btn":  "Aggiungi layer vettoriale di punti",
        "export_btn":         "Esporta Layer...",
        "export_btn_tooltip": "Apre il dialogo nativo di QGIS per esportare in tutti i formati supportati",
        "quick_save_btn":     "Salva GPKG",
        "quick_save_tooltip": "Salvataggio rapido come GeoPackage",
        "footer":             "GeoPoint Manager - v5.3",
        # Language button
        "lang_btn":         "🌐 EN",
        "lang_btn_tooltip": "Switch to English / Passa all'inglese",
        # Log
        "log_ready":        "GeoPoint Manager v5.3 pronto - Google Sheets → GeoPackage, aggiornamento manuale on-demand...",
        "log_mode_ogr":     "Modalità: Caricamento dati da URL",
        "log_mode_layer":   "Modalità: Layer dal progetto QGIS",
        "log_fields_updated": "Campi aggiornati",
        # Google Sheets help
        "gs_help_title":       "Google Sheets -> URL tipo",
        "gs_help_example_label":"Esempio URL:",
        "gs_help_steps_label": "Passi:",
        "gs_help_steps":       "1. Condividi il foglio: \"Chiunque con link possa visualizzare\"\n2. Sostituisci [ID] con l'ID del documento\n3. Sostituisci [SHEET_ID] con l'ID del foglio (opzionale)\n4. Il foglio deve avere colonne Lat/Long con coordinate decimali",
        # Messages – titles
        "err_title":          "Errore",
        "success_title":      "Successo",
        "no_sources_title":   "Nessuna sorgente",
        "update_done_title":  "Aggiornamento completato",
        # Messages – errors
        "err_no_url":          "Inserisci un URL valido!",
        "err_url_scheme":      "L'URL deve iniziare con http://, https:// o ftp://",
        "err_no_source_layer": "Nessun layer di origine selezionato!",
        "err_no_xy_fields":    "Seleziona i campi X e Y!",
        "err_no_coord_fields": "Devi selezionare entrambi i campi di coordinate!",
        "err_fields_not_found":"I campi selezionati non esistono nel dataset!",
        "err_load_url":        "Impossibile caricare i dati dall'URL.",
        "err_create_points":   "Impossibile creare il layer di punti.",
        "err_no_export_layer": "Nessun layer da esportare!",
        "err_no_save_layer":   "Nessun layer da salvare!",
        "err_export":          "Errore durante l'esportazione: {}",
        "err_generic":         "Errore: {}",
        "err_gpkg_path":       "Inserisci il percorso del GeoPackage nel campo apposito.",
        "err_save_gpkg":       "Errore salvataggio: {}",
        "no_sources_msg":      "Nessuna sorgente Google Sheets registrata in questo GeoPackage.\nCarica prima un Google Sheet per registrarlo.",
        # Messages – success / info
        "success_export":       "Layer esportato con successo!\n\nFormato: {}\nFile: {}",
        "success_save_gpkg":    "GeoPackage salvato con successo!\n\nFile: {}\nPercorso: {}",
        "success_load":         "Dati caricati e mappati automaticamente!\n\nLayer punti: {}\nLayer origine: {}\nX (Lon): {}, Y (Lat): {}\nFeatures: {} / {}\nCRS: {}{}",
        "success_load_table":   "Layer caricato: {}\n\nTipo: {}\nCRS: {}\nFeatures: {}{}\n\nUsa la scheda 'Layer QGIS' per configurare la mappatura dei punti.",
        "success_points":       "Layer punti creato con successo!\n\nNome: {}\nTipo: Virtual Layer (auto-update)\nFeatures: {}\nCRS: {}\n\n✓ Il layer si aggiorna automaticamente con la sorgente!",
        "gs_note":              "\nGeoPackage: {}\n✓ Usa '↻ Aggiorna dati' per sincronizzare con Google Sheets.",
        "cancel_user":          "Operazione annullata dall'utente",
        "cancel_export":        "Esportazione annullata dall'utente",
        "cancel_fields":        "Selezione campi annullata dall'utente",
        # Refresh results table
        "tbl_layer":   "Layer",
        "tbl_before":  "Prima",
        "tbl_after":   "Dopo",
        "tbl_delta":   "Variazione",
        "delta_new":   "nuovo",
        "delta_none":  "nessuna",
        "log_update_done": "Aggiornamento completato:\n{}",
        # GeoPackage open
        "gpkg_opened_sources_1": "GeoPackage aperto: 1 sorgente registrata → {}",
        "gpkg_opened_sources_n": "GeoPackage aperto: {} sorgenti registrate → {}",
        "gpkg_opened_no_sources":"GeoPackage aperto — nessuna sorgente Google Sheets registrata",
        # Processing
        "processing_help": "<h3>GeoPoint Manager v5.3</h3><p>Plugin per creare layer di punti da sorgenti dati con coordinate</p>",
        "processing_long_name": "GeoPoint Manager - Strumenti per la gestione di punti geografici",
        # About
        "info_html": _INFO_HTML_IT,
    },

    "en": {
        # Window titles
        "main_title":             "GeoPoint Manager - v5.3",
        "coord_dialog_title":     "Select Coordinate Fields and Columns",
        "refresh_dialog_title":   "Update Google Sheets Sources",
        "gs_help_dialog_title":   "Google Sheets CSV Guide",
        "crs_dialog_title":       "Select CRS",
        "export_dialog_title":    "Export points layer",
        "quick_save_dialog_title":"Quick Save GeoPackage",
        "browse_gpkg_title":      "Save GeoPackage",
        "open_gpkg_title":        "Open existing GeoPackage",
        # Common buttons
        "ok":     "OK",
        "cancel": "Cancel",
        "close":  "Close",
        "browse": "Browse...",
        # CoordinateFieldsDialog
        "coord_select_title":    "Select fields for coordinates:",
        "coord_available_fields":"Available fields: {}",
        "coord_lat_field":       "Latitude field (Y):",
        "coord_lon_field":       "Longitude field (X):",
        "coord_decimal_note":    "Values must be decimal coordinates (e.g.: 45.123, 12.456)",
        "coord_columns_title":   "Columns to include in the virtual layer:",
        "coord_columns_note":    "Deselect columns you don't need. Coordinate fields are always included.",
        "select_all":            "Select all",
        "col_count":             "{} columns selected",
        "auto_detect_btn":       "Auto-detect coordinates",
        # RefreshSourcesDialog
        "refresh_header_1":    "<b>1 source registered in the GeoPackage.</b><br>Select layers to re-sync with Google Sheets:",
        "refresh_header_n":    "<b>{} sources registered in the GeoPackage.</b><br>Select layers to re-sync with Google Sheets:",
        "last_updated_tooltip":"URL: {}\nLast updated: {}",
        "select_all_btn":      "Select all",
        "deselect_all_btn":    "Deselect all",
        "update_selected_btn": "↻  Update selected",
        # CheckableComboBox
        "combo_n_cols":         "{} columns selected  ▾",
        "combo_n_cols_label":   "{} Columns selected",
        "deselect_all_tooltip": "Deselect all",
        "close_popup_tooltip":  "Close",
        # Main dialog – OGR tab
        "url_source_label":              "Data source URL:",
        "url_placeholder":               "e.g. Google Sheets - https://docs.google.com/spreadsheets/d/[FILE_ID]/export?format=csv&gid=[SHEET_ID]",
        "gs_help_btn":                   "Google Sheets",
        "gs_help_tooltip":               "Google Sheets CSV guide",
        "format_label":                  "Format:",
        "name_label":                    "Name:",
        "layer_custom_name_placeholder": "Custom layer name",
        "layer_custom_name_tooltip":     "Custom name for the layer (optional)",
        "table_only_radio":              "Table data only",
        "table_only_tooltip":            "Download data as a tabular layer without automatic coordinate mapping",
        "direct_points_radio":           "Add data table and virtual layer",
        "direct_points_tooltip":         "Automatically create the points layer by mapping coordinate fields",
        "csv_sep_label":                 "CSV Separator:",
        "csv_sep_tooltip":               "Field separator used in the CSV file",
        "csv_sep_comma":                 "Comma (,)",
        "csv_sep_semicolon":             "Semicolon (;)",
        "csv_sep_tab":                   "Tab (\\t)",
        "csv_sep_pipe":                  "Pipe (|)",
        "csv_sep_custom":                "Custom",
        "csv_sep_custom_placeholder":    "Enter separator character",
        "csv_opts_group":                "Record and Field Options",
        "csv_skip_rows_label":           "Header rows to skip:",
        "csv_skip_rows_tooltip":         "Number of initial rows to ignore before the header",
        "csv_has_header":                "First record has field names",
        "csv_has_header_tooltip":        "The first row (after skipped rows) contains column names",
        "csv_decimal_comma":             "Comma is the decimal separator",
        "csv_decimal_comma_tooltip":     "Numeric values use comma as decimal separator (e.g. 38,126112)",
        "csv_trim_fields":               "Trim fields",
        "csv_trim_fields_tooltip":       "Remove leading and trailing whitespace from each value",
        "csv_discard_empty":             "Discard empty fields",
        "csv_discard_empty_tooltip":     "Ignore empty fields at the end of each row",
        "advanced_options_title":        "Advanced Options",
        "gpkg_save_label":               "Save data as GeoPackage (required for Google Sheets):",
        "gpkg_path_placeholder":         ".gpkg file path — leave empty to choose at load time",
        "gpkg_path_tooltip":             "GeoPackage path to save data downloaded from Google Sheets",
        "load_ogr_btn":                  "Load OGR/GDAL data",
        "open_gpkg_btn":                 "📂  Open existing GeoPackage",
        "open_gpkg_tooltip":             "Select an existing GeoPackage to update its layers",
        "refresh_gs_btn":                "↻  Update from Google Sheets",
        "refresh_gs_tooltip":            "Reads the registry from the GeoPackage and updates registered layers",
        "tab_ogr":                       "OGR/GDAL Data",
        "tab_layer":                     "QGIS layer data",
        "tab_log":                       "Log",
        "tab_info":                      "Info / About",
        # Main dialog – Layer tab
        "select_layer_label":     "Select a vector layer from the project:",
        "fields_crs_group":       "Field and CRS configuration",
        "x_lon_label":            "X (Lon):",
        "y_lat_label":            "Y (Lat):",
        "refresh_fields_tooltip": "Refresh fields",
        "crs_label":              "CRS:",
        "custom_crs_btn":         "CRS...",
        "custom_crs_tooltip":     "Select custom CRS",
        "crs_current":            "CRS: EPSG:4326 - WGS 84",
        "layer_name_label":       "Virtual layer name:",
        "layer_name_default":     "Virtual_points",
        "columns_label":          "Columns:",
        "columns_no_layer":       "— no layer loaded —",
        "columns_btn_tooltip":    "Edit columns included in the virtual layer",
        "columns_n_of_m":         "{} / {} columns selected  ✎",
        # Bottom bar
        "create_points_btn":  "Add vector points layer",
        "export_btn":         "Export Layer...",
        "export_btn_tooltip": "Opens the native QGIS dialog to export in all supported formats",
        "quick_save_btn":     "Save GPKG",
        "quick_save_tooltip": "Quick save as GeoPackage",
        "footer":             "GeoPoint Manager - v5.3",
        # Language button
        "lang_btn":         "🌐 IT",
        "lang_btn_tooltip": "Passa all'italiano / Switch to Italian",
        # Log
        "log_ready":          "GeoPoint Manager v5.3 ready - Google Sheets → GeoPackage, manual on-demand update...",
        "log_mode_ogr":       "Mode: Loading data from URL",
        "log_mode_layer":     "Mode: Layer from QGIS project",
        "log_fields_updated": "Fields updated",
        # Google Sheets help
        "gs_help_title":        "Google Sheets -> URL format",
        "gs_help_example_label":"Example URL:",
        "gs_help_steps_label":  "Steps:",
        "gs_help_steps":        "1. Share the sheet: \"Anyone with the link can view\"\n2. Replace [ID] with the document ID\n3. Replace [SHEET_ID] with the sheet ID (optional)\n4. The sheet must have Lat/Long columns with decimal coordinates",
        # Messages – titles
        "err_title":         "Error",
        "success_title":     "Success",
        "no_sources_title":  "No sources",
        "update_done_title": "Update completed",
        # Messages – errors
        "err_no_url":          "Please enter a valid URL!",
        "err_url_scheme":      "URL must start with http://, https:// or ftp://",
        "err_no_source_layer": "No source layer selected!",
        "err_no_xy_fields":    "Please select X and Y fields!",
        "err_no_coord_fields": "You must select both coordinate fields!",
        "err_fields_not_found":"Selected fields do not exist in the dataset!",
        "err_load_url":        "Cannot load data from URL.",
        "err_create_points":   "Cannot create the points layer.",
        "err_no_export_layer": "No layer to export!",
        "err_no_save_layer":   "No layer to save!",
        "err_export":          "Export error: {}",
        "err_generic":         "Error: {}",
        "err_gpkg_path":       "Please enter the GeoPackage path in the field provided.",
        "err_save_gpkg":       "Save error: {}",
        "no_sources_msg":      "No Google Sheets sources registered in this GeoPackage.\nLoad a Google Sheet first to register it.",
        # Messages – success / info
        "success_export":       "Layer exported successfully!\n\nFormat: {}\nFile: {}",
        "success_save_gpkg":    "GeoPackage saved successfully!\n\nFile: {}\nPath: {}",
        "success_load":         "Data loaded and mapped automatically!\n\nPoints layer: {}\nSource layer: {}\nX (Lon): {}, Y (Lat): {}\nFeatures: {} / {}\nCRS: {}{}",
        "success_load_table":   "Layer loaded: {}\n\nType: {}\nCRS: {}\nFeatures: {}{}\n\nUse the 'QGIS layer' tab to configure the points mapping.",
        "success_points":       "Points layer created successfully!\n\nName: {}\nType: Virtual Layer (auto-update)\nFeatures: {}\nCRS: {}\n\n✓ The layer updates automatically with the source!",
        "gs_note":              "\nGeoPackage: {}\n✓ Use '↻ Update from Google Sheets' to sync.",
        "cancel_user":          "Operation cancelled by user",
        "cancel_export":        "Export cancelled by user",
        "cancel_fields":        "Field selection cancelled by user",
        # Refresh results table
        "tbl_layer":   "Layer",
        "tbl_before":  "Before",
        "tbl_after":   "After",
        "tbl_delta":   "Change",
        "delta_new":   "new",
        "delta_none":  "none",
        "log_update_done": "Update completed:\n{}",
        # GeoPackage open
        "gpkg_opened_sources_1": "GeoPackage opened: 1 source registered → {}",
        "gpkg_opened_sources_n": "GeoPackage opened: {} sources registered → {}",
        "gpkg_opened_no_sources":"GeoPackage opened — no Google Sheets sources registered",
        # Processing
        "processing_help": "<h3>GeoPoint Manager v5.3</h3><p>Plugin to create point layers from data sources with coordinates</p>",
        "processing_long_name": "GeoPoint Manager - Tools for geographic point management",
        # About
        "info_html": _INFO_HTML_EN,
    },
}
