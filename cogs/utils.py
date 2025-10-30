import discord
from discord.ext import commands
from datetime import datetime, timezone
import random
import asyncio

class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # =====================================================
    # USER INFO – ESTILO DISCORD OFICIAL (CORREGIDO)
    # =====================================================
    @commands.command(aliases=["userinfo", "ui", "user", "w"])
    async def usuario(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        user = member._user  # Solo para datos globales (banner, about, flags)

        # === BADGES ===
        badges = []
        flags = user.public_flags
        badge_map = {
            "staff": "<:discord_staff:1139666211892232212>",
            "partner": "<:partner:1139666213855191040>",
            "certified_moderator": "<:certified_mod:1139666209916751872>",
            "hypesquad": "<:hypesquad:1139666215893581824>",
            "hypesquad_bravery": "<:bravery:1139666205877604352>",
            "hypesquad_brilliance": "<:brilliance:1139666207890804806>",
            "hypesquad_balance": "<:balance:1139666203924557844>",
            "early_supporter": "<:early_supporter:1139666208872292352>",
            "bug_hunter": "<:bug_hunter:1139666210130157568>",
            "bug_hunter_level_2": "<:bug_hunter_gold:1139666212848164864>",
        }
        for flag, emoji in badge_map.items():
            if getattr(flags, flag, False):
                badges.append(emoji)
        
        # CORREGIDO: Usa member.premium_since
        if member.premium_since:
            badges.append("<:nitro:1139666214857199616>")
        
        badges_text = " ".join(badges) if badges else "Sin insignias"

        # === ESTADO ===
        status_icons = {
            discord.Status.online: "<:status_online:1139666228908093440>",
            discord.Status.idle: "<:status_idle:1139666230808150016>",
            discord.Status.dnd: "<:status_dnd:1139666226869698560>",
            discord.Status.offline: "<:status_offline:1139666228861976576>"
        }
        status_emoji = status_icons.get(member.status, "<:status_offline:1139666228861976576>")
        status_text = {
            discord.Status.online: "En línea",
            discord.Status.idle: "Ausente",
            discord.Status.dnd: "No molestar",
            discord.Status.offline: "Desconectado"
        }.get(member.status, "Desconocido")

        # === DISPOSITIVOS ===
        devices = []
        if member.desktop_status != discord.Status.offline: devices.append("<:desktop:1139666242854236160>")
        if member.mobile_status != discord.Status.offline: devices.append("<:mobile:1139666244859092992>")
        if member.web_status != discord.Status.offline: devices.append("<:web:1139666246851321856>")
        devices_text = " ".join(devices) if devices else "<:status_offline:1139666228861976576>"

        # === CUSTOM STATUS ===
        custom_status = "Ninguno"
        for act in member.activities:
            if act.type == discord.ActivityType.custom and act.name:
                emoji = f"{act.emoji} " if act.emoji else ""
                custom_status = f"{emoji}{act.name}"
                break

        # === ROLES ===
        roles = [role.mention for role in member.roles[::-1][:-1]]
        roles_text = " ".join(roles[:25]) + ("..." if len(roles) > 25 else "") if roles else "Sin roles"

        # === FECHAS ===
        discord_join = int(user.created_at.timestamp())
        server_join = int(member.joined_at.timestamp()) if member.joined_at else "?"

        # === URLs ===
        banner_url = user.banner.url if user.banner else None
        avatar_url = member.display_avatar.url

        # === ABOUT ME ===
        about = user.about or "No tiene descripción."

        # === EMBED ===
        embed = discord.Embed(
            description=f"**{about}**",
            color=member.color if member.color != discord.Color.default() else discord.Color.blurple(),
            timestamp=datetime.utcnow()
        )
        embed.set_author(name=str(member), icon_url=avatar_url)
        if banner_url:
            embed.set_image(url=banner_url)
        embed.set_thumbnail(url=avatar_url)

        embed.add_field(
            name="",
            value=(
                f"{status_emoji} **Estado**\n"
                f"{status_emoji} {status_text}\n"
                f"{devices_text}\n\n"
                f"**Estado personalizado**\n{custom_status}\n\n"
                f"**Insignias**\n{badges_text}"
            ),
            inline=False
        )

        embed.add_field(
            name="Entradas",
            value=(
                f"<:discord_logo:1139666250008381440> **Discord** <t:{discord_join}:R>\n"
                f"<:server_icon:1139666252000694272> **Servidor** <t:{server_join}:R>"
            ),
            inline=True
        )

        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(name="Roles", value=roles_text, inline=True)

        # === BOTONES ===
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Avatar", url=avatar_url, emoji="<:avatar_icon:1139666254001672192>"))
        if banner_url:
            view.add_item(discord.ui.Button(label="Banner", url=banner_url, emoji="<:banner_icon:1139666256002363392>"))

        await ctx.send(embed=embed, view=view)

    # =====================================================
    # AVATAR
    # =====================================================
    @commands.command(aliases=["pfp", "av"])
    async def avatar(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        embed = discord.Embed(title=f"Avatar de {member.display_name}", color=member.color or discord.Color.blurple())
        embed.set_image(url=member.display_avatar.url)
        embed.set_footer(text=f"ID: {member.id}")
        await ctx.send(embed=embed)

    # =====================================================
    # BANNER
    # =====================================================
    @commands.command()
    async def banner(self, ctx, user: discord.User = None):
        user = user or ctx.author
        user = await self.bot.fetch_user(user.id)
        if user.banner:
            embed = discord.Embed(title=f"Banner de {user.display_name}", color=discord.Color.blurple())
            embed.set_image(url=user.banner.url)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"**{user.display_name}** no tiene banner.")

    # =====================================================
    # SERVER INFO
    # =====================================================
    @commands.command(aliases=["serverinfo", "sv", "guild"])
    async def server(self, ctx):
        g = ctx.guild
        embed = discord.Embed(title=f"**{g.name}**", color=discord.Color.blue(), timestamp=datetime.now(timezone.utc))
        if g.icon: embed.set_thumbnail(url=g.icon.url)
        if g.banner: embed.set_image(url=g.banner.url)

        humanos = len([m for m in g.members if not m.bot])
        bots = g.member_count - humanos

        embed.add_field(name="ID", value=g.id, inline=True)
        embed.add_field(name="Dueño", value=g.owner.mention, inline=True)
        embed.add_field(name="Miembros", value=f"**{g.member_count}** total\n{humanos} humanos\n{bots} bots", inline=True)
        embed.add_field(name="Canales", value=f"{len(g.text_channels)} texto\n{len(g.voice_channels)} voz", inline=True)
        embed.add_field(name="Roles", value=len(g.roles), inline=True)
        embed.add_field(name="Boosts", value=f"Nivel {g.premium_tier}\n{g.premium_subscription_count} boosts", inline=True)
        embed.add_field(name="Creado", value=f"<t:{int(g.created_at.timestamp())}:R>", inline=True)

        await ctx.send(embed=embed)

    # =====================================================
    # ROLE INFO
    # =====================================================
    @commands.command(aliases=["ri"])
    async def roleinfo(self, ctx, role: discord.Role):
        embed = discord.Embed(title=f"Rol: {role.name}", color=role.color)
        embed.add_field(name="ID", value=role.id)
        embed.add_field(name="Miembros", value=len(role.members))
        embed.add_field(name="Mencionable", value="Sí" if role.mentionable else "No")
        embed.add_field(name="Creado", value=f"<t:{int(role.created_at.timestamp())}:R>")
        await ctx.send(embed=embed)

    # =====================================================
    # FIND USER
    # =====================================================
    @commands.command(aliases=["fu", "buscar"])
    async def finduser(self, ctx, *, nombre: str = None):
        if not nombre:
            return await ctx.send("Usa: `,finduser <nombre>`")
        resultados = [m for m in ctx.guild.members if nombre.lower() in m.display_name.lower()]
        if not resultados:
            return await ctx.send("No se encontraron usuarios.")
        embed = discord.Embed(title=f"Resultados para: {nombre}", color=discord.Color.gold())
        embed.description = "\n".join([f"{m.mention} (`{m.display_name}`)" for m in resultados[:15]])
        await ctx.send(embed=embed)

    # =====================================================
    # PING MEJORADO: Latencia + Velocidad de Internet
    # =====================================================
    @commands.command()
    async def ping(self, ctx):
        embed = discord.Embed(title="Calculando velocidad...", color=discord.Color.orange())
        msg = await ctx.send(embed=embed)

        # Latencia del WebSocket
        ws_latency = round(self.bot.latency * 1000)

        # Latencia real (mensaje enviado → editado)
        before = datetime.utcnow()
        await msg.edit(content=None, embed=embed)
        after = datetime.utcnow()
        msg_latency = round((after - before).total_seconds() * 1000)

        # Estado de conexión
        status = "Excelente" if msg_latency < 150 else "Bueno" if msg_latency < 300 else "Lento"

        embed = discord.Embed(title="Velocidad de Internet", color=discord.Color.green() if status == "Excelente" else discord.Color.yellow() if status == "Bueno" else discord.Color.red())
        embed.add_field(name="WebSocket", value=f"{ws_latency}ms", inline=True)
        embed.add_field(name="Mensaje", value=f"{msg_latency}ms", inline=True)
        embed.add_field(name="Estado", value=status, inline=True)
        embed.set_footer(text="Tiempo real de respuesta del bot")

        await msg.edit(embed=embed)

    # =====================================================
    # 8BALL
    # =====================================================
    @commands.command(aliases=["8ball", "pregunta", "bola"])
    async def _8ball(self, ctx, *, pregunta: str = None):
        if not pregunta:
            return await ctx.send("Haz una pregunta.")
        respuestas = [
            "Sí, totalmente.", "Sin duda.", "Claro que sí.",
            "No lo creo.", "Ni de broma.", "Imposible.",
            "Tal vez...", "Pregunta de nuevo.", "No puedo decirlo ahora."
        ]
        respuesta = random.choice(respuestas)
        embed = discord.Embed(title="Bola Mágica", color=discord.Color.purple())
        embed.add_field(name="Pregunta", value=pregunta, inline=False)
        embed.add_field(name="Respuesta", value=respuesta, inline=False)
        await ctx.send(embed=embed)

# =====================================================
# SETUP
# =====================================================
async def setup(bot):
    await bot.add_cog(Utils(bot))
