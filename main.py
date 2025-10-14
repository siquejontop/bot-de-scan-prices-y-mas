import discord
from discord.ext import commands
import os
import asyncio
import logging
import colorlog
import pyfiglet
from dotenv import load_dotenv
from flask import Flask
import threading
import signal
import sys

# ============================================================
# 🔧 CONFIGURACIÓN INICIAL
# ============================================================
load_dotenv()
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("No se encontró el TOKEN en el archivo .env")

# Configuración de logs
logger = logging.getLogger("discord_bot")
logger.setLevel(logging.INFO)
handler = colorlog.StreamHandler()
handler.setFormatter(
    colorlog.ColoredFormatter(
        "%(log_color)s[%(asctime)s] [%(levelname)-8s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
    )
)
logger.addHandler(handler)

# ============================================================
# 🌐 SERVIDOR FLASK (KEEP ALIVE)
# ============================================================
app = Flask("keep_alive")
@app.route("/")
def home():
    return "✅ Bot is alive"

def keep_alive():
    server_thread = threading.Thread(target=lambda: app.run(host="0.0.0.0", port=10000, use_reloader=False), daemon=True)
    server_thread.start()
    logger.info("🚀 Servidor Flask iniciado en puerto 10000")

# ============================================================
# 🤖 CONFIGURACIÓN DEL BOT
# ============================================================
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ============================================================
# ⚙️ EVENTOS
# ============================================================
@bot.event
async def on_ready():
    banner = pyfiglet.figlet_format("SIQUEJ BOT", font="slant")
    print(f"\n{banner}")
    logger.info(f"✅ Bot conectado como {bot.user} (ID: {bot.user.id})")
    await bot.change_presence(activity=discord.Game("online 💻"))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Ese comando no existe.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ No tienes permisos para usar este comando.")
    else:
        logger.error(f"⚠️ Error ejecutando comando: {error}")
        await ctx.send("⚠️ Ocurrió un error al ejecutar el comando.")

# ============================================================
# 📦 CARGA DE COGS (módulos)
# ============================================================
async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and not filename.startswith("_"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                logger.info(f"✅ Cog cargado: cogs.{filename[:-3]}")
            except Exception as e:
                logger.error(f"❌ Error cargando cogs.{filename[:-3]}: {e}")

# ============================================================
# 🚀 INICIO DEL BOT
# ============================================================
async def main():
    try:
        async with bot:
            await load_cogs()
            await bot.start(TOKEN)
    except Exception as e:
        logger.error(f"❌ Error iniciando el bot: {e}")
        sys.exit(1)

# ============================================================
# 🔹 MANEJO DE CIERRE
# ============================================================
def handle_shutdown(signum, frame):
    logger.info("🛑 Recibida señal de cierre, apagando...")
    asyncio.run(bot.close())
    sys.exit(0)

signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

# ============================================================
# 🔹 KEEP ALIVE + ARRANQUE
# ============================================================
if __name__ == "__main__":
    keep_alive()
    asyncio.run(main())
