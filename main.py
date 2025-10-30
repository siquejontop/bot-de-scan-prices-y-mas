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
# Configuración Inicial
# ============================================================
def setup_environment():
    load_dotenv()
    token = os.getenv("TOKEN")
    if not token:
        raise ValueError("No se encontró el TOKEN en el archivo .env")
    return token

# ============================================================
# Logging
# ============================================================
def configure_logging():
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
    return logger

# ============================================================
# Flask Keep-Alive
# ============================================================
app = Flask("keep_alive")
@app.route("/")
def home():
    return "Bot is alive"

def run_flask_server():
    server_thread = threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=10000, use_reloader=False),
        daemon=True,
    )
    server_thread.start()
    logger.info("Servidor Flask iniciado en puerto 10000")

# ============================================================
# BOT + INTENTS (CORREGIDOS)
# ============================================================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.messages = True  # Necesario para comandos

bot = commands.Bot(command_prefix=",", intents=intents, help_command=None)  # help_command=None evita errores

# ============================================================
# COMANDO DE PRUEBA (para verificar embeds)
# ============================================================
@bot.command()
async def test(ctx):
    embed = discord.Embed(
        title="PRUEBA DE EMBED",
        description="Si ves el GIF, **todo funciona**.",
        color=discord.Color.green()
    )
    embed.set_image(url="https://media1.tenor.com/m/kmxEaVuW8AoAAAAC/kiss-gentle-kiss.gif")
    await ctx.send(embed=embed)

# ============================================================
# Eventos
# ============================================================
@bot.event
async def on_ready():
    banner = pyfiglet.figlet_format("SIQUEJ BOT", font="slant")
    print(f"\n{banner}")
    logger.info(f"Bot conectado como {bot.user} (ID: {bot.user.id})")
    await bot.change_presence(activity=discord.Game("online"))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Ese comando no existe.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("No tienes permisos.")
    else:
        logger.error(f"Error: {error}")
        await ctx.send("Ocurrió un error.")

# ============================================================
# Carga de Cogs
# ============================================================
async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and not filename.startswith("_"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                logger.info(f"Cog cargado: cogs.{filename[:-3]}")
            except Exception as e:
                logger.error(f"Error cargando cog {filename}: {e}")

# ============================================================
# Cierre
# ============================================================
async def shutdown_bot():
    logger.info("Apagando bot...")
    await bot.close()

def setup_signal_handlers(loop):
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown_bot()))

# ============================================================
# Main
# ============================================================
async def main():
    try:
        async with bot:
            await load_cogs()
            await bot.start(TOKEN)
    except Exception as e:
        logger.error(f"Error iniciando bot: {e}")
        sys.exit(1)

# ============================================================
# EJECUCIÓN
# ============================================================
if __name__ == "__main__":
    TOKEN = setup_environment()
    logger = configure_logging()
    run_flask_server()
    loop = asyncio.get_event_loop()
    setup_signal_handlers(loop)
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(shutdown_bot())
        loop.close()
