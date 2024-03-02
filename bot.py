from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import sqlite3
import requests
import re
import fcntl
import os
import sys


# Obtener el directorio actual del script
current_directory = os.path.dirname(os.path.abspath(__file__))
lockfile_path = os.path.join(current_directory, "bot.lock")

# Tratar de adquirir el bloqueo de archivo
try:
    lockfile = open(lockfile_path, "w")
    fcntl.lockf(lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
except IOError:
    # Si no se puede adquirir el bloqueo, significa que otra instancia del bot ya está en ejecución.
    print("Otra instancia del bot ya está en ejecución.")
    sys.exit(1)
    

# Conexión a la base de datos SQLite
conn = sqlite3.connect('usuarios.db')
cursor = conn.cursor()

# Crear tabla de usuarios si no existe
cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                first_name TEXT,
                registered BOOLEAN)''')
conn.commit()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Función para el comando /start."""
    # Mensaje de bienvenida al bot
    message = (
        "¡Hola {}!\n\n"
        "Bienvenido al bot de CodexPE.\n\n"
        "Para registrarte, utiliza el comando /me.\n"
        "Para ver la lista de comandos disponibles, utiliza el comando /cmds."
    ).format(update.effective_user.first_name)
    await update.message.reply_text(message)


async def me(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Función para el comando /me."""
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name

    if not verificar_registro(user_id):
        registrar_usuario(user_id, first_name)
        message = f"{first_name}, has sido registrado exitosamente."
    else:
        message = f"Hola, {first_name}, Ya estás registrado."

    await update.message.reply_text(message)


def registrar_usuario(user_id, first_name):
    """Registra a un usuario en la base de datos."""
    cursor.execute(
        "INSERT INTO usuarios (user_id, first_name, registered) VALUES (?, ?, 1)", (user_id, first_name))
    conn.commit()


def verificar_registro(user_id):
    """Verifica si un usuario está registrado."""
    cursor.execute("SELECT * FROM usuarios WHERE user_id=?", (user_id,))
    usuario = cursor.fetchone()
    return usuario is not None


async def cmds(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Función para el comando /cmds."""
    # Lista de comandos disponibles
    commands_list = (
        "/start - Iniciar el bot\n"
        "/me - Registrarse\n"
        "/cmds - Ver lista de comandos\n"
        "/dni 12345678 \n"
        "/ruc 10/20 \n"
        "/cmds - Ver lista de comandos\n"

    )
    await update.message.reply_text("Lista de comandos disponibles:\n\n" + commands_list)


async def dni(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Función para el comando /dni."""
    # Obtener el argumento del mensaje
    dni = context.args[0] if context.args else None
    first_name = update.effective_user.first_name
    user_id = update.effective_user.id

    if not verificar_registro(user_id):
        await update.message.reply_text("Por favor ingresa el comando /me para reguistarce")
    else:
        if dni is None or not re.match(r'^\d{8}$', dni):
            await update.message.reply_text("Por favor ingresa un DNI válido de 8 dígitos.")
        else:
            # Consulta a la API para obtener la información del DNI
            url = 'https://apiperu.dev/api/dni'
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                # Reemplazar TU_TOKEN con tu token de acceso
                'Authorization': 'Bearer 1924f8d50d2981a8af16013036a34303dbceee77b0914a3c1f1d598b0a4d135c'
            }
            data = {'dni': dni}
            response = requests.post(url, headers=headers, json=data)

            # Procesar la respuesta de la API
            if response.status_code == 200:
                persona = response.json().get('data', {})
                first_name = update.effective_user.first_name

                if persona:
                    # Construir el mensaje con la información obtenida
                    message = (
                        f"[Desarrollador](https://t.me/CodexPE) - [Codex Bot]\n\n"
                        f"Información del DNI *{dni}*:\n"
                        f"Nombres Completos: *{persona.get('nombre_completo', '')}*\n"
                        f"Nombres: *{persona.get('nombres', '')}*\n"
                        f"Apellido paterno: *{persona.get('apellido_paterno', '')}*\n"
                        f"Apellido materno: *{persona.get('apellido_materno', '')}*\n"
                        f"Codigo de verificaion: *{persona.get('codigo_verificacion', '')}*\n\n"
                        f"By: {first_name}"
                    )
                    print(message)
                else:
                    message = "No se encontraron datos para el DNI proporcionado."
            else:
                message = "Hubo un error al obtener la información del DNI. Por favor, intenta nuevamente más tarde."
            await update.message.reply_text(message, parse_mode='Markdown')


async def ruc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Función para el comando /ruc."""
    # Obtener el argumento del mensaje
    ruc_number = context.args[0] if context.args else None
    first_name = update.effective_user.first_name
    user_id = update.effective_user.id

    if not verificar_registro(user_id):
        await update.message.reply_text("Por favor ingresa el comando /me para reguistarce")
    else:
        if ruc_number is None or not re.match(r'^\d{11}$', ruc_number):
            await update.message.reply_text("Por favor ingresa un RUC válido.")
        else:
            # Consulta a la API para obtener la información del RUC
            url = f"https://api.apis.net.pe/v1/ruc?numero={ruc_number}"
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                # Reemplazar TU_TOKEN con tu token de acceso
                'Authorization': 'Bearer apis-token-1.aTSI1U7KEuT-6bbbCguH-4Y8TI6KS73N'
            }
            response = requests.get(url, headers=headers, verify=False)

            # Procesar la respuesta de la API
            if response.status_code == 200:
                persona = response.json()
                if persona:
                    # Construir el mensaje con la información obtenida
                    message = (
                        f"[Desarrollador](https://t.me/CodexPE) - [Codex Bot]\n\n"
                        f"*Información del RUC {ruc_number}:*\n"
                        f"Nombres Completos: * {persona.get('nombre', '')}*\n"
                        f"Estado: *{persona.get('estado', '')}*\n"
                        f"Condicion: *{persona.get('condicion', '')}*\n"
                        f"Direccion: *{persona.get('direccion', '')}*\n"
                        f"Direccion: *{persona.get('direccion', '')} - ({persona.get('viaNombre', '')})*\n"
                        f"Distrito: *{persona.get('distrito', '')}*\n"
                        f"Provincia: *{persona.get('provincia', '')}*\n"
                        f"Departamento: *{persona.get('departamento', '')}*\n"
                        f"Ubigeo: *{persona.get('ubigeo', '')}*\n\n"
                        f"By: {first_name}"

                    )
                else:
                    message = "No se encontraron datos para el RUC proporcionado."
            else:
                message = "Hubo un error al obtener la información del RUC. Por favor, intenta nuevamente más tarde."

            await update.message.reply_text(message, parse_mode='Markdown')


app = ApplicationBuilder().token(
    "7080590731:AAHbuMhLFzfei7xB8jSGg5_bj1oEX7GHZmI").build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("me", me))
app.add_handler(CommandHandler("cmds", cmds))
app.add_handler(CommandHandler("dni", dni))
app.add_handler(CommandHandler("ruc", ruc))


app.run_polling()
