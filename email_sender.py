import os
import csv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

SMTP_HOST      = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT      = int(os.getenv("SMTP_PORT", 587))
SENDER_EMAIL   = os.getenv("SENDER_EMAIL", "")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "")


def send_certificates(csv_path: str, renamed_folder: str,
                      subject: str = "Your Certificate is Here!",
                      body_template: str = "Dear {name},\n\nPlease find your certificate attached.\n\nBest regards,\nSmartCert Team",
                      filter_email: str = None,
                      sender_user: str = None,
                      sender_pass: str = None):
    """
    Send personalised certificate emails.
    
    If filter_email is provided, only participants with that email address will receive the email.
    If sender_user/sender_pass are provided, they override the .env defaults.
    """
    participants = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames:
            reader.fieldnames = [h.strip().lower() for h in reader.fieldnames]
        for row in reader:
            name  = row.get("name",  "").strip()
            email = row.get("email", "").strip()
            if name and email:
                participants.append({"name": name, "email": email})

    sent   = 0
    failed = 0
    report = []

    # Determine credentials
    final_user = sender_user if sender_user else SENDER_EMAIL
    final_pass = sender_pass if sender_pass else SENDER_PASSWORD

    # Open SMTP connection once
    try:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15)
        server.ehlo()
        server.starttls()
        server.login(final_user, final_pass)
    except Exception as e:
        for p in participants:
            report.append({"name": p["name"], "email": p["email"],
                           "status": "failed", "reason": f"SMTP error: {e}"})
            failed += 1
        return sent, failed, report

    for participant in participants:
        name  = participant["name"]
        email = participant["email"]

        # Only deliver to the logged-in user's email if specified
        if filter_email and email.lower() != filter_email.lower():
            continue

        # Find renamed certificate
        safe_name = name.replace(" ", "_").replace("/", "_")
        cert_file = None
        for fname in os.listdir(renamed_folder):
            if fname.startswith(safe_name + "_certificate"):
                cert_file = os.path.join(renamed_folder, fname)
                break

        if cert_file is None:
            report.append({"name": name, "email": email,
                           "status": "failed", "reason": "Certificate file not found"})
            failed += 1
            continue

        try:
            msg = MIMEMultipart()
            msg["From"]    = final_user
            msg["To"]      = email
            msg["Subject"] = subject

            # Personalise body
            body = body_template.replace("{name}", name)
            msg.attach(MIMEText(body, "plain"))

            # Attach certificate
            with open(cert_file, "rb") as fh:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(fh.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition",
                            f'attachment; filename="{os.path.basename(cert_file)}"')
            msg.attach(part)

            server.sendmail(final_user, email, msg.as_string())
            report.append({"name": name, "email": email, "status": "sent", "reason": ""})
            sent += 1

        except Exception as e:
            report.append({"name": name, "email": email,
                           "status": "failed", "reason": str(e)})
            failed += 1

    try:
        server.quit()
    except Exception:
        pass

    return sent, failed, report
