import logging
import logging.handlers
import os
from datetime import datetime, timezone, timedelta
import traceback
import asyncio
import discord
from discord.ext import commands

try:
    import colorlog
    HAS_COLORLOG = True
except Exception:
    HAS_COLORLOG = False

try:
    import config
    CONFIG = config
except Exception:
    CONFIG = None

LOG_DIR = "logs"
LOG_FILENAME = "bot.log"
MAX_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 5
CONSOLE_LEVEL = logging.INFO
FILE_LEVEL = logging.DEBUG
LOGGER_NAME = "unban_bot"

os.makedirs(LOG_DIR, exist_ok=True)
log_path = os.path.join(LOG_DIR, LOG_FILENAME)

def setup_root_logger():
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        fh = logging.handlers.RotatingFileHandler(
            log_path, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
        )
        fh.setLevel(FILE_LEVEL)
        fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
        logger.addHandler(fh)

        ch = logging.StreamHandler()
        ch.setLevel(CONSOLE_LEVEL)
        if HAS_COLORLOG:
            log_colors = {
                "DEBUG": "reset",
                "INFO": "cyan",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            }
            formatter = colorlog.ColoredFormatter(
                "%(log_color)s%(asctime)s%(reset)s [%(log_color)s%(levelname)s%(reset)s] "
                "%(log_color)s%(message)s%(reset)s",
                datefmt="%H:%M:%S",
                log_colors=log_colors,
            )
        else:
            formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        logger.propagate = False
    return logger

logger = setup_root_logger()

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(LOGGER_NAME)
        self.last_sent = {}  # {channel_id: datetime}
        self.logger.debug("Logs cog inicializado con anti-rate-limit activo.")

    # ----------------------------------
    def _find_log_channel(self, guild):
        if CONFIG and hasattr(CONFIG, "LOG_CHANNEL_ID"):
            ch = guild.get_channel(getattr(CONFIG, "LOG_CHANNEL_ID"))
            if ch:
                return ch
        for name in ["logs", "log", "mod-log", "bot-logs", "moderation"]:
            ch = discord.utils.get(guild.text_channels, name=name)
            if ch:
                return ch
        return None

    def _make_embed(self, title, description, color=discord.Color.blurple()):
        return discord.Embed(title=title, description=description, color=color, timestamp=datetime.now(timezone.utc))

    async def _safe_send(self, channel, embed):
        now = datetime.utcnow()
        last = self.last_sent.get(channel.id)

        # evitar flood (1 mensaje cada 2 segundos por canal)
        if last and (now - last).total_seconds() < 2:
            self.logger.warning(f"Saltando envío para evitar rate-limit en {channel.guild}/{channel.name}")
            return

        try:
            await channel.send(embed=embed)
            self.last_sent[channel.id] = now
        except Exception as e:
            self.logger.error(f"No se pudo enviar mensaje en {channel.guild}/{channel.name}: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info(f"Bot conectado como: {self.bot.user}")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        self.logger.info(f"Unido a guild: {guild.name} ({guild.id})")
        ch = self._find_log_channel(guild)
        if ch:
            embed = self._make_embed("✅ Unido al servidor", f"Me uní a **{guild.name}** (ID: `{guild.id}`)", discord.Color.green())
            await self._safe_send(ch, embed)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        self.logger.info(f"Salí de guild: {guild.name} ({guild.id})")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        ch = self._find_log_channel(member.guild)
        if ch:
            embed = self._make_embed("✅ Usuario unido", f"{member.mention} se unió\nID: `{member.id}`", discord.Color.green())
            embed.set_thumbnail(url=member.display_avatar.url)
            await self._safe_send(ch, embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        ch = self._find_log_channel(member.guild)
        if ch:
            embed = self._make_embed("❌ Usuario salió", f"{member} (`{member.id}`) salió del servidor.", discord.Color.red())
            await self._safe_send(ch, embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if not message.guild or message.author.bot:
            return
        ch = self._find_log_channel(message.guild)
        if ch:
            desc = (
                f"**Autor:** {message.author} (`{message.author.id}`)\n"
                f"**Canal:** {message.channel.mention}\n"
                f"**Contenido:** {message.content or '*[embed/archivo]*'}"
            )
            embed = self._make_embed("🗑️ Mensaje eliminado", desc, discord.Color.orange())
            await self._safe_send(ch, embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if not before.guild or before.author.bot or before.content == after.content:
            return
        ch = self._find_log_channel(before.guild)
        if ch:
            desc = (
                f"**Autor:** {before.author} (`{before.author.id}`)\n"
                f"**Canal:** {before.channel.mention}\n\n"
                f"**Antes:** {before.content or '*Vacío*'}\n"
                f"**Después:** {after.content or '*Vacío*'}"
            )
            embed = self._make_embed("✏️ Mensaje editado", desc, discord.Color.yellow())
            await self._safe_send(ch, embed)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        err_text = "".join(traceback.format_exception(type(error), error, error.__traceback__))[:1500]
        self.logger.error(f"Error en comando {ctx.command} por {ctx.author}: {error}\n{err_text}")
        embed = self._make_embed("⚠️ Error", f"`{error}`", discord.Color.orange())
        try:
            await ctx.send(embed=embed)
        except Exception:
            self.logger.exception("No se pudo enviar embed de error al canal.")

    @commands.command(name="showlogs")
    @commands.is_owner()
    async def showlogs(self, ctx, lines: int = 25):
        try:
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().splitlines()
            tail = content[-lines:]
            text = "```\n" + "\n".join(tail[-1500:]) + "\n```"
            await ctx.send(text[:2000])
        except Exception as e:
            await ctx.send(f"Error leyendo logs: {e}")
            self.logger.exception("Error al leer el archivo de logs")

async def setup(bot):
    await bot.add_cog(Logs(bot))
