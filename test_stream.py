# -*- coding: utf-8 -*-
"""
Test Suite para Radio Watchdog
Incluye pruebas de funcionalidad del stream y codificación UTF-8
"""

import os
from datetime import datetime
from monitoreo import bajar_fragmento, analizar_audio, enviar_alerta, TEMP_AUDIO_FILE, TEMP_AUDIO_FILE2, STREAM_URL, STREAM2_URL

def test_manual_stream():
    print("\n=== Test Manual de Streams ===\n")
    print("Iniciando prueba...")
    
    resultados = []
    
    # Probar Stream Principal
    print("📡 Descargando fragmento del Stream Principal...")
    if not bajar_fragmento(STREAM_URL, TEMP_AUDIO_FILE):
        mensaje = "❌ ERROR: No se pudo descargar el Stream Principal"
        print(mensaje)
        resultados.append(("Stream Principal", False, mensaje))
    else:
        print("🔍 Analizando audio del Stream Principal...")
        tiene_audio = analizar_audio(TEMP_AUDIO_FILE)
        if tiene_audio:
            estado = "✅ CORRECTO: Stream Principal funcionando correctamente"
            resultados.append(("Stream Principal", True, estado))
        else:
            estado = "⚠️ ALERTA: Se detectó silencio en el Stream Principal"
            resultados.append(("Stream Principal", False, estado))
        print(f"   {estado}")
    
    # Probar Stream Secundario (si está configurado)
    if STREAM2_URL:
        print("\n📻 Descargando fragmento del Stream Secundario...")
        if not bajar_fragmento(STREAM2_URL, TEMP_AUDIO_FILE2):
            mensaje = "❌ ERROR: No se pudo descargar el Stream Secundario"
            print(mensaje)
            resultados.append(("Stream Secundario", False, mensaje))
        else:
            print("🔍 Analizando audio del Stream Secundario...")
            tiene_audio2 = analizar_audio(TEMP_AUDIO_FILE2)
            if tiene_audio2:
                estado = "✅ CORRECTO: Stream Secundario funcionando correctamente"
                resultados.append(("Stream Secundario", True, estado))
            else:
                estado = "⚠️ ALERTA: Se detectó silencio en el Stream Secundario"
                resultados.append(("Stream Secundario", False, estado))
            print(f"   {estado}")
    else:
        print("\n📻 Stream Secundario: No configurado")
        resultados.append(("Stream Secundario", None, "No configurado"))
    
    # Preparar mensaje completo
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mensaje = f"Test Manual de Streams\n\nFecha: {timestamp}\n\nResultados:\n"
    
    for stream, estado, detalle in resultados:
        if estado is None:
            mensaje += f"📋 {stream}: {detalle}\n"
        elif estado:
            mensaje += f"✅ {stream}: {detalle}\n"
        else:
            mensaje += f"❌ {stream}: {detalle}\n"
    
    mensaje += "\nEsta es una prueba manual del sistema de monitoreo."
    
    # Enviar notificaciones
    print("\nEnviando notificaciones...")
    enviar_alerta("[TEST MANUAL] Resultado de Prueba de Streams", mensaje)
    
    # Limpiar archivos temporales
    for temp_file in [TEMP_AUDIO_FILE, TEMP_AUDIO_FILE2]:
        if os.path.exists(temp_file):
            os.remove(temp_file)
    
    # Mostrar resumen
    print(f"\n📊 RESUMEN DE PRUEBAS:")
    for stream, estado, detalle in resultados:
        if estado is None:
            print(f"   {stream}: ⚪ {detalle}")
        elif estado:
            print(f"   {stream}: ✅ OK")
        else:
            print(f"   {stream}: ❌ FALLO")
    
    print("\nPrueba completada.\n")
    return all(r[1] for r in resultados if r[1] is not None)

def test_codificacion():
    """Prueba específica para verificar que la codificación UTF-8 funciona correctamente"""
    print("\n=== Test de Codificación UTF-8 ===\n")
    
    # Mensaje de prueba con caracteres especiales
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mensaje_test = f"""Prueba de Codificación UTF-8

Fecha: {timestamp}
Caracteres especiales: ñ á é í ó ú ü Ñ
Símbolos: © ® ™ € £ ¥
Emojis: 🎵 📧 📲 ❌ ✅ ⚠️

Este mensaje verifica que el sistema puede enviar caracteres especiales correctamente por email y Telegram."""

    print("Enviando mensaje de prueba con caracteres especiales...")
    try:
        enviar_alerta("[TEST UTF-8] Prueba de Codificación", mensaje_test)
        print("✅ Prueba de codificación completada - revisar email y Telegram")
        return True
    except Exception as e:
        print(f"❌ Error en prueba de codificación: {e}")
        return False

def menu_principal():
    """Menú interactivo para seleccionar diferentes tipos de prueba"""
    while True:
        print("\n" + "="*50)
        print("🔧 RADIO WATCHDOG - MENU DE PRUEBAS")
        print("="*50)
        print("1. 📻 Test completo de ambos streams")
        print("2. 🔤 Test de codificación UTF-8")
        print("3. 🚀 Ejecutar ambas pruebas")
        print("0. ❌ Salir")
        print("-"*50)
        
        opcion = input("Selecciona una opción (0-3): ").strip()
        
        if opcion == "1":
            test_manual_stream()
        elif opcion == "2":
            test_codificacion()
        elif opcion == "3":
            print("\n🚀 Ejecutando todas las pruebas...\n")
            resultado_stream = test_manual_stream()
            resultado_utf8 = test_codificacion()
            print(f"\n📊 RESUMEN DE PRUEBAS:")
            print(f"   Streams: {'✅ OK' if resultado_stream else '❌ FALLO'}")
            print(f"   UTF-8:   {'✅ OK' if resultado_utf8 else '❌ FALLO'}")
        elif opcion == "0":
            print("\n👋 ¡Hasta luego!")
            break
        else:
            print("\n❌ Opción no válida. Por favor, selecciona 0-3.")

if __name__ == "__main__":
    menu_principal()