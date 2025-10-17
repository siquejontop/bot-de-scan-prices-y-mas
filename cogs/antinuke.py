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

PROTECTED_ROLE_ID = 1421330892038869063  # Rol "auth mm"
OWNER_ROLE_ID = 1421330806399565888      # Rol "owner"

MAX_BANS = 3
MAX_CHANNELS = 3
MAX_ROLES = 3
ACTION_EXPIRY_SECONDS = 300

# =====================================================
# 🧾 Configurar logging seguro en Render
# =====================================================
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
        self.user_actions = {}

    async def log_action(self, guild, description):
        try:
            channel = guild.get_channel(LOG_CHANNEL_ID)
            if channel:
                embed = discord.Embed(
                    title="🛡️ Sistema AntiNuke",
                    description=description,
                    color=discord.Color.red(),
                    timestamp=datetime.now(timezone.utc)
                )
                await channel.send(embed=embed)
        except Exception as e:
            logging.warning(f"No se pudo enviar log en Discord: {e}")

        logging.info(f"{guild.name}: {description}")

    def is_whitelisted(self, user_id, guild):
        return (
            user_id in OWNER_IDS
            or user_id == guild.owner_id
            or user_id in WHITELIST
        )

    async def check_actions(self, executor):
        current_time = datetime.now(timezone.utc)
        if executor.id in self.user_actions:
            last_action = self.user_actions[executor.id].get("last_action", current_time)
            if (current_time - last_action).total_seconds() > ACTION_EXPIRY_SECONDS:
                self.user_actions[executor.id] = {"bans": 0, "channels": 0, "roles": 0, "last_action": current_time}
            else:
                self.user_actions[executor.id]["last_action"] = current_time

    # 🚨 Anti Massban
    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.ban):
            if (datetime.now(timezone.utc) - entry.created_at).total_seconds() < 60:
                executor = entry.user
                if self.is_whitelisted(executor.id, guild):
                    return
                await self.check_actions(executor)
                self.user_actions.setdefault(executor.id, {"bans": 0, "channels": 0, "roles": 0, "last_action": datetime.now(timezone.utc)})
                self.user_actions[executor.id]["bans"] += 1
                if self.user_actions[executor.id]["bans"] >= MAX_BANS:
                    try:
                        await guild.ban(executor, reason="AntiNuke: demasiados bans")
                        await self.log_action(guild, f"🚫 {executor.mention} baneado por intentar hacer massban.")
                    except discord.Forbidden:
                        await self.log_action(guild, f"⛔ No tengo permisos para banear a {executor.mention}.")
                break

    # 🚨 Anti Creación Masiva de Canales
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        async for entry in channel.guild.audit_logs(limit=5, action=discord.AuditLogAction.channel_create):
            if (datetime.now(timezone.utc) - entry.created_at).total_seconds() < 60:
                executor = entry.user
                if self.is_whitelisted(executor.id, channel.guild):
                    return
                await self.check_actions(executor)
                self.user_actions.setdefault(executor.id, {"bans": 0, "channels": 0, "roles": 0, "last_action": datetime.now(timezone.utc)})
                self.user_actions[executor.id]["channels"] += 1
                if self.user_actions[executor.id]["channels"] >= MAX_CHANNELS:
                    try:
                        await channel.guild.ban(executor, reason="AntiNuke: creación masiva de canales")
                        await self.log_action(channel.guild, f"🚫 {executor.mention} baneado por crear demasiados canales.")
                    except discord.Forbidden:
                        await self.log_action(channel.guild, f"⛔ No tengo permisos para banear a {executor.mention}.")
                break

    # 🚨 Anti Eliminación de Canales
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        async for entry in channel.guild.audit_logs(limit=5, action=discord.AuditLogAction.channel_delete):
            if (datetime.now(timezone.utc) - entry.created_at).total_seconds() < 60:
                executor = entry.user
                if self.is_whitelisted(executor.id, channel.guild):
                    return
                try:
                    # Re-crear el canal eliminado
                    new_channel = await channel.guild.create_text_channel(
                        name=channel.name,
                        topic=getattr(channel, "topic", None),
                        position=channel.position,
                        overwrites=channel.overwrites
                    )
                    await self.log_action(channel.guild, f"🔄 {executor.mention} eliminó {channel.name}, canal recreado como {new_channel.mention}.")
                    await channel.guild.ban(executor, reason="AntiNuke: eliminación de canal")
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
                if self.is_whitelisted(executor.id, role.guild):
                    return
                await self.check_actions(executor)
                self.user_actions.setdefault(executor.id, {"bans": 0, "channels": 0, "roles": 0, "last_action": datetime.now(timezone.utc)})
                self.user_actions[executor.id]["roles"] += 1
                if self.user_actions[executor.id]["roles"] >= MAX_ROLES:
                    try:
                        await role.guild.ban(executor, reason="AntiNuke: creación masiva de roles")
                        await self.log_action(role.guild, f"🚫 {executor.mention} baneado por crear demasiados roles.")
                    except discord.Forbidden:
                        await self.log_action(role.guild, f"⛔ No tengo permisos para banear a {executor.mention}.")
                break

    # 🚨 Anti Permisos Peligrosos
    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        async for entry in after.guild.audit_logs(limit=5, action=discord.AuditLogAction.role_update):
            if (datetime.now(timezone.utc) - entry.created_at).total_seconds() < 10:
                executor = entry.user
                if self.is_whitelisted(executor.id, after.guild):
                    return
                dangerous = discord.Permissions(administrator=True, manage_guild=True, ban_members=True, kick_members=True)
                if after.permissions.value & dangerous.value:
                    try:
                        await after.edit(permissions=before.permissions, reason="AntiNuke: permisos peligrosos detectados")
                        await after.guild.ban(executor, reason="AntiNuke: otorgó permisos peligrosos")
                        await self.log_action(after.guild, f"🚫 {executor.mention} baneado por otorgar permisos peligrosos al rol {after.mention}.")
                    except discord.Forbidden:
                        await self.log_action(after.guild, f"⛔ No tengo permisos para revertir el rol o banear a {executor.mention}.")
                break

    # 🚨 Anti Otorgar Rol Protegido
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        protected_role = after.guild.get_role(PROTECTED_ROLE_ID)
        if protected_role and protected_role in after.roles and protected_role not in before.roles:
            async for entry in after.guild.audit_logs(limit=5, action=discord.AuditLogAction.member_role_update):
                if (datetime.now(timezone.utc) - entry.created_at).total_seconds() < 10:
                    executor = entry.user
                    if self.is_whitelisted(executor.id, after.guild):
                        return
                    try:
                        await after.remove_roles(protected_role, reason="AntiNuke: otorgó rol protegido")
                        await after.guild.ban(executor, reason="AntiNuke: otorgó rol protegido")
                        await self.log_action(
                            after.guild,
                            f"⛔ {executor.mention} intentó dar el rol protegido a {after.mention}. "
                            f"El rol fue removido y {executor.mention} fue baneado."
                        )
                    except discord.Forbidden:
                        await self.log_action(after.guild, f"⛔ No tengo permisos para remover el rol de {after.mention} o banear a {executor.mention}.")
                    break

    # 🚨 Anti creación de webhooks
    @commands.Cog.listener()
    async def on_webhook_create(self, webhook):
        guild = webhook.guild
        async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.webhook_create):
            if (datetime.now(timezone.utc) - entry.created_at).total_seconds() < 10:
                executor = entry.user
                if self.is_whitelisted(executor.id, guild):
                    return
                try:
                    await webhook.delete(reason="AntiNuke: creación de webhook no autorizada")
                    await guild.ban(executor, reason="AntiNuke: creó un webhook no autorizado")
                    await self.log_action(guild, f"🔗 {executor.mention} baneado por crear un webhook no autorizado en {webhook.channel.mention}.")
                except discord.Forbidden:
                    await self.log_action(guild, f"⛔ No tengo permisos para eliminar el webhook creado por {executor.mention}.")
                except discord.HTTPException as e:
                    await self.log_action(guild, f"⛔ Error al eliminar webhook: {e}")
                break

    # 🚨 Anti adición de bots
    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        if member.bot:
            async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.bot_add):
                if (datetime.now(timezone.utc) - entry.created_at).total_seconds() < 60:
                    executor = entry.user
                    if self.is_whitelisted(executor.id, guild):
                        return
                    try:
                        await member.ban(reason="AntiNuke: adición de bot no autorizada")
                        await guild.ban(executor, reason="AntiNuke: añadió un bot no autorizado")
                        await self.log_action(guild, f"🤖 {executor.mention} baneado por añadir un bot: {member.mention}.")
                    except discord.Forbidden:
                        await self.log_action(guild, f"⛔ No tengo permisos para banear al bot {member.mention} o a {executor.mention}.")
                    except discord.HTTPException as e:
                        await self.log_action(guild, f"⛔ Error al banear bot: {e}")
                    break

    # 📖 Comando de ayuda
    @commands.command(name="helpantinuke")
    async def helpantinuke(self, ctx):
        embed = discord.Embed(
            title="🛡️ Ayuda AntiNuke",
            description="Lista de protecciones activas:",
            color=discord.Color.blue()
        )
        embed.add_field(name="Protecciones activas", value="""  
        ✅ Anti massban  
        ✅ Anti creación masiva de canales  
        ✅ **Anti eliminación de canales (ban + recreación con permisos)**  
        ✅ Anti creación masiva de roles  
        ✅ Anti permisos peligrosos  
        ✅ Protección especial rol **auth mm**  
        ✅ Anti creación de webhooks  
        ✅ Anti adición de bots/aplicaciones  
        """, inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AntiNuke(bot))
