import discord
from discord.ext import commands
from discord.ui import View, Button
from datetime import datetime, timedelta, timezone
import asyncio
import re
from typing import Optional

# ============================================================
# ⚙️ Configuración
# ============================================================
MUTE_ROLE_ID = 1418314510049083556  # ID del rol de mute
LIMIT_ROLE_ID = 1415860204624416971  # ID del rol límite para permisos
LOG_CHANNEL_ID = 1418314310739955742  # ID del canal de logs
OWNER_IDS = {335596693603090434, 523662219020337153}  # IDs con permisos absolutos

# ============================================================
# 🛡️ Moderation Cog
# ============================================================
class Moderation(commands.Cog):
    """A cog for server moderation tasks like warnings, mutes, bans, and channel management."""

    def __init__(self, bot: commands.Bot):
        """Initialize the Moderation cog with the bot instance."""
        self.bot = bot
        self.warnings = {}  # Dict[user_id_str]: list of {reason, moderator, timestamp}

    # ============================================================
    # 🔍 Helpers de Permisos y Jerarquía
    # ============================================================
    def is_owner_or_bot_owner(self, ctx: commands.Context, user: discord.abc.Snowflake) -> bool:
        """Check if the user is a bot owner or guild owner."""
        try:
            uid = int(getattr(user, "id", user))
            return uid in OWNER_IDS or (ctx.guild and ctx.guild.owner_id == uid)
        except Exception:
            return False

    def has_permission(self, ctx: commands.Context) -> bool:
        """Check if the author has permission based on LIMIT_ROLE_ID or ownership."""
        author = ctx.author
        if author.id in OWNER_IDS or (ctx.guild and author == ctx.guild.owner):
            return True

        limit_role = ctx.guild.get_role(LIMIT_ROLE_ID) if ctx.guild else None
        if not limit_role:
            return True

        try:
            return author.top_role > limit_role
        except Exception:
            return False

    def check_hierarchy(self, ctx: commands.Context, target_member: discord.Member) -> tuple[bool, str]:
        """Verify hierarchy to ensure the author and bot can act on the target member."""
        if not ctx.guild:
            return False, "❌ Comando solo en servidor."

        author = ctx.author
        if target_member.id == author.id:
            return False, "❌ No puedes aplicarte esa acción a ti mismo."

        if self.is_owner_or_bot_owner(ctx, target_member) and not (author.id in OWNER_IDS or ctx.guild and author == ctx.guild.owner):
            return False, "❌ No puedes sancionar a ese usuario (es owner o protegido)."

        bot_member = ctx.guild.get_member(self.bot.user.id)
        if bot_member and bot_member.top_role <= target_member.top_role:
            return False, "❌ No puedo actuar sobre ese usuario: mi rol es inferior o igual."

        if author.id not in OWNER_IDS and ctx.guild and author != ctx.guild.owner:
            if author.top_role <= target_member.top_role:
                return False, "❌ No puedes actuar sobre ese usuario (rol igual o superior)."

        return True, ""

    # ============================================================
    # 📜 Logging
    # ============================================================
    async def log_action(self, ctx: commands.Context, title: str, color: discord.Colour, target: Optional[discord.abc.Snowflake] = None, extra: str = ""):
        """Send a log embed to the configured log channel."""
        channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if not channel:
            return

        embed = discord.Embed(title=title, color=color, timestamp=datetime.now(timezone.utc))
        embed.add_field(
            name="👤 Usuario",
            value=target.mention if target and hasattr(target, "mention") else "N/A",
            inline=False
        )
        embed.add_field(name="🛠️ Moderador", value=ctx.author.mention, inline=False)
        if extra:
            embed.add_field(name="📌 Extra", value=extra, inline=False)

        try:
            await channel.send(embed=embed)
        except Exception:
            pass

    # ============================================================
    # 🛠️ Utilidades
    # ============================================================
    def parse_duration(self, duration_str: str) -> Optional[timedelta]:
        """Parse a duration string (e.g., 5s, 10m, 2h, 3d, 1w) to timedelta."""
        if not duration_str:
            return None
        match = re.match(r'^(\d+)([smhdw])$', duration_str.lower())
        if not match:
            return None
        value, unit = int(match.group(1)), match.group(2)
        return {
            's': timedelta(seconds=value),
            'm': timedelta(minutes=value),
            'h': timedelta(hours=value),
            'd': timedelta(days=value),
            'w': timedelta(weeks=value),
        }.get(unit)

    async def resolve_member(self, ctx: commands.Context, identifier: str) -> Optional[discord.Member]:
        """Resolve a guild member from mention, ID, name, or name#discriminator."""
        if not identifier or not ctx.guild:
            return None

        # Try mention or ID
        id_match = re.search(r'(\d{6,20})', identifier)
        if id_match:
            member = ctx.guild.get_member(int(id_match.group(1)))
            if member:
                return member

        # Try name#discriminator
        if '#' in identifier:
            name, discrim = identifier.rsplit('#', 1)
            for member in ctx.guild.members:
                if member.name == name and member.discriminator == discrim:
                    return member

        # Try display_name or name (case-insensitive)
        lower = identifier.lower()
        for member in ctx.guild.members:
            if member.display_name.lower() == lower or member.name.lower() == lower:
                return member
        return None

    async def find_banned_user(self, ctx: commands.Context, identifier: str) -> Optional[discord.User]:
        """Find a banned user by ID, name, or name#discriminator."""
        if not ctx.guild:
            return None

        try:
            bans = [entry async for entry in ctx.guild.bans()]
        except discord.Forbidden:
            return None
        except Exception:
            return None

        id_match = re.search(r'(\d{6,20})', identifier)
        if id_match:
            uid = int(id_match.group(1))
            for entry in bans:
                if entry.user.id == uid:
                    return entry.user
            try:
                return await self.bot.fetch_user(uid)
            except Exception:
                return None

        if '#' in identifier:
            name, discrim = identifier.rsplit('#', 1)
            for entry in bans:
                if entry.user.name == name and entry.user.discriminator == discrim:
                    return entry.user

        lower = identifier.lower()
        for entry in bans:
            if entry.user.name.lower() == lower:
                return entry.user
        return None

    # ============================================================
    # ⚠️ Comandos: Advertencias
    # ============================================================
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx: commands.Context, target: str = None, *, reason: str = "No especificado"):
        """Add a warning to a user."""
        if not target or not self.has_permission(ctx):
            embed = discord.Embed(
                title="⚠️ Uso incorrecto",
                description="`$warn <usuario/id/mention/name#1234> [razón]`",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            return await ctx.send(embed=embed)

        member = await self.resolve_member(ctx, target)
        if not member:
            return await ctx.send("❌ Usuario no encontrado en el servidor.")

        ok, reason_err = self.check_hierarchy(ctx, member)
        if not ok:
            return await ctx.send(reason_err)

        uid = str(member.id)
        self.warnings.setdefault(uid, []).append({
            "reason": reason,
            "moderator": ctx.author.id,
            "timestamp": datetime.now(timezone.utc)
        })

        embed = discord.Embed(
            title="⚠️ Advertencia",
            description=f"{member.mention} ha sido advertido.\n**Razón:** {reason}",
            color=discord.Color.yellow(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="🔢 Total advertencias", value=str(len(self.warnings[uid])), inline=True)
        embed.set_footer(text=f"Moderador: {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
        await self.log_action(ctx, "⚠️ Advertencia", discord.Color.yellow(), target=member, extra=f"Razón: {reason}")

        if len(self.warnings[uid]) >= 3:
            mute_role = ctx.guild.get_role(MUTE_ROLE_ID)
            if mute_role:
                ok2, err2 = self.check_hierarchy(ctx, member)
                if ok2:
                    await member.add_roles(mute_role, reason="Alcanzó 3 advertencias")
                    embed2 = discord.Embed(
                        title="🔇 Mute automático",
                        description=f"{member.mention} fue muteado automáticamente por alcanzar 3 advertencias.",
                        color=discord.Color.dark_gray(),
                        timestamp=datetime.now(timezone.utc)
                    )
                    await ctx.send(embed=embed2)
                    await self.log_action(ctx, "🔇 Mute automático", discord.Color.dark_gray(), target=member, extra="3 advertencias alcanzadas")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def unwarn(self, ctx: commands.Context, target: str = None, index: int = None):
        """Remove a specific warning by index (1-based)."""
        if not target or index is None or not self.has_permission(ctx):
            embed = discord.Embed(
                title="⚠️ Uso incorrecto",
                description="`$unwarn <usuario/id/mention/name#1234> <índice>`",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            return await ctx.send(embed=embed)

        member = await self.resolve_member(ctx, target)
        if not member:
            return await ctx.send("❌ Usuario no encontrado en el servidor.")

        ok, reason_err = self.check_hierarchy(ctx, member)
        if not ok:
            return await ctx.send(reason_err)

        uid = str(member.id)
        if uid not in self.warnings or index < 1 or index > len(self.warnings[uid]):
            return await ctx.send("⚠️ Índice inválido o el usuario no tiene advertencias.")

        removed = self.warnings[uid].pop(index - 1)
        await ctx.send(f"✅ Advertencia #{index} removida de {member.mention}.")
        await self.log_action(ctx, "⚠️ Advertencia removida", discord.Color.orange(), target=member, extra=f"Índice: {index} - Razón original: {removed.get('reason')}")

    @commands.command(aliases=["infractions", "warns"])
    @commands.has_permissions(manage_messages=True)
    async def warnings(self, ctx: commands.Context, target: str = None):
        """Display a user's warnings."""
        if not target:
            embed = discord.Embed(
                title="⚠️ Uso incorrecto",
                description="`$warnings <usuario/id/mention/name#1234>`",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            return await ctx.send(embed=embed)

        member = await self.resolve_member(ctx, target)
        if not member:
            return await ctx.send("❌ Usuario no encontrado en el servidor.")

        uid = str(member.id)
        if uid not in self.warnings or not self.warnings[uid]:
            return await ctx.send(f"📋 {member.mention} no tiene advertencias.")

        embed = discord.Embed(
            title=f"📋 Advertencias de {member}",
            color=discord.Color.orange(),
            timestamp=datetime.now(timezone.utc)
        )
        for i, warning in enumerate(self.warnings[uid], 1):
            ts = warning.get("timestamp")
            ts_str = ts.strftime('%Y-%m-%d %H:%M:%S UTC') if isinstance(ts, datetime) else str(ts)
            embed.add_field(
                name=f"Advertencia #{i}",
                value=f"Razón: {warning['reason']}\nModerador: <@{warning['moderator']}>\nFecha: {ts_str}",
                inline=False
            )
        await ctx.send(embed=embed)

    # ============================================================
    # 🔇 Comandos: Mute y Timeout
    # ============================================================
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx: commands.Context, target: str = None, duration: str = None, *, reason: str = "No especificado"):
        """Mute a user by assigning the mute role, with optional duration."""
        if not target or not self.has_permission(ctx):
            embed = discord.Embed(
                title="⚠️ Uso incorrecto",
                description="`$mute <usuario/id/mention/name#1234> [duración(s/m/h/d/w)] [razón]`",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            return await ctx.send(embed=embed)

        member = await self.resolve_member(ctx, target)
        if not member:
            return await ctx.send("❌ Usuario no encontrado en el servidor.")

        ok, err = self.check_hierarchy(ctx, member)
        if not ok:
            return await ctx.send(err)

        mute_role = ctx.guild.get_role(MUTE_ROLE_ID)
        if not mute_role:
            return await ctx.send("❌ Rol de mute no configurado o no encontrado.")

        duration_td = self.parse_duration(duration) if duration else None
        if duration and not duration_td:
            return await ctx.send("⚠️ Duración inválida. Usa: 5s, 10m, 7h, 2d, 1w.")

        try:
            await member.add_roles(mute_role, reason=reason)
            description = f"{member.mention} fue muteado.\n**Razón:** {reason}"
            if duration:
                description += f"\n⏳ Duración: {duration}"
            embed = discord.Embed(
                title="🔇 Usuario muteado",
                description=description,
                color=discord.Color.dark_gray(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)
            await self.log_action(ctx, "🔇 Usuario muteado", discord.Color.dark_gray(), target=member, extra=f"Duración: {duration or 'Indefinida'}")

            if duration_td:
                async def auto_unmute():
                    await asyncio.sleep(duration_td.total_seconds())
                    if mute_role in member.roles:
                        await member.remove_roles(mute_role, reason="Mute expirado automáticamente")
                        await self.log_action(ctx, "🔊 Mute expirado", discord.Color.green(), target=member)

                self.bot.loop.create_task(auto_unmute())
        except discord.Forbidden:
            await ctx.send("❌ No tengo permisos para asignar roles.")
        except Exception as e:
            await ctx.send(f"❌ Error al mutear: {e}")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx: commands.Context, target: str = None):
        """Remove the mute role from a user."""
        if not target or not self.has_permission(ctx):
            embed = discord.Embed(
                title="⚠️ Uso incorrecto",
                description="`$unmute <usuario/id/mention/name#1234>`",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            return await ctx.send(embed=embed)

        member = await self.resolve_member(ctx, target)
        if not member:
            return await ctx.send("❌ Usuario no encontrado en el servidor.")

        ok, err = self.check_hierarchy(ctx, member)
        if not ok:
            return await ctx.send(err)

        mute_role = ctx.guild.get_role(MUTE_ROLE_ID)
        if not mute_role:
            return await ctx.send("❌ Rol de mute no configurado.")

        try:
            if mute_role in member.roles:
                await member.remove_roles(mute_role, reason=f"Desmuteado por {ctx.author}")
                embed = discord.Embed(
                    title="🔊 Usuario desmuteado",
                    description=f"{member.mention} fue desmuteado.",
                    color=discord.Color.green(),
                    timestamp=datetime.now(timezone.utc)
                )
                await ctx.send(embed=embed)
                await self.log_action(ctx, "🔊 Usuario desmuteado", discord.Color.green(), target=member)
            else:
                await ctx.send("⚠️ Ese usuario no está muteado.")
        except discord.Forbidden:
            await ctx.send("❌ No tengo permisos para remover roles.")
        except Exception as e:
            await ctx.send(f"❌ Error al desmutear: {e}")

    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx: commands.Context, target: str = None, duration: str = None, *, reason: str = "No especificado"):
        """Apply a timeout to a user (max 28 days)."""
        if not target or not duration or not self.has_permission(ctx):
            embed = discord.Embed(
                title="⚠️ Uso incorrecto",
                description="`$timeout <usuario/id/mention/name#1234> <duración(s/m/h/d/w)> [razón]`",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            return await ctx.send(embed=embed)

        member = await self.resolve_member(ctx, target)
        if not member:
            return await ctx.send("❌ Usuario no encontrado en el servidor.")

        ok, err = self.check_hierarchy(ctx, member)
        if not ok:
            return await ctx.send(err)

        duration_td = self.parse_duration(duration)
        if not duration_td or duration_td > timedelta(days=28):
            return await ctx.send("⚠️ Duración inválida (máx. 28 días). Usa: 5s, 10m, 7h, 2d, 1w.")

        until = datetime.now(timezone.utc) + duration_td
        try:
            await member.edit(timed_out_until=until, reason=reason)
            embed = discord.Embed(
                title="⏳ Timeout aplicado",
                description=f"{member.mention} fue silenciado por {duration}.\n**Razón:** {reason}",
                color=discord.Color.blue(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)
            await self.log_action(ctx, "⏳ Timeout aplicado", discord.Color.blue(), target=member, extra=f"Duración: {duration}")
        except discord.Forbidden:
            await ctx.send("❌ No tengo permisos para aplicar timeout.")
        except Exception as e:
            await ctx.send(f"❌ Error al aplicar timeout: {e}")

    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def remove_timeout(self, ctx: commands.Context, target: str = None):
        """Remove a timeout from a user."""
        if not target or not self.has_permission(ctx):
            embed = discord.Embed(
                title="⚠️ Uso incorrecto",
                description="`$remove_timeout <usuario/id/mention/name#1234>`",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            return await ctx.send(embed=embed)

        member = await self.resolve_member(ctx, target)
        if not member:
            return await ctx.send("❌ Usuario no encontrado en el servidor.")

        ok, err = self.check_hierarchy(ctx, member)
        if not ok:
            return await ctx.send(err)

        try:
            await member.edit(timed_out_until=None, reason=f"Timeout removido por {ctx.author}")
            embed = discord.Embed(
                title="🔓 Timeout removido",
                description=f"{member.mention} puede hablar de nuevo.",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)
            await self.log_action(ctx, "🔓 Timeout removido", discord.Color.green(), target=member)
        except discord.Forbidden:
            await ctx.send("❌ No tengo permisos para remover timeout.")
        except Exception as e:
            await ctx.send(f"❌ Error al remover timeout: {e}")

    # ============================================================
    # 👢 Comandos: Kick y Ban
    # ============================================================
    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, target: str = None, *, reason: str = "No especificado"):
        """Kick a user from the server."""
        if not target or not self.has_permission(ctx):
            embed = discord.Embed(
                title="⚠️ Uso incorrecto",
                description="`$kick <usuario/id/mention/name#1234> [razón]`",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            return await ctx.send(embed=embed)

        member = await self.resolve_member(ctx, target)
        if not member:
            return await ctx.send("❌ Usuario no encontrado en el servidor.")

        ok, err = self.check_hierarchy(ctx, member)
        if not ok:
            return await ctx.send(err)

        try:
            await member.kick(reason=reason)
            embed = discord.Embed(
                title="👢 Usuario expulsado",
                description=f"{member.mention} fue expulsado.\n**Razón:** {reason}",
                color=discord.Color.orange(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)
            await self.log_action(ctx, "👢 Usuario expulsado", discord.Color.orange(), target=member, extra=f"Razón: {reason}")
        except discord.Forbidden:
            await ctx.send("❌ No tengo permisos para expulsar a este usuario.")
        except Exception as e:
            await ctx.send(f"❌ Error al expulsar: {e}")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, target: str = None, *, reason: str = "No especificado"):
        """Ban a user by ID, mention, or name#discriminator."""
        if not target or not self.has_permission(ctx):
            embed = discord.Embed(
                title="⚠️ Uso incorrecto",
                description="`$ban <usuario/id/mention/name#1234> [razón]`",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            return await ctx.send(embed=embed)

        member = await self.resolve_member(ctx, target)
        target_obj = member

        if member:
            ok, err = self.check_hierarchy(ctx, member)
            if not ok:
                return await ctx.send(err)
        else:
            id_match = re.search(r'(\d{6,20})', target)
            if id_match:
                uid = int(id_match.group(1))
                if uid in OWNER_IDS or (ctx.guild and ctx.guild.owner_id == uid and ctx.author.id not in OWNER_IDS):
                    return await ctx.send("❌ No puedes banear a ese usuario (protegido o owner).")
                try:
                    user = await self.bot.fetch_user(uid)
                    target_obj = user
                except Exception:
                    return await ctx.send("❌ Usuario no encontrado para banear.")
            else:
                user = await self.find_banned_user(ctx, target)
                if user:
                    return await ctx.send("⚠️ Ese usuario ya está baneado.")
                return await ctx.send("❌ Usuario no encontrado. Usa ID o name#discrim.")

        try:
            await ctx.guild.ban(target_obj, reason=reason)
            embed = discord.Embed(
                title="🚫 Usuario baneado",
                description=f"{getattr(target_obj, 'mention', target_obj.name)} fue baneado.\n**Razón:** {reason}",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)
            await self.log_action(ctx, "🚫 Usuario baneado", discord.Color.red(), target=target_obj, extra=f"Razón: {reason}")
        except discord.Forbidden:
            await ctx.send("❌ No tengo permisos para banear a este usuario.")
        except Exception as e:
            await ctx.send(f"❌ Error al banear: {e}")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, target: str = None, *, reason: str = "No especificado"):
        """Unban a user by ID or name#discriminator."""
        if not target or not self.has_permission(ctx):
            embed = discord.Embed(
                title="⚠️ Uso incorrecto",
                description="`$unban <usuario/id/name#1234> [razón]`",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            return await ctx.send(embed=embed)

        banned_user = await self.find_banned_user(ctx, target)
        if not banned_user:
            return await ctx.send("❌ No encontré al usuario en la lista de bans.")

        if banned_user.id in OWNER_IDS or (ctx.guild and ctx.guild.owner_id == banned_user.id and ctx.author.id not in OWNER_IDS):
            return await ctx.send("❌ No puedes desbanear a ese usuario (protegido o owner).")

        try:
            await ctx.guild.unban(banned_user, reason=reason)
            embed = discord.Embed(
                title="🔓 Usuario desbaneado",
                description=f"{banned_user.name} fue desbaneado.\n**Razón:** {reason}",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)
            await self.log_action(ctx, "🔓 Usuario desbaneado", discord.Color.green(), target=banned_user, extra=f"Razón: {reason}")
        except discord.Forbidden:
            await ctx.send("❌ No tengo permisos para desbanear.")
        except discord.NotFound:
            await ctx.send("❌ No se encontró el ban.")
        except Exception as e:
            await ctx.send(f"❌ Error al desbanear: {e}")

    # ============================================================
    # 🧹 Comandos: Limpieza
    # ============================================================
    @commands.command(aliases=["purge", "c"])
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx: commands.Context, amount: int = None):
        """Delete a specified number of messages (max 100)."""
        if not amount or amount < 1 or amount > 100 or not self.has_permission(ctx):
            embed = discord.Embed(
                title="❌ Uso incorrecto",
                description="`$clear <cantidad>` (máx. 100)",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            return await ctx.send(embed=embed)

        try:
            deleted = await ctx.channel.purge(limit=amount + 1)
            count = max(0, len(deleted) - 1)
            embed = discord.Embed(
                title="🧹 Purge realizado",
                description=f"Se eliminaron **{count}** mensajes en {ctx.channel.mention}.",
                color=discord.Color.blurple(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed, delete_after=3)
            await self.log_action(ctx, "🧹 Purge realizado", discord.Color.blurple(), extra=f"Canal: {ctx.channel.mention}\nMensajes: {count}")
        except discord.Forbidden:
            await ctx.send("❌ No tengo permisos para eliminar mensajes.")
        except Exception as e:
            await ctx.send(f"❌ Error al purgar: {e}")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clearuser(self, ctx: commands.Context, target: str = None, amount: int = None):
        """Delete a specified number of messages from a user (max 100)."""
        if not target or not amount or amount < 1 or amount > 100 or not self.has_permission(ctx):
            embed = discord.Embed(
                title="❌ Uso incorrecto",
                description="`$clearuser <usuario/id/mention/name#1234> <cantidad>` (máx. 100)",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            return await ctx.send(embed=embed)

        member = await self.resolve_member(ctx, target)
        if not member:
            return await ctx.send("❌ Usuario no encontrado en el servidor.")

        ok, err = self.check_hierarchy(ctx, member)
        if not ok:
            return await ctx.send(err)

        def is_member_message(m):
            return m.author == member

        try:
            deleted = await ctx.channel.purge(limit=amount + 1, check=is_member_message)
            count = max(0, len(deleted) - 1)
            embed = discord.Embed(
                title="🧹 Mensajes eliminados",
                description=f"Se eliminaron **{count}** mensajes de {member.mention} en {ctx.channel.mention}.",
                color=discord.Color.blurple(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed, delete_after=3)
            await self.log_action(ctx, "🧹 Mensajes eliminados", discord.Color.blurple(), target=member, extra=f"Mensajes: {count}")
        except discord.Forbidden:
            await ctx.send("❌ No tengo permisos para eliminar mensajes.")
        except Exception as e:
            await ctx.send(f"❌ Error al purgar: {e}")

    # ============================================================
    # 🔒 Comandos: Gestión de Canales
    # ============================================================
    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None):
        """Lock a channel for @everyone."""
        channel = channel or ctx.channel
        try:
            overwrite = channel.overwrites_for(ctx.guild.default_role)
            overwrite.send_messages = False
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
            embed = discord.Embed(
                title="🔒 Canal bloqueado",
                description=f"{channel.mention} ha sido bloqueado.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)
            await self.log_action(ctx, "🔒 Canal bloqueado", discord.Color.red(), extra=f"Canal: {channel.mention}")
        except discord.Forbidden:
            await ctx.send("❌ No tengo permisos para modificar permisos del canal.")
        except Exception as e:
            await ctx.send(f"❌ Error al bloquear canal: {e}")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None):
        """Unlock a channel for @everyone."""
        channel = channel or ctx.channel
        try:
            overwrite = channel.overwrites_for(ctx.guild.default_role)
            overwrite.send_messages = None
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
            embed = discord.Embed(
                title="🔓 Canal desbloqueado",
                description=f"{channel.mention} ha sido desbloqueado.",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)
            await self.log_action(ctx, "🔓 Canal desbloqueado", discord.Color.green(), extra=f"Canal: {channel.mention}")
        except discord.Forbidden:
            await ctx.send("❌ No tengo permisos para modificar permisos del canal.")
        except Exception as e:
            await ctx.send(f"❌ Error al desbloquear canal: {e}")

    # ============================================================
    # 📖 Comando: Ayuda
    # ============================================================
    @commands.command(name="helpmoderation", aliases=["helpmod", "modhelp"])
    async def helpmoderation(self, ctx: commands.Context):
        """Display a help embed for moderation commands."""
        embed = discord.Embed(
            title="🛠️ Panel de Moderación",
            description="Lista de comandos disponibles para moderar el servidor.",
            color=discord.Color.blurple(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(
            name="⚠️ Advertencias",
            value="`$warn <usuario> [razón]`\n`$unwarn <usuario> <índice>`\n`$warnings <usuario>`",
            inline=False
        )
        embed.add_field(
            name="🔇 Mute / Timeout",
            value="`$mute <usuario> [duración] [razón]`\n`$unmute <usuario>`\n`$timeout <usuario> <duración> [razón]`\n`$remove_timeout <usuario>`",
            inline=False
        )
        embed.add_field(
            name="👢 Kick / Ban",
            value="`$kick <usuario> [razón]`\n`$ban <usuario|id> [razón]`\n`$unban <usuario|id> [razón]`",
            inline=False
        )
        embed.add_field(
            name="🧹 Limpieza",
            value="`$clear <número>`\n`$clearuser <usuario> <número>`",
            inline=False
        )
        embed.add_field(
            name="🔒 Canales",
            value="`$lock [canal]`\n`$unlock [canal]`",
            inline=False
        )
        embed.add_field(
            name="📜 Duraciones válidas",
            value="`5s`, `10m`, `1h`, `2d`, `1w` (máx. 28d para timeout)",
            inline=False
        )
        embed.set_footer(text=f"Solicitado por {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

# ============================================================
# 🚀 Setup
# ============================================================
async def setup(bot: commands.Bot):
    """Set up the Moderation cog for the bot."""
    await bot.add_cog(Moderation(bot))
