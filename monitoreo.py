
# -*- coding: utf-8 -*-
"""
Radio Watchdog - Sistema de Monitoreo de Stream
Monitorea streams de radio 24/7 y envía alertas por email y Telegram
"""

import os
import smtplib
import requests
import logging
import glob
from datetime import datetime, timedelta
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from pydub import AudioSegment
from pydub.silence import detect_nonsilent


# Inicialización
load_dotenv()

# Configuración desde .env
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TO = os.getenv("EMAIL_TO")
STREAM_URL = os.getenv("STREAM_URL")
STREAM2_URL = os.getenv("STREAM2_URL")  # Segundo stream opcional
THRESHOLD_DBFS = int(os.getenv("THRESHOLD_DBFS", -35))
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Paths
HOY = datetime.now().strftime('%Y-%m-%d')
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, f"log_{HOY}.log")
TEMP_AUDIO_FILE = "temp_stream.mp3"
TEMP_AUDIO_FILE2 = "temp_stream2.mp3"

# Asegurar carpeta logs
os.makedirs(LOG_DIR, exist_ok=True)

# Configurar logging
logging.basicConfig(filename=LOG_FILE, level=logging.INFO)

def log(msg):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mensaje = f"[{now}] {msg}"
    print(mensaje)
    logging.info(mensaje)

def enviar_alerta(asunto:str, cuerpo:str) -> None:
    try:
        print(f"Asunto: {asunto!r}")  # Depuración
        mensaje = MIMEMultipart()
        mensaje["From"] = EMAIL_FROM
        mensaje["To"] = EMAIL_TO
        mensaje["Subject"] = Header(asunto, "utf-8").encode()
        mensaje.attach(MIMEText(cuerpo, "plain", "utf-8"))

        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(mensaje)

        log(f"📧 Alerta enviada: {asunto}")
    except Exception as e:
        log(f"🚫 Error al enviar email: {e}")

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

def bajar_fragmento(stream_url, temp_file):
    """
    Descarga un fragmento de 10 segundos del stream especificado
    """
    cmd = f'ffmpeg -y -i "{stream_url}" -t 10 -acodec copy {temp_file} -loglevel error'
    return os.system(cmd) == 0 and os.path.exists(temp_file)

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
    """
    Verifica si es momento de enviar resumen.
    Horarios: 06:00-06:16 y 18:00-18:16
    """
    ahora = datetime.now()
    # Verificar si estamos en las horas correctas (6 AM o 6 PM)
    if ahora.hour not in [6, 18]:
        return False
    
    # Verificar ventana de tolerancia de 16 minutos (0-15 minutos)
    return 0 <= ahora.minute <= 15

def enviar_resumen_telegram():
    """
    Envía resumen de las últimas 6 horas por Telegram.
    Analiza logs y cuenta eventos OK vs errores para ambos streams.
    """
    ahora = datetime.now()
    desde = ahora - timedelta(hours=6)
    
    # Contadores para Stream Principal
    ok_count_principal = 0
    caidas_principal = []
    
    # Contadores para Stream Secundario
    ok_count_secundario = 0
    caidas_secundario = []
    
    log(f"📊 Generando resumen desde {desde.strftime('%H:%M')} hasta {ahora.strftime('%H:%M')}")

    try:
        for archivo in glob.glob(os.path.join(LOG_DIR, "log_*.log")):
            with open(archivo, "r", encoding="utf-8") as f:
                for linea in f:
                    try:
                        # Extraer timestamp de la línea
                        if "]" not in linea or "[" not in linea:
                            continue
                            
                        fecha_str = linea.split("]")[0].strip("[")
                        fecha = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
                        
                        # Solo procesar eventos dentro del rango de 6 horas
                        if fecha >= desde:
                            # Stream Principal
                            if ("🎵 Stream Principal funcionando correctamente" in linea or 
                                "Stream Principal funcionando correctamente (modo nocturno)" in linea):
                                ok_count_principal += 1
                            elif ("❌" in linea and "Stream Principal" in linea) or ("🔇" in linea and "Stream Principal" in linea):
                                caidas_principal.append(fecha.strftime("%H:%M"))
                            
                            # Stream Secundario (si existe)
                            elif ("🎵 Stream Secundario funcionando correctamente" in linea or 
                                  "Stream Secundario funcionando correctamente (modo nocturno)" in linea):
                                ok_count_secundario += 1
                            elif ("❌" in linea and "Stream Secundario" in linea) or ("🔇" in linea and "Stream Secundario" in linea):
                                caidas_secundario.append(fecha.strftime("%H:%M"))
                            
                            # Compatibilidad con logs antiguos (sin especificar stream)
                            elif ("🎵 Stream funcionando correctamente" in linea and 
                                  "Principal" not in linea and "Secundario" not in linea):
                                ok_count_principal += 1
                            elif (("❌" in linea or "🔇" in linea) and 
                                  "Principal" not in linea and "Secundario" not in linea):
                                caidas_principal.append(fecha.strftime("%H:%M"))
                                
                    except (ValueError, IndexError):
                        # Error al parsear fecha, continuar con siguiente línea
                        continue

        # Generar mensaje de resumen
        horario = "🌅 Mañana" if ahora.hour == 6 else "🌆 Tarde"
        
        mensaje = f"{horario} - Resumen últimas 6hs:\n\n"
        
        # Resumen Stream Principal
        if not caidas_principal:
            mensaje += f"📡 Stream Principal: ✅ Todo OK ({ok_count_principal} chequeos)\n"
        else:
            primer_error_principal = min(caidas_principal) if caidas_principal else "N/A"
            mensaje += f"📡 Stream Principal: ✅ {ok_count_principal} OK | ❌ {len(caidas_principal)} errores\n"
            mensaje += f"   🕐 Primer error: {primer_error_principal}\n"
        
        # Resumen Stream Secundario (solo si está configurado)
        if STREAM2_URL:
            if not caidas_secundario:
                mensaje += f"📻 Stream Secundario: ✅ Todo OK ({ok_count_secundario} chequeos)\n"
            else:
                primer_error_secundario = min(caidas_secundario) if caidas_secundario else "N/A"
                mensaje += f"📻 Stream Secundario: ✅ {ok_count_secundario} OK | ❌ {len(caidas_secundario)} errores\n"
                mensaje += f"   🕐 Primer error: {primer_error_secundario}\n"
        else:
            mensaje += "📻 Stream Secundario: No configurado\n"

        enviar_alerta_telegram(mensaje)
        log(f"📋 Resumen enviado: Principal({ok_count_principal} OK, {len(caidas_principal)} errores), "
            f"Secundario({ok_count_secundario} OK, {len(caidas_secundario)} errores)")
        
    except Exception as e:
        log(f"🚫 Error generando resumen: {e}")
        enviar_alerta_telegram(f"⚠️ Error al generar resumen de las últimas 6hs: {str(e)}")

