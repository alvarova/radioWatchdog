# 📻 Radio Watchdog - Sistema de Monitoreo de Stream

Sistema automatizado de monitoreo para streams de radio que detecta caídas de transmisión y silencios prolongados, enviando alertas por email y Telegram.

## 🚀 Características

- **Monitoreo 24/7** del stream de radio
- **Detección inteligente de silencio** con umbral configurable
- **Modo nocturno** (00:00-05:00) que omite detección de silencio
- **Alertas duales**: Email + Telegram
- **Resúmenes automáticos** cada 6 horas
- **Logging detallado** con rotación automática
- **Limpieza automática** de logs antiguos (>30 días)

## 📋 Requisitos

### Software necesario:
- **Python 3.7+**
- **FFmpeg** (para procesamiento de audio)

### Dependencias Python:
```
requests
python-dotenv
pydub
```

## 🔧 Instalación

1. **Clonar o descargar el proyecto**
   ```bash
   git clone <url-del-repositorio>
   cd radioWatchdog
   ```

2. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

3. **Instalar FFmpeg**
   - **Windows**: Descargar desde [ffmpeg.org](https://ffmpeg.org/download.html) y agregar al PATH
   - **Linux**: `sudo apt install ffmpeg`
   - **macOS**: `brew install ffmpeg`

4. **Configurar variables de entorno** (ver sección siguiente)

## ⚙️ Configuración del archivo .env

Crear un archivo `.env` en la raíz del proyecto con las siguientes variables:

```env
# === CONFIGURACIÓN SMTP (Email) ===
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu-email@gmail.com
SMTP_PASS=tu-contraseña-de-aplicacion
EMAIL_FROM=tu-email@gmail.com
EMAIL_TO=destino@ejemplo.com

# === CONFIGURACIÓN TELEGRAM ===
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789

# === CONFIGURACIÓN DEL STREAM ===
STREAM_URL=http://ejemplo.com:8000/radio.mp3
THRESHOLD_DBFS=-35
```

### 📧 Configuración de Email (Gmail)

1. **Habilitar verificación en 2 pasos** en tu cuenta de Gmail
2. **Generar contraseña de aplicación**:
   - Ir a Configuración de Google → Seguridad
   - Seleccionar "Contraseñas de aplicaciones"
   - Generar una nueva contraseña para "Correo"
3. **Usar la contraseña generada** en `SMTP_PASS`

### 🤖 Configuración de Telegram

1. **Crear un bot**:
   - Hablar con [@BotFather](https://t.me/botfather) en Telegram
   - Enviar `/newbot` y seguir instrucciones
   - Guardar el **token** proporcionado

2. **Obtener Chat ID**:
   - Enviar un mensaje a tu bot
   - Visitar: `https://api.telegram.org/bot<TU_TOKEN>/getUpdates`
   - Buscar el `chat.id` en la respuesta JSON

### 🎵 Configuración del Stream

- **STREAM_URL**: URL completa del stream de radio
- **THRESHOLD_DBFS**: Umbral de silencio en decibelios (valores más negativos = más sensible)
  - `-20`: Muy sensible (detecta susurros)
  - `-35`: Sensibilidad media (recomendado)
  - `-50`: Menos sensible (solo detecta silencio total)

## 🚀 Ejecución

### Ejecución manual:
```bash
python monitoreo.py
```

### Ejecución como servicio (Windows):
1. **Descargar NSSM** (Non-Sucking Service Manager)
2. **Instalar como servicio**:
   ```cmd
   nssm install RadioWatchdog "C:\path\to\python.exe" "C:\path\to\monitoreo.py"
   nssm set RadioWatchdog AppDirectory "C:\path\to\radioWatchdog"
   nssm start RadioWatchdog
   ```

### Ejecución programada (Linux/macOS):
Agregar al crontab para ejecutar cada 5 minutos:
```bash
crontab -e
# Agregar línea:
*/5 * * * * /usr/bin/python3 /path/to/monitoreo.py
```

## 📊 Funcionamiento

### Proceso de monitoreo:
1. **Descarga** 10 segundos del stream usando FFmpeg
2. **Analiza** el audio buscando contenido no silencioso
3. **Evalúa** si al menos 10% del tiempo tiene audio válido
4. **Registra** el resultado en logs diarios
5. **Envía alertas** solo cuando detecta problemas

### Modo nocturno (00:00 - 05:00):
- ✅ Sigue verificando conectividad del stream
- ❌ Omite detección de silencio
- 📝 Registra estado especial en logs

### Resúmenes automáticos:
- **Horarios**: 06:00 AM y 06:00 PM
- **Contenido**: Estadísticas de las últimas 6 horas
- **Envío**: Solo por Telegram

## 📁 Estructura de archivos

```
radioWatchdog/
├── monitoreo.py          # Script principal
├── requirements.txt      # Dependencias Python
├── .env                 # Variables de entorno (crear)
├── .gitignore          # Archivos a ignorar en Git
├── logs/               # Logs diarios (se crea automáticamente)
│   ├── log_2025-07-08.log
│   └── ...
└── temp_stream.mp3     # Archivo temporal (se elimina automáticamente)
```

## 📋 Logs

### Ubicación:
- **Directorio**: `logs/`
- **Formato**: `log_YYYY-MM-DD.log`
- **Retención**: 30 días (limpieza automática)

### Tipos de mensajes:
- `🎵` Stream funcionando correctamente
- `🌙` Modo nocturno activo
- `❌` Error de conectividad
- `🔇` Silencio detectado
- `📧` Email enviado
- `📲` Mensaje de Telegram enviado
- `🧹` Log antiguo eliminado

## 🚨 Tipos de alertas

### 🛑 Stream caído:
- **Trigger**: No se puede conectar al stream
- **Envío**: Email + Telegram
- **Frecuencia**: Cada vez que ocurre

### ⚠️ Silencio detectado:
- **Trigger**: Menos del 10% del audio tiene contenido
- **Envío**: Email + Telegram
- **Excepción**: No se envía en horario nocturno (00:00-05:00)

### ✅ Resúmenes:
- **Trigger**: Cada 6 horas (06:00 y 18:00)
- **Envío**: Solo Telegram
- **Contenido**: Estadísticas del período

## 🔧 Troubleshooting

### Problema: No recibo emails
**Solución**: 
- Verificar credenciales SMTP en `.env`
- Usar contraseña de aplicación (no la contraseña normal)
- Revisar logs para errores específicos

### Problema: No recibo mensajes de Telegram
**Solución**:
- Verificar token del bot y chat ID
- Enviar un mensaje al bot primero
- Verificar que el bot no esté bloqueado

### Problema: FFmpeg no encontrado
**Solución**:
- Instalar FFmpeg en el sistema
- Agregar FFmpeg al PATH del sistema
- En Windows, reiniciar después de modificar PATH

### Problema: Muchas falsas alarmas
**Solución**:
- Ajustar `THRESHOLD_DBFS` a un valor más negativo
- Verificar que el horario nocturno esté bien configurado
- Revisar la calidad del stream de origen

## 📄 Licencia

Este proyecto es de código abierto. Puedes usarlo y modificarlo según tus necesidades.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Fork del proyecto
2. Crear una rama para tu feature
3. Commit de tus cambios
4. Push a la rama
5. Crear un Pull Request

---

**💡 Tip**: Para un monitoreo más frecuente, programa la ejecución cada 2-3 minutos. Para uso básico, cada 5-10 minutos es suficiente.
