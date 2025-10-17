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
# ✨ Configuración Inicial
# ============================================================
def setup_environment():
    """Load environment variables and validate required settings."""
    load_dotenv()
    token = os.getenv("TOKEN")
    if not token:
        raise ValueError("❌ No se encontró el TOKEN en el archivo .env")
    return token

# ============================================================
# 📜 Configuración de Logging
# ============================================================
def configure_logging():
    """Configure colored logging for the bot."""
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
# 🌐 Servidor Flask (Keep-Alive)
# ============================================================
app = Flask("keep_alive")

@app.route("/")
def home():
    """Endpoint to keep the bot alive."""
    return "✅ Bot is alive"

def run_flask_server():
    """Run Flask server in a separate thread for keep-alive."""
    server_thread = threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=10000, use_reloader=False),
        daemon=True,
    )
    server_thread.start()
    logger.info("🚀 Servidor Flask iniciado en puerto 10000")

# ============================================================
# 🤖 Configuración del Bot
# ============================================================
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ============================================================
# 🎉 Eventos del Bot
# ============================================================
@bot.event
async def on_ready():
    """Handle the bot's ready event."""
    banner = pyfiglet.figlet_format("SIQUEJ BOT", font="slant")
    print(f"\n{banner}")
    logger.info(f"✅ Bot conectado como {bot.user} (ID: {bot.user.id})")
    await bot.change_presence(activity=discord.Game("online 💻"))

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors gracefully."""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Ese comando no existe.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ No tienes permisos para usar este comando.")
    else:
        logger.error(f"⚠️ Error ejecutando comando: {error}")
        await ctx.send("⚠️ Ocurrió un error al ejecutar el comando.")

# ============================================================
# 📦 Carga de Cogs
# ============================================================
async def load_cogs():
    """Load all cogs from the cogs directory."""
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and not filename.startswith("_"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                logger.info(f"✅ Cog cargado: cogs.{filename[:-3]}")
            except Exception as e:
                logger.error(f"❌ Error cargando cogs.{filename[:-3]}: {e}")

# ============================================================
# 🛑 Manejo de Cierre
# ============================================================
async def shutdown_bot():
    """Gracefully shut down the bot."""
    logger.info("🛑 Recibida señal de cierre, apagando...")
    await bot.close()

def setup_signal_handlers(loop):
    """Configure signal handlers for graceful shutdown."""
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(
            sig,
            lambda: asyncio.create_task(shutdown_bot())
        )

# ============================================================
# 🚀 Arranque del Bot
# ============================================================
async def main():
    """Main function to start the bot and load cogs."""
    try:
        async with bot:
            await load_cogs()
            await bot.start(TOKEN)
    except Exception as e:
        logger.error(f"❌ Error iniciando el bot: {e}")
        sys.exit(1)

# ============================================================
# 🔧 Ejecución Principal
# ============================================================
if __name__ == "__main__":
    # Initialize environment and logging
    TOKEN = setup_environment()
    logger = configure_logging()

    # Start Flask keep-alive server
    run_flask_server()

    # Set up event loop and signal handlers
    loop = asyncio.get_event_loop()
    setup_signal_handlers(loop)

    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(shutdown_bot())
        loop.close()
