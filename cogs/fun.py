import discord
from discord.ext import commands
from datetime import datetime, timedelta, timezone
import asyncio
import typing

# ---------- Configuración ----------
COLOMBIA_TZ = timezone(timedelta(hours=-5))

ORDERED_ROLE_ID = 1421330898569269409
STAFF_CHANNEL_ID = 1424412692860633278
REGLAS_CHANNEL_ID = 1421331154006577182
GUIDE_CHANNEL_ID = 1421331155604471839
HELP_CHANNEL_ID = 1421331102890725487
RULES_CHANNEL_ID = 1421331109622583447

MIDDLEMANNOVATO_ROLE_ID = 1421330888192561152
VENTAS_CHANNEL_ID = 1424451810059354122
MMGUIDE_CHANNEL_ID = 1421331155604471839

OWNER_ID = 335596693603090434
# ------------------------------------

class Fun(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Ping
    @commands.command()
    async def ping(self, ctx: commands.Context):
        await ctx.send("🏓 Pong!")

    # Enviar DM robusto
    async def send_dm(self, member: discord.Member, embed: discord.Embed, staff_channel: typing.Optional[discord.TextChannel] = None, max_attempts: int = 3):
        delay = 2
        for attempt in range(1, max_attempts + 1):
            try:
                await member.send(embed=embed)
                print(f"✅ DM enviado a {member} (intento {attempt})")
                return True
            except discord.Forbidden:
                print(f"⚠️ {member} tiene los DMs cerrados.")
                if staff_channel:
                    await staff_channel.send(f"⚠️ No se pudo enviar DM a {member.mention}, tiene los mensajes directos cerrados.")
                return False
            except Exception as e:
                print(f"❌ Error enviando DM a {member} (intento {attempt}): {e}")
                if attempt < max_attempts:
                    await asyncio.sleep(delay)
                    delay *= 2
        if staff_channel:
            await staff_channel.send(f"⚠️ No se pudo enviar DM a {member.mention} tras {max_attempts} intentos.")
        return False

    # Esperar confirmación del rol
    async def wait_for_role(self, guild: discord.Guild, member_id: int, role_id: int, attempts: int = 5, interval: float = 1.0) -> typing.Optional[discord.Member]:
        for i in range(attempts):
            try:
                member = await guild.fetch_member(member_id)
            except Exception as e:
                print(f"Error fetch_member intento {i+1}: {e}")
                member = None
            if member:
                role = discord.utils.get(guild.roles, id=role_id)
                if role and role in member.roles:
                    return member
            await asyncio.sleep(interval)
        return None

    # Listener: al recibir rol
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        try:
            added_roles = [r for r in after.roles if r not in before.roles]
            print(f"DEBUG: {after} roles agregados: {[r.id for r in added_roles]}")

            staff_channel = after.guild.get_channel(STAFF_CHANNEL_ID)

            # Hitter / Ordered from Site
            ordered_role = discord.utils.get(after.guild.roles, id=ORDERED_ROLE_ID)
            if ordered_role and ordered_role.id in {r.id for r in added_roles}:
                if staff_channel:
                    await staff_channel.send(f"📢 {after.mention} recibió el rol de **Hitter**")
                
                confirmed_member = await self.wait_for_role(after.guild, after.id, ORDERED_ROLE_ID)
                if confirmed_member:
                    reglas_channel = after.guild.get_channel(REGLAS_CHANNEL_ID)
                    guide_channel = after.guild.get_channel(GUIDE_CHANNEL_ID)
                    help_channel = after.guild.get_channel(HELP_CHANNEL_ID)
                    rules_channel = after.guild.get_channel(RULES_CHANNEL_ID)

                    dm_embed = discord.Embed(
                        title="🎉 Welcome to the server!",
                        description=(
                            f"Please read {reglas_channel.mention} to avoid any problems in the server.\n"
                            f"You can find information in {guide_channel.mention}.\n"
                            f"If you have any questions, ask in {help_channel.mention}.\n"
                            f"Read the rules in {rules_channel.mention}."
                        ),
                        color=discord.Color.green()
                    )
                    await self.send_dm(confirmed_member, dm_embed, staff_channel=staff_channel)

            # Middleman Novato
            mm_role = discord.utils.get(after.guild.roles, id=MIDDLEMANNOVATO_ROLE_ID)
            if mm_role and mm_role.id in {r.id for r in added_roles}:
                ventas_channel = after.guild.get_channel(VENTAS_CHANNEL_ID)
                mmguide_channel = after.guild.get_channel(MMGUIDE_CHANNEL_ID)
                if ventas_channel:
                    await ventas_channel.send(f"⭐ {after.mention} recibió el rol de **Middleman**")
                    
                    # Embed visible en canal ventas
                    embed_channel = discord.Embed(
                        title="Bienvenido Middleman",
                        description=(f"No olvides de leer {mmguide_channel.mention} para evitar cualquier problema en el servidor."),
                        color=discord.Color.gold()
                    )
                    await ventas_channel.send(embed=embed_channel)
                
                confirmed_member = await self.wait_for_role(after.guild, after.id, MIDDLEMANNOVATO_ROLE_ID)
                if confirmed_member:
                    dm_embed_mm = discord.Embed(
                        title="🎉 Felicidades, recibiste el rol de Middleman",
                        description=(
                            f"Ahora formas parte de los **Middleman** del servidor.\n\n"
                            f"Recuerda leer {mmguide_channel.mention} y tener en cuenta todas las reglas."
                        ),
                        color=discord.Color.gold()
                    )
                    dm_embed_mm.set_footer(text="Gracias por tu apoyo")
                    await self.send_dm(confirmed_member, dm_embed_mm, staff_channel=ventas_channel)

        except Exception as e:
            print("Error en on_member_update:", e)

    # Desbanear a todos
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unbanall(self, ctx: commands.Context):
        await ctx.send("🔓 Iniciando proceso de desbaneo...")
        try:
            banned_users = [entry async for entry in ctx.guild.bans()]
            if not banned_users:
                await ctx.send("✅ No hay usuarios baneados.")
                return
            await ctx.send(f"🛠️ Desbaneando {len(banned_users)} usuarios...")
            desbaneados = 0
            for ban_entry in banned_users:
                user = ban_entry.user
                try:
                    await ctx.guild.unban(user)
                    desbaneados += 1
                except discord.NotFound:
                    continue
                except discord.Forbidden:
                    await ctx.send(f"⛔ No tengo permiso para desbanear a {user}.")
                    continue
                except Exception as e:
                    await ctx.send(f"⚠️ Error con {user}: {e}")
                    continue
            await ctx.send(f"✅ Desbaneados {desbaneados} usuarios exitosamente.")
        except Exception as e:
            await ctx.send(f"❌ Error inesperado: {e}")
            print(f"[ERROR] {e}")

    # Contador de baneados
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def banlist(self, ctx: commands.Context):
        try:
            banned_entries = [ban async for ban in ctx.guild.bans()]
            total = len(banned_entries)
            embed = discord.Embed(
                title="📊 Lista de baneados",
                description=f"🔒 Este servidor tiene **{total}** usuarios baneados.",
                color=discord.Color.dark_red(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"⚠️ Error al obtener la lista de baneados: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(Fun(bot))
