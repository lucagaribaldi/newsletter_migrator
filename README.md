# 📬 Newsletter Migrator (Brevo → Substack)

**Newsletter Migrator** è una web app in Streamlit che ti consente di:

- ✅ Estrarre le newsletter inviate da Brevo
- ✅ Convertirle in Markdown con immagini su Cloudinary
- ✅ Visualizzarle e salvarle in locale
- ✅ Pubblicarle su Substack come bozze (via Selenium)
- ✅ Tenere traccia delle newsletter già migrate
- ✅ Automatizzare il caricamento (batch 5-10 newsletter ogni 2h)

---

## 🚀 Funzionalità principali

### 🔄 Estrazione da Brevo
- Connessione API Brevo con `limit` + `offset`
- Filtra solo newsletter inviate (`status=sent`)
- Ordinamento cronologico
- Selettore newsletter da migrare
- Titolo pulito da `Cronache dal Consiglio n° xxx -`

### 📄 Conversione
- HTML → Markdown
- Upload immagini su Cloudinary
- Salvataggio file `.md` in `converted/`

### 📤 Pubblicazione su Substack
- Login con `cookies.json`
- Inserimento automatico di titolo e contenuto
- Salvataggio come **bozza**
- Script: `app/substack_bot.py`

### 🕓 Batch automatico
- Script in preparazione per invio ogni 2 ore di 5–10 newsletter

---

## 📁 Struttura del progetto

```
newsletter_migrator/
├── Home.py
├── pages/
│   └── Migrazione.py
├── converted/
├── exported_posts.json
├── cookies.json
├── app/
│   └── substack_bot.py
├── requirements.txt
├── .replit
└── README.md
```

---

## ▶️ Avvio su Replit

1. Inserisci le API nella sidebar (o come variabili ambiente):
   - `BREVO_API_KEY`
   - `CLOUDINARY_CLOUD_NAME`, `API_KEY`, `API_SECRET`

2. Carica i file:
   - `cookies.json` (Substack)
   - `exported_posts.json` (opzionale)

3. Premi **Run** su Replit per avviare l'app (`streamlit run Home.py`)

---

## 📦 Requisiti
```
streamlit
cloudinary
requests
beautifulsoup4
html2text
markdown2
selenium
```

---

## ✍️ Autore
Realizzato con ❤️ da [@lucagaribaldi](https://github.com/lucagaribaldi)