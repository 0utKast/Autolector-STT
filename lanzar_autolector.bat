@echo off
setlocal
cd /d "%~dp0"

echo Iniciando Autolector...

:: Verificar si el entorno virtual existe
if not exist "venv\Scripts\activate" (
    echo Creando entorno virtual...
    python -m venv venv
)

:: Activar entorno virtual
call venv\Scripts\activate

:: Instalar/Actualizar dependencias
echo Verificando dependencias...
pip install -r requirements.txt

:: Iniciar la aplicación
echo Abriendo Autolector en http://127.0.0.1:5000
start http://127.0.0.1:5000
python app.py

pause
