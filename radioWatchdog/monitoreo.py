
import os
import smtplib
import requests
import logging
import glob
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
from win10toast import ToastNotifier

# Inicialización
load_dotenv()
toaster = ToastNotifier()

# Configuración desde .env
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TO = os.getenv("EMAIL_TO")
STREAM_URL = os.getenv("STREAM_URL")
THRESHOLD_DBFS = int(os.getenv("THRESHOLD_DBFS", -35))
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Paths
HOY = datetime.now().strftime('%Y-%m-%d')
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, f"log_{HOY}.log")
TEMP_AUDIO_FILE = "temp_stream.mp3"

# Asegurar carpeta logs
os.makedirs(LOG_DIR, exist_ok=True)

# Configurar logging
logging.basicConfig(filename=LOG_FILE, level=logging.INFO)

def log(msg):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mensaje = f"[{now}] {msg}"
    print(mensaje)
    logging.info(mensaje)

def enviar_alerta(asunto, cuerpo):
    try:
        mensaje = MIMEMultipart()
        mensaje["From"] = EMAIL_FROM
        mensaje["To"] = EMAIL_TO
        mensaje["Subject"] = asunto
        mensaje.attach(MIMEText(cuerpo, "plain"))

        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(mensaje)

        log(f"📧 Alerta enviada: {asunto}")
    except Exception as e:
        log(f"🚫 Error al enviar email: {e}")

    try:
        toaster.show_toast(asunto, cuerpo, duration=10, threaded=True)
    except:
        pass

    enviar_alerta_telegram(f"{asunto}\n{cuerpo}")

def enviar_alerta_telegram(mensaje):
    try:
        token = TELEGRAM_BOT_TOKEN
        chat_id = TELEGRAM_CHAT_ID
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {"chat_id": chat_id, "text": mensaje}
        r = requests.post(url, data=data)
        if r.status_code == 200:
            log("📲 Alerta enviada a Telegram")
        else:
            log(f"❌ Error al enviar Telegram: {r.text}")
    except Exception as e:
        log(f"🚫 Error en función Telegram: {e}")

def bajar_fragmento():
    cmd = f'ffmpeg -y -i "{STREAM_URL}" -t 10 -acodec copy {TEMP_AUDIO_FILE} -loglevel error'
    return os.system(cmd) == 0 and os.path.exists(TEMP_AUDIO_FILE)

def analizar_audio(path):
    audio = AudioSegment.from_file(path)
    duracion_total = len(audio)
    partes_no_silencio = detect_nonsilent(audio, min_silence_len=1000, silence_thresh=THRESHOLD_DBFS)
    if not partes_no_silencio:
        return False
    tiempo_sonando = sum([end - start for start, end in partes_no_silencio])
    return (tiempo_sonando / duracion_total) * 100 >= 10

def limpiar_logs_viejos():
    ahora = datetime.now().timestamp()
    for archivo in glob.glob(os.path.join(LOG_DIR, "log_*.log")):
        if ahora - os.path.getmtime(archivo) > 30 * 86400:
            os.remove(archivo)
            log(f"🧹 Log eliminado: {archivo}")

def es_hora_de_resumen():
    ahora = datetime.now()
    return (ahora.hour == 6 or ahora.hour == 18) and ahora.minute < 5

def enviar_resumen_telegram():
    ahora = datetime.now()
    desde = ahora - timedelta(hours=6)
    ok_count = 0
    caidas = []

    for archivo in glob.glob(os.path.join(LOG_DIR, "log_*.log")):
        with open(archivo, "r", encoding="utf-8") as f:
            for linea in f:
                try:
                    fecha_str = linea.split("]")[0].strip("[")
                    fecha = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
                    if fecha >= desde:
                        if "🎵 Stream funcionando correctamente" in linea:
                            ok_count += 1
                        elif "❌" in linea or "🔇" in linea:
                            caidas.append(fecha.strftime("%H:%M"))
                except:
                    continue

    if not caidas:
        mensaje = f"✅ Resumen de las últimas 6hs: todo OK ({ok_count} chequeos correctos)."
    else:
        mensaje = f"⚠️ Resumen 6hs: {ok_count} OK / {len(caidas)} caídas.\nPrimer error: {caidas[0]}"

    enviar_alerta_telegram(mensaje)

def monitorear():
    log("⏱ Iniciando monitoreo...")
    limpiar_logs_viejos()

    if not bajar_fragmento():
        msg = "No se pudo acceder al stream."
        log(f"❌ {msg}")
        enviar_alerta("🛑 ALERTA: Stream caído", msg)
    elif not analizar_audio(TEMP_AUDIO_FILE):
        msg = "Silencio prolongado detectado en el stream."
        log(f"🔇 {msg}")
        enviar_alerta("⚠️ ALERTA: Silencio detectado", msg)
    else:
        log("🎵 Stream funcionando correctamente")

    if os.path.exists(TEMP_AUDIO_FILE):
        os.remove(TEMP_AUDIO_FILE)

    if es_hora_de_resumen():
        enviar_resumen_telegram()

if __name__ == "__main__":
    monitorear()
