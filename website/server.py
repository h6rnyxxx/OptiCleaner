"""
OptiCleaner v4.0 - Local Web Server & SMTP Email Dispatcher
Serves the website locally and sends real license emails using Python's smtplib.
"""

import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse

WEBSITE_DIR = Path(__file__).resolve().parent
REPO_ROOT = WEBSITE_DIR.parent
RELEASES_DIR = REPO_ROOT / "releases"

PORT = 5000

# Optional SMTP Settings (configured via environment or defaults)
SMTP_SERVER = os.environ.get("SMTP_SERVER", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")


class OptiCleanerWebHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEBSITE_DIR), **kwargs)

    def do_POST(self):
        if self.path == "/api/send-license":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                email = data.get("email")
                hwid = data.get("hwid")
                token = data.get("token")

                email_sent = False
                if SMTP_SERVER and SMTP_USER and SMTP_PASS:
                    try:
                        msg = MIMEMultipart()
                        msg['From'] = SMTP_USER
                        msg['To'] = email
                        msg['Subject'] = "Ваша лицензия OptiCleaner v4.0 Pro"

                        body = f"""
                        <h2>Спасибо за выбор OptiCleaner v4.0 Pro!</h2>
                        <p><b>Ваш аппаратный HWID:</b> <code>{hwid}</code></p>
                        <p><b>Лицензионный ключ:</b></p>
                        <pre style="background:#131927;color:#00E5FF;padding:12px;border-radius:8px;">{token}</pre>
                        <p><a href="https://github.com/h6rnyxxx/OptiCleaner/releases/download/v4.0.0/OptiCleaner-v4.0.0-Windows.exe">Скачать программу OptiCleaner-v4.0.0-Windows.exe</a></p>
                        """
                        msg.attach(MIMEText(body, 'html'))

                        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
                        server.starttls()
                        server.login(SMTP_USER, SMTP_PASS)
                        server.send_message(msg)
                        server.quit()
                        email_sent = True
                    except Exception as err:
                        print(f"SMTP error: {err}")

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "email_sent": email_sent}).encode('utf-8'))
                return
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode('utf-8'))
                return

        super().do_POST()


def run():
    print(f"==================================================")
    print(f" OptiCleaner v4.0 Web Server running on port {PORT}")
    print(f" Open: http://localhost:{PORT}")
    print(f"==================================================")
    server = HTTPServer(('0.0.0.0', PORT), OptiCleanerWebHandler)
    server.serve_forever()


if __name__ == "__main__":
    run()
