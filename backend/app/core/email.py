"""Email sending via SMTP - simple version"""
import smtplib
import ssl
import re
from datetime import datetime
from email.message import EmailMessage

from app.core.config import settings


def _otp_html(code: str) -> str:
    return (
        '<html><body style="font-family:Arial;background:#f5f7fb;padding:20px">'
        '<table align="center" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:12px;max-width:500px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,.08)">'
        '<tr><td style="background:linear-gradient(135deg,#3b82f6,#06b6d4);padding:24px;text-align:center;color:#fff">'
        '<h1 style="margin:0;font-size:22px">SERGAK AI</h1>'
        '<div style="font-size:12px;opacity:.85;margin-top:4px">SANOAT XAVFSIZLIGI</div>'
        '</td></tr>'
        '<tr><td style="padding:30px;color:#1a2238">'
        '<h2>Tizimga kirish kodi</h2>'
        '<p style="color:#5d6a85">Salom! Sergak AI tizimiga kirish uchun quyidagi kodni kiriting. Kod 10 daqiqa amal qiladi.</p>'
        '<div style="background:#f5f7fb;border-radius:10px;padding:20px;text-align:center;margin:20px 0">'
        '<div style="font-family:Courier New,monospace;font-size:32px;font-weight:bold;letter-spacing:8px;color:#3b82f6">' + code + '</div>'
        '</div>'
        '<p style="font-size:12px;color:#8d9bb8">Agar siz so\'rov yubormagan bo\'lsangiz, bu xabarni e\'tiborsiz qoldiring.</p>'
        '</td></tr>'
        '<tr><td style="background:#f5f7fb;padding:14px;text-align:center;font-size:11px;color:#8d9bb8">'
        'Sergak AI &middot; ' + str(datetime.now().year) +
        '</td></tr></table></body></html>'
    )


def _welcome_html(full_name: str, role: str, added_by: str) -> str:
    role_map = {"admin": "Administrator", "manager": "Menejer", "operator": "Operator", "auditor": "Auditor"}
    role_name = role_map.get(role, role)
    return (
        '<html><body style="font-family:Arial;background:#f5f7fb;padding:20px">'
        '<table align="center" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:12px;max-width:500px;overflow:hidden">'
        '<tr><td style="background:linear-gradient(135deg,#10b981,#059669);padding:24px;text-align:center;color:#fff">'
        '<h1 style="margin:0;font-size:20px">SERGAK AI ga xush kelibsiz!</h1>'
        '</td></tr>'
        '<tr><td style="padding:28px;color:#1a2238">'
        '<h2>Salom, ' + full_name + '!</h2>'
        '<p>Siz Sergak AI tizimiga ' + added_by + ' tomonidan qo\'shildingiz.</p>'
        '<p>Rolingiz: <b>' + role_name + '</b></p>'
        '<p>Tizimga kirish uchun emailingizni kiriting va 6-xonali kod yuboriladi.</p>'
        '</td></tr></table></body></html>'
    )


def send_email(to_email: str, subject: str, html_body: str) -> bool:
    """Send email. Falls back to file log if SMTP not configured."""
    log_path = settings.BASE_DIR / "email_log.txt"
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write("\n" + "=" * 60 + "\n")
            f.write("[" + datetime.now().isoformat() + "] TO: " + to_email + "\n")
            f.write("SUBJECT: " + subject + "\n")
            f.write("=" * 60 + "\n" + html_body + "\n")
    except Exception:
        pass

    print("[Email] To:", to_email, "| Subject:", subject)

    if not settings.SMTP_HOST or not settings.SMTP_USER:
        m = re.search(r'(\d{6})', html_body)
        if m:
            print("[Email] >>> DEMO: code =", m.group(1), "<<<")
        return False

    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
        msg["To"] = to_email
        msg.set_content("HTML email - please view in HTML client")
        msg.add_alternative(html_body, subtype="html")

        password = settings.SMTP_PASSWORD.replace(" ", "")
        ctx = ssl.create_default_context()

        if settings.SMTP_USE_TLS:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
                server.starttls(context=ctx)
                server.login(settings.SMTP_USER, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, context=ctx, timeout=15) as server:
                server.login(settings.SMTP_USER, password)
                server.send_message(msg)
        print("[Email] Sent OK to", to_email)
        return True
    except Exception as e:
        print("[Email] SMTP FAILED:", type(e).__name__, str(e)[:200])
        return False


