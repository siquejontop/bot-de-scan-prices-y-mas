import discord
from discord.ext import commands
from datetime import datetime, timedelta, timezone
import logging
import os

# =====================================================
# CONFIGURACIÓN
# =====================================================
OWNER_IDS = [335596693603090434, 523662219020337153, 1158970670928113745]
WHITELIST = {1325579039888511056, 235148962103951360, 762271645855252501, 416358583220043796, 710034409214181396}
LOG_CHANNEL_ID = 1421331172969156660
PROTECTED_ROLE_ID = 1421330892038869063
OWNER_ROLE_ID = 1421330806399565888  # ID del rol Co-Owner

MAX_BANS = 3
MAX_CHANNELS = 3
MAX_ROLES = 3
ACTION_EXPIRY_SECONDS = 300

# Configurar logging
LOG_DIR = "./data"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "antinuke.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class AntiNuke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_actions = {}  # Almacena acciones recientes por usuario

    async def log_action(self, guild, description):
        """Registra una acción en el canal de logs y en el archivo de log."""
        channel = guild.get_channel(LOG_CHANNEL_ID)
        if channel:
            embed = discord.Embed(
                title="🛡️ Sistema AntiNuke",
                description=description,
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            await channel.send(embed=embed)
        logging.info(f"{guild.name}: {description}")

    def is_authorized(self, user_id, guild):
        """Verifica si un usuario está autorizado (owner, whitelist o dueño del servidor)."""
        return user_id in OWNER_IDS or user_id == guild.owner_id or user_id in WHITELIST

    async def track_action(self, executor):
        """Registra y verifica las acciones recientes de un usuario."""
        current_time = datetime.now(timezone.utc)
        if executor.id not in self.user_actions:
            self.user_actions[executor.id] = {"bans": 0, "channels": 0, "roles": 0, "last_action": current_time}
        elif (current_time - self.user_actions[executor.id]["last_action"]).total_seconds() > ACTION_EXPIRY_SECONDS:
            self.user_actions[executor.id] = {"bans": 0, "channels": 0, "roles": 0, "last_action": current_time}
        else:
            self.user_actions[executor.id]["last_action"] = current_time

    async def enforce_action_limit(self, guild, executor, action_type, max_limit, reason):
        """Aplica un ban si se excede el límite de acciones de un tipo específico."""
        self.user_actions[executor.id][action_type] += 1
        if self.user_actions[executor.id][action_type] >= max_limit:
            try:
                await guild.ban(executor, reason=reason)
                await self.log_action(guild, f"🚫 {executor.mention} baneado por {reason.lower()}.")
            except discord.Forbidden:
                await self.log_action(guild, f"⛔ No tengo permisos para banear a {executor.mention}.")

    # 🚨 Anti Massban
    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.ban):
            if (datetime.now(timezone.utc) - entry.created_at).total_seconds() < 60:
                executor = entry.user
                if self.is_authorized(executor.id, guild):
                    return
                await self.track_action(executor)
                await self.enforce_action_limit(guild, executor, "bans", MAX_BANS, "AntiNuke: demasiados bans")
                break

    # 🚨 Anti Creación Masiva de Canales
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        async for entry in channel.guild.audit_logs(limit=5, action=discord.AuditLogAction.channel_create):
            if (datetime.now(timezone.utc) - entry.created_at).total_seconds() < 60:
                executor = entry.user
                if self.is_authorized(executor.id, channel.guild):
                    return
                await self.track_action(executor)
                await self.enforce_action_limit(channel.guild, executor, "channels", MAX_CHANNELS, "AntiNuke: creación masiva de canales")
                break

    # 🚨 Anti Eliminación de Canales
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        async for entry in channel.guild.audit_logs(limit=5, action=discord.AuditLogAction.channel_delete):
            if (datetime.now(timezone.utc) - entry.created_at).total_seconds() < 60:
                executor = entry.user
                if self.is_authorized(executor.id, channel.guild):
                    return
                try:
                    new_channel = await channel.guild.create_text_channel(
                        name=channel.name,
                        topic=getattr(channel, "topic", None),
                        position=channel.position,
                        overwrites=channel.overwrites
                    )
                    await channel.guild.ban(executor, reason="AntiNuke: eliminación de canal")
                    await self.log_action(channel.guild, f"🔄 {executor.mention} eliminó {channel.name}, canal recreado como {new_channel.mention}.")
                    await self.log_action(channel.guild, f"🚫 {executor.mention} baneado por eliminar {channel.name}.")
                except discord.Forbidden:
                    await self.log_action(channel.guild, f"⛔ No tengo permisos para recrear el canal o banear a {executor.mention}.")
                break

    # 🚨 Anti Creación Masiva de Roles
    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        async for entry in role.guild.audit_logs(limit=5, action=discord.AuditLogAction.role_create):
            if (datetime.now(timezone.utc) - entry.created_at).total_seconds() < 60:
                executor = entry.user
                if self.is_authorized(executor.id, role.guild):
                    return
                await self.track_action(executor)
                await self.enforce_action_limit(role.guild, executor, "roles", MAX_ROLES, "AntiNuke: creación masiva de roles")
                break

    # 🚨 Anti Permisos Peligrosos
    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        async for entry in after.guild.audit_logs(limit=5, action=discord.AuditLogAction.role_update):
            if (datetime.now(timezone.utc) - entry.created_at).total_seconds() < 10:
                executor = entry.user
                if self.is_authorized(executor.id, after.guild) or after.id in (PROTECTED_ROLE_ID, OWNER_ROLE_ID):
                    return
                dangerous_perms = discord.Permissions(administrator=True, manage_guild=True, ban_members=True, kick_members=True)
                if after.permissions.value & dangerous_perms.value:
                    bot_member = after.guild.me
                    if not bot_member.guild_permissions.manage_roles or bot_member.top_role <= after:
                        await self.log_action(after.guild, f"⛔ No tengo permisos suficientes para revertir el rol {after.mention}.")
                        return
                    try:
                        await after.edit(permissions=before.permissions, reason="AntiNuke: permisos peligrosos detectados")
                        await after.guild.ban(executor, reason="AntiNuke: otorgó permisos peligrosos")
                        await self.log_action(after.guild, f"🚫 {executor.mention} baneado por otorgar permisos peligrosos al rol {after.mention}.")
                    except discord.Forbidden:
                        await self.log_action(after.guild, f"⛔ No tengo permisos para revertir el rol o banear a {executor.mention}.")
                    except discord.HTTPException as e:
                        await self.log_action(after.guild, f"⛔ Error al revertir permisos: {e}")
                    break

    # 🚨 Anti Otorgar Rol Protegido
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        protected_role = after.guild.get_role(PROTECTED_ROLE_ID)
        if protected_role and protected_role in after.roles and protected_role not in before.roles:
            async for entry in after.guild.audit_logs(limit=5, action=discord.AuditLogAction.member_role_update):
                if (datetime.now(timezone.utc) - entry.created_at).total_seconds() < 10:
                    executor = entry.user
                    if self.is_authorized(executor.id, after.guild):
                        return
                    try:
                        await after.remove_roles(protected_role, reason="AntiNuke: otorgó rol protegido")
                        await executor.timeout(duration=timedelta(minutes=5), reason="AntiNuke: otorgó rol protegido")
                        await self.log_action(
                            after.guild,
                            f"⛔ {executor.mention} intentó dar el rol protegido a {after.mention}. "
                            f"El rol fue removido y {executor.mention} recibió un timeout de 5 minutos."
                        )
                    except discord.Forbidden:
                        await self.log_action(after.guild, f"⛔ No tengo permisos para remover el rol de {after.mention} o aplicar timeout a {executor.mention}.")
                    break

    # 🚨 Anti Creación de Webhooks
    @commands.Cog.listener()
    async def on_webhook_create(self, webhook):
        async for entry in webhook.guild.audit_logs(limit=5, action=discord.AuditLogAction.webhook_create):
            if (datetime.now(timezone.utc) - entry.created_at).total_seconds() < 10:
                executor = entry.user
                if self.is_authorized(executor.id, webhook.guild):
                    return
                try:
                    await webhook.delete(reason="AntiNuke: creación de webhook no autorizada")
                    await webhook.guild.ban(executor, reason="AntiNuke: creó un webhook no autorizado")
                    await self.log_action(webhook.guild, f"🔗 {executor.mention} baneado por crear un webhook no autorizado en {webhook.channel.mention}.")
                except discord.Forbidden:
                    await self.log_action(webhook.guild, f"⛔ No tengo permisos para eliminar el webhook creado por {executor.mention}.")
                except discord.HTTPException as e:
                    await self.log_action(webhook.guild, f"⛔ Error al eliminar webhook: {e}")
                break

    # 🚨 Anti Adición de Bots
    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.bot:
            async for entry in member.guild.audit_logs(limit=5, action=discord.AuditLogAction.bot_add):
                if (datetime.now(timezone.utc) - entry.created_at).total_seconds() < 60:
                    executor = entry.user
                    if self.is_authorized(executor.id, member.guild):
                        return
                    try:
                        await member.ban(reason="AntiNuke: adición de bot no autorizada")
                        await member.guild.ban(executor, reason="AntiNuke: añadió un bot no autorizado")
                        await self.log_action(member.guild, f"🤖 {executor.mention} baneado por añadir un bot: {member.mention}.")
                    except discord.Forbidden:
                        await self.log_action(member.guild, f"⛔ No tengo permisos para banear al bot {member.mention} o a {executor.mention}.")
                    except discord.HTTPException as e:
                        await self.log_action(member.guild, f"⛔ Error al banear bot: {e}")
                    break

    # 📖 Comando de ayuda
    @commands.command(name="helpantinuke")
    async def helpantinuke(self, ctx):
        embed = discord.Embed(
            title="🛡️ Ayuda AntiNuke",
            description="Lista de protecciones activas:",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Protecciones activas",
            value="✅ Anti massban\n✅ Anti creación masiva de canales\n✅ Anti eliminación de canales (ban + recreación)\n"
                  "✅ Anti creación masiva de roles\n✅ Anti permisos peligrosos\n✅ Protección rol protegido\n"
                  "✅ Anti creación de webhooks\n✅ Anti adición de bots",
            inline=False
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AntiNuke(bot))