def monitorear_stream(stream_url, temp_file, stream_nombre):
    """
    Monitorea un stream específico y retorna el resultado
    """
    if not bajar_fragmento(stream_url, temp_file):
        msg = f"No se pudo acceder al {stream_nombre}."
        log(f"❌ {msg}")
        return False, msg
    
    if not analizar_audio(temp_file):
        msg = f"Silencio prolongado detectado en el {stream_nombre}."
        log(f"🔇 {msg}")
        return False, msg
    else:
        log(f"🎵 {stream_nombre} funcionando correctamente")
        return True, None

def monitorear():
    log("⏱ Iniciando monitoreo...")
    limpiar_logs_viejos()
    
    # Verificar si estamos en horario nocturno (00:00 - 05:00)
    hora_actual = datetime.now().hour
    es_horario_nocturno = 0 <= hora_actual < 5
    
    # Lista para almacenar errores encontrados
    errores = []
    
    # Monitorear Stream Principal
    if not bajar_fragmento(STREAM_URL, TEMP_AUDIO_FILE):
        msg = "No se pudo acceder al Stream Principal."
        log(f"❌ {msg}")
        errores.append(f"🛑 Stream Principal caído: {msg}")
    elif es_horario_nocturno:
        log("🌙 Horario nocturno (00:00-05:00): omitiendo detección de silencio en Stream Principal")
        log("🎵 Stream Principal funcionando correctamente (modo nocturno)")
    elif not analizar_audio(TEMP_AUDIO_FILE):
        msg = "Silencio prolongado detectado en el Stream Principal."
        log(f"🔇 {msg}")
        errores.append(f"⚠️ Stream Principal con silencio: {msg}")
    else:
        log("🎵 Stream Principal funcionando correctamente")

    # Monitorear Stream Secundario (si está configurado)
    if STREAM2_URL:
        if not bajar_fragmento(STREAM2_URL, TEMP_AUDIO_FILE2):
            msg = "No se pudo acceder al Stream Secundario."
            log(f"❌ {msg}")
            errores.append(f"🛑 Stream Secundario caído: {msg}")
        elif es_horario_nocturno:
            log("🌙 Horario nocturno (00:00-05:00): omitiendo detección de silencio en Stream Secundario")
            log("🎵 Stream Secundario funcionando correctamente (modo nocturno)")
        elif not analizar_audio(TEMP_AUDIO_FILE2):
            msg = "Silencio prolongado detectado en el Stream Secundario."
            log(f"🔇 {msg}")
            errores.append(f"⚠️ Stream Secundario con silencio: {msg}")
        else:
            log("🎵 Stream Secundario funcionando correctamente")

    # Enviar alertas si hay errores
    if errores:
        asunto = "🚨 ALERTA: Problemas detectados en streams"
        cuerpo = "Se detectaron los siguientes problemas:\n\n" + "\n".join(errores)
        enviar_alerta(asunto, cuerpo)

    # Limpiar archivos temporales
    for temp_file in [TEMP_AUDIO_FILE, TEMP_AUDIO_FILE2]:
        if os.path.exists(temp_file):
            os.remove(temp_file)

    if es_hora_de_resumen():
        enviar_resumen_telegram()

if __name__ == "__main__":
    monitorear()
