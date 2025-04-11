
# 📓 CHANGELOG - newsletter_migrator

Storico delle principali modifiche al progetto.

---

## [v1.0.0] - 2025-04-11
### Aggiunto
- Prima versione funzionante con interfaccia Streamlit
- Connessione a Brevo tramite API key
- Upload di cookies.json per autenticazione su Substack
- Conversione HTML -> Markdown delle newsletter
- Pubblicazione su Substack come bozza tramite Selenium
- Archivio locale delle newsletter esportate (`exported_posts.json`)
- Visualizzazione anteprima contenuti

---

## [v1.1.0] - 2025-04-11
### Migliorato
- Aggiunta protezione contro duplicazioni
- Evidenziazione newsletter già migrate

---

## [v1.2.0] - 2025-04-11
### Aggiunto
- Struttura multipagina Streamlit:
  - `Home.py`
  - `pages/Migrazione.py`
  - `pages/Storico.py`
- Navigazione laterale Streamlit
- Rimozione di `streamlit_app.py` obsoleto
- Pagina di benvenuto con controllo file
