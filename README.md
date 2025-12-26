# Autolector - Transcripción Multimedia en Tiempo Real

**Autolector** es una aplicación moderna y potente diseñada para convertir el audio de tus archivos multimedia (MP3, MP4, WAV, etc.) en texto de manera sincronizada y en tiempo real. Utilizando **faster-whisper** y **Server-Sent Events (SSE)**, ofrece una experiencia de lectura tipo "Karaoke", ideal para audiolibros y transcripciones rápidas.

## Características Principales

- **Velocidad Optimizada**: Basado en `faster-whisper` (CTranslate2), es hasta 4 veces más rápido que la implementación estándar de OpenAI.
- **Streaming en Vivo**: No esperes a que termine el archivo. El texto aparece en pantalla segundo a segundo a medida que se procesa.
- **Modo Autolector (Karaoke)**: Resaltado de texto sincronizado con el reproductor de audio. Lee y escucha al mismo tiempo sin perderte.
- **Interfaz Premium**: Diseño oscuro ("Deep Blue") optimizado para la lectura prolongada, con transiciones fluidas y estilo moderno.
- **Carga en Memoria**: El modelo se carga una sola vez al iniciar el servidor, eliminando tiempos de espera en transcripciones sucesivas.
- **Soporte de Hardware**: Detección automática de GPU (CUDA) con caída automática a CPU (int8) para máxima compatibilidad.

## Requisitos Previos

- **Python 3.10+**
- **FFmpeg**: Necesario para el procesamiento de audio y extracción de video.
  - Comprobar con: `ffmpeg -version`
- **NVIDIA GPU (Opcional)**: Para aceleración por hardware (requiere drivers de CUDA instalados).

## Instalación

1. **Clona el repositorio**:
   ```bash
   git clone https://github.com/0utKast/Autolector-STT.git
   cd Autolector-STT
   ```

2. **Crea un entorno virtual**:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Instala las dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

## Uso

1. **Inicia el servidor**:
   ```bash
   python app.py
   ```
   El servidor se abrirá en `http://127.0.0.1:5000`.

2. **Carga tu archivo**:
   Selecciona un MP4 o MP3 y pulsa "Comenzar Lectura". El reproductor se activará automáticamente y el texto aparecerá en tiempo real.

## Stack Tecnológico

- **Backend**: Python 3, Flask.
- **Motor de IA**: [faster-whisper](https://github.com/SYSTRAN/faster-whisper).
- **Comunicación**: Server-Sent Events (SSE) para el streaming de segmentos.
- **Frontend**: HTML5, Vanilla CSS (Custom Properties), JavaScript (Async/Await).

## Estructura del Proyecto

```
.
├── app.py              # Servidor Flask con streaming SSE y carga de modelo.
├── requirements.txt    # Dependencias (faster-whisper, torch, flask).
├── static/
│   └── style.css       # Diseño Premium Dark Mode.
├── templates/
│   └── index.html      # Interfaz de usuario y lógica de sincronización.
├── uploads/            # Archivos temporales de procesamiento.
└── README.md           # Esta documentación.
```

## Licencia

Este proyecto está bajo la Licencia MIT.
