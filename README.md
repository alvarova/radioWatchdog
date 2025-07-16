# 📻 Radio Watchdog - Sistema de Monitoreo de Stream

Sistema automatizado de monitoreo para streams de radio que detecta caídas de transmisión y silencios prolongados, enviando alertas por email y Telegram.

## 🚀 Características

- **Monitoreo 24/7** de múltiples streams de radio
- **Monitoreo dual**: Stream principal + stream secundario (opcional)
- **Detección inteligente de silencio** con umbral configurable
- **Modo nocturno** (00:00-05:00) que omite detección de silencio
- **Alertas duales**: Email + Telegram
- **Resúmenes automáticos** cada 6 horas con estadísticas por stream
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

# === CONFIGURACIÓN DE STREAMS ===
STREAM_URL=http://ejemplo.com:8000/radio.mp3
STREAM2_URL=http://ejemplo2.com:8000/radio2.mp3
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

### 🎵 Configuración de Streams

- **STREAM_URL**: URL completa del stream principal de radio
- **STREAM2_URL**: URL del stream secundario (opcional - dejar vacío si no se usa)
- **THRESHOLD_DBFS**: Umbral de silencio en decibelios (valores más negativos = más sensible)
  - `-20`: Muy sensible (detecta susurros)
  - `-35`: Sensibilidad media (recomendado)
  - `-50`: Menos sensible (solo detecta silencio total)

### 📡 Configuración de múltiples streams:

El sistema puede monitorear hasta 2 streams simultáneamente:

**Solo stream principal:**
```env
STREAM_URL=http://radio.ejemplo.com:8000/stream.mp3
# STREAM2_URL= (dejar vacío o comentado)
```

**Ambos streams:**
```env
STREAM_URL=http://radio-principal.com:8000/stream.mp3
STREAM2_URL=http://radio-backup.com:8000/stream.mp3
```

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
1. **Descarga** 10 segundos de cada stream usando FFmpeg
2. **Analiza** el audio buscando contenido no silencioso
3. **Evalúa** si al menos 10% del tiempo tiene audio válido
4. **Registra** el resultado en logs diarios (distinguiendo entre streams)
5. **Envía alertas** consolidadas cuando detecta problemas en cualquier stream

### Modo nocturno (00:00 - 05:00):
- ✅ Sigue verificando conectividad de ambos streams
- ❌ Omite detección de silencio en ambos streams
- 📝 Registra estado especial en logs para cada stream

### Resúmenes automáticos:
- **Horarios**: 06:00-06:15 AM y 18:00-18:15 PM (ventana de 16 minutos)
- **Contenido**: Estadísticas separadas por stream de las últimas 6 horas
- **Envío**: Solo por Telegram
- **Formato**: Muestra estado independiente de cada stream configurado

## 📁 Estructura de archivos

```
radioWatchdog/
├── monitoreo.py          # Script principal
├── test_stream.py        # Suite de pruebas para streams
├── requirements.txt      # Dependencias Python
├── .env                 # Variables de entorno (crear)
├── .gitignore          # Archivos a ignorar en Git
├── README.md           # Esta documentación
├── logs/               # Logs diarios (se crea automáticamente)
│   ├── log_2025-07-15.log
│   └── ...
├── temp_stream.mp3     # Archivo temporal stream principal
└── temp_stream2.mp3    # Archivo temporal stream secundario
```

## 📋 Logs

### Ubicación:
- **Directorio**: `logs/`
- **Formato**: `log_YYYY-MM-DD.log`
- **Retención**: 30 días (limpieza automática)

### Tipos de mensajes:
- `🎵` Stream funcionando correctamente (con identificación del stream)
- `🌙` Modo nocturno activo
- `❌` Error de conectividad (especifica qué stream)
- `🔇` Silencio detectado (especifica qué stream)
- `📧` Email enviado
- `📲` Mensaje de Telegram enviado
- `🧹` Log antiguo eliminado
- `📊` Generación de resumen iniciada
- `📋` Resumen enviado con estadísticas

## 🚨 Tipos de alertas

### 🛑 Stream caído:
- **Trigger**: No se puede conectar a cualquiera de los streams
- **Envío**: Email + Telegram
- **Frecuencia**: Cada vez que ocurre
- **Detalle**: Especifica qué stream(s) están afectados

### ⚠️ Silencio detectado:
- **Trigger**: Menos del 10% del audio tiene contenido en cualquier stream
- **Envío**: Email + Telegram
- **Excepción**: No se envía en horario nocturno (00:00-05:00)
- **Detalle**: Especifica en qué stream se detectó el silencio

### ✅ Resúmenes:
- **Trigger**: Cada 6 horas (06:00-06:15 y 18:00-18:15)
- **Envío**: Solo Telegram
- **Contenido**: Estadísticas separadas por stream del período
- **Formato**: 
  ```
  🌅 Mañana - Resumen últimas 6hs:
  
  📡 Stream Principal: ✅ Todo OK (36 chequeos)
  📻 Stream Secundario: ✅ 30 OK | ❌ 6 errores
     🕐 Primer error: 14:23
  ```

## 🧪 Pruebas del Sistema

Para verificar el funcionamiento del sistema, ejecuta:

```bash
python test_stream.py
```

**Menú de pruebas disponibles:**
1. **Test completo de ambos streams**: Verifica conectividad y análisis de audio
2. **Test de codificación UTF-8**: Prueba el envío de caracteres especiales
3. **Ejecutar ambas pruebas**: Combinación completa con reporte de resultados

**Ejemplo de salida:**
```
📊 RESUMEN DE PRUEBAS:
   Stream Principal: ✅ OK
   Stream Secundario: ✅ OK  
   UTF-8: ✅ OK
```

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
- Considerar si ambos streams tienen el mismo comportamiento

### Problema: No detecta uno de los streams
**Solución**:
- Verificar que `STREAM2_URL` esté correctamente configurado en `.env`
- Probar las URLs manualmente en un navegador
- Revisar logs para errores específicos de cada stream
- Ejecutar `python test_stream.py` para diagnóstico individual

### Problema: Resúmenes no llegan en horario
**Solución**:
- Verificar que el sistema se ejecute dentro de la ventana 06:00-06:15 y 18:00-18:15
- Revisar logs para confirmar generación de resúmenes
- Verificar configuración de Telegram

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

**🔄 Novedades v2.0**: Soporte para monitoreo dual de streams, resúmenes mejorados con estadísticas por stream, y sistema de pruebas integrado.