def send_otp_email(to_email: str, code: str) -> bool:
    return send_email(to_email, "Sergak AI - Kirish kodi: " + code, _otp_html(code))


def send_welcome_email(to_email: str, full_name: str, role: str, added_by: str = "Admin") -> bool:
    return send_email(to_email, "Sergak AI - Xush kelibsiz!", _welcome_html(full_name, role, added_by))


def _approval_html(full_name: str, role: str, password: str) -> str:
    role_map = {"admin": "Administrator", "manager": "Menejer", "operator": "Operator", "auditor": "Auditor"}
    role_name = role_map.get(role, role)
    return (
        '<html><body style="font-family:Arial;background:#f5f7fb;padding:20px">'
        '<table align="center" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:12px;max-width:520px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,.08)">'
        '<tr><td style="background:linear-gradient(135deg,#10b981,#059669);padding:24px;text-align:center;color:#fff">'
        '<h1 style="margin:0;font-size:22px">SO\'ROVINGIZ TASDIQLANDI</h1>'
        '<div style="font-size:12px;opacity:.85;margin-top:4px">SERGAK AI</div>'
        '</td></tr>'
        '<tr><td style="padding:30px;color:#1a2238">'
        '<h2>Tabriklaymiz, ' + full_name + '!</h2>'
        '<p>Sizning Sergak AI tizimiga qo\'shilish so\'rovingiz admin tomonidan tasdiqlandi.</p>'
        '<p>Rolingiz: <b>' + role_name + '</b></p>'
        '<div style="background:#f5f7fb;border-radius:10px;padding:18px;margin:18px 0">'
        '<div style="font-size:12px;color:#5d6a85;margin-bottom:8px">Vaqtinchalik parol:</div>'
        '<div style="font-family:Courier New,monospace;font-size:18px;font-weight:bold;color:#10b981;letter-spacing:2px">' + password + '</div>'
        '</div>'
        '<p>Tizimga kirib parolingizni almashtirib oling. Yoki email orqali OTP kod bilan kiring.</p>'
        '</td></tr></table></body></html>'
    )


def _rejection_html(full_name: str) -> str:
    return (
        '<html><body style="font-family:Arial;background:#f5f7fb;padding:20px">'
        '<table align="center" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:12px;max-width:520px;overflow:hidden">'
        '<tr><td style="background:linear-gradient(135deg,#ef4444,#dc2626);padding:24px;text-align:center;color:#fff">'
        '<h1 style="margin:0;font-size:20px">SO\'ROV RAD ETILDI</h1>'
        '<div style="font-size:12px;opacity:.85;margin-top:4px">SERGAK AI</div>'
        '</td></tr>'
        '<tr><td style="padding:28px;color:#1a2238">'
        '<h2>Salom, ' + full_name + '</h2>'
        '<p>Afsuski, Sergak AI tizimiga qo\'shilish so\'rovingiz qabul qilinmadi.</p>'
        '<p>Qo\'shimcha ma\'lumot uchun korxona administratoriga murojaat qiling.</p>'
        '</td></tr></table></body></html>'
    )


def send_approval_email(to_email: str, full_name: str, role: str, password: str) -> bool:
    return send_email(to_email, "Sergak AI - So'rovingiz tasdiqlandi", _approval_html(full_name, role, password))


def send_rejection_email(to_email: str, full_name: str) -> bool:
    return send_email(to_email, "Sergak AI - So'rovingiz rad etildi", _rejection_html(full_name))
