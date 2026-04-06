# 🎓 SmartCert

**SmartCert** is a full-stack bulk certificate distribution web app built with Python Flask. It automates the process of sending personalized certificate emails to hundreds of participants in just a few clicks.

---

## ✨ Features

- 🔐 **Secure Authentication** — Auth Key gated signup, per-user SMTP credentials
- 📄 **CSV Upload** — Drag & drop participants list with live preview
- 🏆 **Bulk Certificate Upload** — PDF, PNG, JPG support, drag & drop
- ✉️ **Personalized Emails** — Custom subject, body with `{name}` placeholder
- 🔒 **Safety Mode** — Test sends go only to your own email; flip the toggle to go live
- 📊 **Delivery Report** — Full per-participant status, downloadable as CSV or PDF
- 🎨 **Premium UI** — Dark glassmorphism design, animated orbs, live email preview

---

## 🗂️ Project Structure

```
SmartCertApp/
├── app.py                  # Flask backend — routes, auth, session logic
├── email_sender.py         # SMTP email delivery engine
├── rename_certificates.py  # Maps CSV rows → renamed certificate files
├── report_generator.py     # Generates CSV & PDF delivery reports
├── smartcert.db            # SQLite user database (auto-created)
├── .env                    # SMTP & secret key configuration
├── static/
│   └── style.css           # Full custom dark-mode UI
├── templates/
│   ├── index.html          # Step 1 — Upload files
│   ├── compose.html        # Step 2 — Compose email
│   ├── result.html         # Step 3 — View delivery report
│   ├── login.html          # Login page
│   └── signup.html         # Signup page
└── uploads/                # Temp storage for uploaded files
```

---

## ⚙️ Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/SmartCertApp.git
cd SmartCertApp
```

### 2. Install dependencies
```bash
pip install flask python-dotenv fpdf2 werkzeug
```

### 3. Configure environment variables

Edit the `.env` file:
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_16_char_app_password
EMAIL_SUBJECT=Your Certificate is Here!
SECRET_KEY=your-secret-key-here
```

> ⚠️ **Use a Gmail App Password**, not your regular Gmail password.  
> Go to [Google App Passwords](https://myaccount.google.com/apppasswords) to generate one.

### 4. Run the application
```bash
python app.py
```

Open your browser and navigate to: **http://127.0.0.1:5000**

---

## ☁️ Deploy to Render

### 1. Push to GitHub
Make sure your project is pushed to a GitHub repository.

> ⚠️ **Add a `.gitignore`** to avoid committing secrets:
> ```
> .env
> smartcert.db
> uploads/
> renamed_certificates/
> __pycache__/
> ```

### 2. Create a new Web Service on Render
- Go to [render.com](https://render.com) → **New → Web Service**
- Connect your GitHub repo
- Set the following:

| Setting | Value |
|---------|-------|
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app:app` |

### 3. Add Environment Variables on Render
In your Render service → **Environment** tab, add:

| Key | Value |
|-----|-------|
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SENDER_EMAIL` | `your_email@gmail.com` |
| `SENDER_PASSWORD` | `your_app_password` |
| `SECRET_KEY` | `any-random-secret-string` |

### 4. Deploy
Click **Deploy** — Render will install dependencies and start gunicorn automatically.

> ⚠️ **Important — Ephemeral Storage:**  
> Render's free tier uses ephemeral storage. Uploaded files and the SQLite database are **wiped on every redeploy**. For persistent data, use [Render Disks](https://render.com/docs/disks) (paid) or migrate to PostgreSQL.

---

## 🚀 How to Use

### Step 1 — Sign Up
- Go to `/signup`
- Enter your name, work email, and SMTP credentials (Gmail + App Password)
- Use the **Authentication Key** provided by your admin (`Shamstabraiz@911` by default — change in `app.py`)

### Step 2 — Upload Files
- Upload a **CSV file** with `name` and `email` columns
- Upload one **certificate file per participant** (in the same row order as the CSV)

**CSV Format:**
```csv
name,email
Alice Smith,alice@example.com
Bob Jones,bob@example.com
```

### Step 3 — Compose Email
- Write your email **subject** and **body** (use `{name}` for personalization)
- Use the **live preview** to see how it'll look
- Toggle **Safety Mode**:
  - ✅ **ON** → Send only to your registered email (for testing)
  - ❌ **OFF** → Send to all participants in the CSV

### Step 4 — Send & Download Report
- Click **Send Certificates Now**
- View the full delivery report (Sent / Failed / Success Rate)
- Download the report as **CSV** or **PDF**

---

## 🔐 Security Notes

| Feature | Details |
|---------|---------|
| Auth Key | Prevents public registration |
| Password Hashing | Werkzeug PBKDF2-SHA256 |
| Safety Mode | Prevents accidental bulk sends |
| Per-user SMTP | Each user sends from their own Gmail account |
| Session Protection | All routes gated with `@login_required` |

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| `flask` | Web framework |
| `python-dotenv` | Load `.env` configuration |
| `fpdf2` | PDF report generation |
| `werkzeug` | Password hashing |

---

## 🛠️ Customization

### Change the Admin Auth Key
In `app.py`, line 31:
```python
AUTH_KEY = "YourNewSecretKey"
```

### Change default email subject
In `.env`:
```env
EMAIL_SUBJECT=Congratulations! Your Certificate Awaits
```

---

## 📸 Screenshots

| Page | Description |
|------|-------------|
| Upload | Drag & drop CSV + certificates with live preview |
| Compose | Email editor with live rendered preview panel |
| Results | Stats dashboard + full per-participant table |

---

## 📄 License

MIT License — free to use and modify.

---

> Built with ❤️ using Flask, SQLite, and vanilla CSS.
