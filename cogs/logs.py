import logging
import logging.handlers
import os
from datetime import datetime, timezone, timedelta
import traceback
import asyncio
import discord
from discord.ext import commands

# ======================
# CONFIGURACIÓN LOGS
# ======================

try:
    import colorlog
    HAS_COLORLOG = True
except:
    HAS_COLORLOG = False

try:
    import config
    CONFIG = config
except:
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
            formatter = colorlog.ColoredFormatter(
                "%(log_color)s%(asctime)s%(reset)s [%(log_color)s%(levelname)s%(reset)s] "
                "%(log_color)s%(message)s%(reset)s",
                datefmt="%H:%M:%S",
            )
        else:
            formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")

        ch.setFormatter(formatter)
        logger.addHandler(ch)

    return logger


logger = setup_root_logger()


# ===========================================================
# ====================== COG DE LOGS ========================
# ===========================================================

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(LOGGER_NAME)
        self.last_sent = {}  
        self.logger.debug("✅ Cog de logs inicializado correctamente.")

    # ======================
    # BUSCAR CANAL DE LOGS
    # ======================
    def _find_log_channel(self, guild):
        if CONFIG and hasattr(CONFIG, "LOG_CHANNEL_ID"):
            ch = guild.get_channel(CONFIG.LOG_CHANNEL_ID)
            if ch:
                return ch

        for name in ["logs", "mod-log", "bot-logs", "registro", "moderation"]:
            ch = discord.utils.get(guild.text_channels, name=name)
            if ch:
                return ch
        return None

    # ======================
    def _embed(self, title, desc, color=discord.Color.blurple()):
        return discord.Embed(
            title=title,
            description=desc,
            color=color,
            timestamp=datetime.now(timezone.utc)
        )

    # ======================
    async def _safe_send(self, channel, embed):
        now = datetime.utcnow()
        last = self.last_sent.get(channel.id)
        if last and (now - last).total_seconds() < 1:
            return

        try:
            await channel.send(embed=embed)
            self.last_sent[channel.id] = now
        except Exception as e:
            self.logger.error(f"Error enviando logs en {channel.guild}/{channel.name}: {e}")

    # ===========================================================
    # ======================== EVENTOS ===========================
    # ===========================================================

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info(f"✅ Bot listo: {self.bot.user}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        ch = self._find_log_channel(member.guild)
        if ch:
            embed = self._embed("✅ Usuario unido", f"{member.mention}\nID: `{member.id}`", discord.Color.green())
            embed.set_thumbnail(url=member.display_avatar.url)
            await self._safe_send(ch, embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        ch = self._find_log_channel(member.guild)
        if ch:
            embed = self._embed("❌ Usuario salió", f"{member} (`{member.id}`)", discord.Color.red())
            await self._safe_send(ch, embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if not message.guild or message.author.bot:
            return

        ch = self._find_log_channel(message.guild)
        if not ch:
            return

        embed = self._embed(
            "🗑️ Mensaje eliminado",
            f"**Autor:** {message.author} (`{message.author.id}`)\n"
            f"**Canal:** {message.channel.mention}\n"
            f"**Contenido:** {message.content or '*[embed/archivo]*'}",
            discord.Color.orange()
        )
        await self._safe_send(ch, embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if not before.guild or before.author.bot or before.content == after.content:
            return

        ch = self._find_log_channel(before.guild)
        if not ch:
            return

        embed = self._embed(
            "✏️ Mensaje editado",
            f"**Autor:** {before.author} (`{before.author.id}`)\n"
            f"**Canal:** {before.channel.mention}\n\n"
            f"**Antes:** {before.content or '*Vacío*'}\n"
            f"**Después:** {after.content or '*Vacío*'}",
            discord.Color.yellow()
        )
        await self._safe_send(ch, embed)

    # ===========================================================
    # 🔥 LOGS DE ROLES (AL ESTILO AUDIT LOG)
    # ===========================================================

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.roles == after.roles:
            return

        ch = self._find_log_channel(after.guild)
        if not ch:
            return

        # quién hizo el cambio
        try:
            entry = (await after.guild.audit_logs(
                limit=1,
                action=discord.AuditLogAction.member_role_update
            ).flatten())[0]
            moderator = entry.user
        except:
            moderator = "Desconocido"

        added = list(set(after.roles) - set(before.roles))
        removed = list(set(before.roles) - set(after.roles))

        embed = discord.Embed(
            color=discord.Color.blurple(),
            timestamp=datetime.now(timezone.utc)
        )

        embed.set_author(
            name=f"{moderator} updated roles for {after}",
            icon_url=after.display_avatar.url
        )

        c = 1
        if added:
            embed.add_field(
                name=f"{c:02d} – Added Roles",
                value="\n".join([r.name for r in added]),
                inline=False
            )
            c += 1

        if removed:
            embed.add_field(
                name=f"{c:02d} – Removed Roles",
                value="\n".join([r.name for r in removed]),
                inline=False
            )

        await self._safe_send(ch, embed)

    # ===========================================================
    # 🔥 LOGS DE PURGE (GUARDA TODOS LOS MENSAJES)
    # ===========================================================

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages):
        if not messages:
            return

        guild = messages[0].guild
        ch = self._find_log_channel(guild)
        if not ch:
            return

        content = "\n".join(
            [f"[{m.author}] {m.content or '[embed/archivo]'}" for m in messages]
        )

        embed = self._embed(
            f"🧹 Purge ejecutado ({len(messages)} mensajes)",
            f"```{content[:3900]}```",
            discord.Color.red()
        )

        await self._safe_send(ch, embed)

    # ===========================================================
    # LOGS DE ERRORES
    # ===========================================================

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        self.logger.error(f"⚠️ Error: {error}")

        embed = self._embed("⚠️ Error en comando", f"```{error}```", discord.Color.orange())
        try:
            await ctx.send(embed=embed, delete_after=10)
        except:
            pass


async def setup(bot):
    await bot.add_cog(Logs(bot))
