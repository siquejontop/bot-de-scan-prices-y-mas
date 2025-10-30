import discord
from discord.ext import commands
from datetime import datetime, timezone

# Idioma global por defecto
bot_language = "es"

# =====================================================
# Traducciones (simplificadas para el nuevo diseño)
# =====================================================
translations = {
    "es": {
        "no_badges": "Sin insignias",
        "no_roles": "Sin roles",
        "no_custom_status": "Ninguno",
        "no_about": "No tiene descripción."
    },
    "en": {
        "no_badges": "No badges",
        "no_roles": "No roles",
        "no_custom_status": "None",
        "no_about": "No description."
    }
}

class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # =====================================================
    # Avatar
    # =====================================================
    @commands.command(aliases=["pfp"])
    async def avatar(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        embed = discord.Embed(
            title=f"Avatar de {member.display_name}",
            color=member.color,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_image(url=member.display_avatar.url)
        await ctx.send(embed=embed)

    # =====================================================
    # Banner
    # =====================================================
    @commands.command()
    async def banner(self, ctx, user: discord.User = None):
        user = user or ctx.author
        user = await self.bot.fetch_user(user.id)
        if user.banner:
            embed = discord.Embed(
                title=f"Banner de {user.display_name}",
                color=discord.Color.blurple(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_image(url=user.banner.url)
            embed.set_footer(text=f"Solicitado por {ctx.author}", icon_url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"{user.display_name} no tiene banner.")

    # =====================================================
    # USER INFO – ESTILO DISCORD OFICIAL
    # =====================================================
    @commands.command(aliases=["userinfo", "ui", "user", "w"])
    async def usuario(self, ctx, member: discord.Member = None):
        lang = translations[bot_language]
        member = member or ctx.author
        user = member._user

        # === BADGES ===
        badges = []
        flags = user.public_flags
        badge_emojis = {
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
        for flag, emoji in badge_emojis.items():
            if getattr(flags, flag, False):
                badges.append(emoji)
        if user.premium_since:
            badges.append("<:nitro:1139666214857199616>")
        badges_text = " ".join(badges) if badges else lang["no_badges"]

        # === ESTADO ===
        status_icons = {
            discord.Status.online: "<:status_online:1139666228908093440>",
            discord.Status.idle: "<:status_idle:1139666230808150016>",
            discord.Status.dnd: "<:status_dnd:1139666226869698560>",
            discord.Status.offline: "<:status_offline:1139666228861976576>"
        }
        status_emoji = status_icons.get(member.status, "<:status_offline:1139666228861976576>")
        status_text = str(member.status).capitalize()

        # === DISPOSITIVOS ===
        devices = []
        if member.desktop_status != discord.Status.offline:
            devices.append("<:desktop:1139666242854236160>")
        if member.mobile_status != discord.Status.offline:
            devices.append("<:mobile:1139666244859092992>")
        if member.web_status != discord.Status.offline:
            devices.append("<:web:1139666246851321856>")
        devices_text = " ".join(devices) if devices else "<:status_offline:1139666228861976576>"

        # === CUSTOM STATUS ===
        custom_status = None
        for act in member.activities:
            if act.type == discord.ActivityType.custom:
                emoji = str(act.emoji) + " " if act.emoji else ""
                custom_status = f"{emoji}{act.name}" if act.name else None
                break
        custom_status = custom_status or lang["no_custom_status"]

        # === ROLES ===
        roles = [role.mention for role in member.roles[::-1][:-1]]  # Sin @everyone
        roles_text = " ".join(roles[:25]) + ("..." if len(roles) > 25 else "") if roles else lang["no_roles"]

        # === FECHAS ===
        discord_join = int(user.created_at.timestamp())
        server_join = int(member.joined_at.timestamp()) if member.joined_at else "?"

        # === BANNER & AVATAR ===
        banner_url = user.banner.url if user.banner else None
        avatar_url = member.display_avatar.url

        # === ABOUT ME ===
        about = user.about or lang["no_about"]

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

        # === CAMPOS ===
        embed.add_field(
            name="",
            value=(
                f"{status_emoji} **Status**\n"
                f"{status_emoji} {status_text}\n"
                f"{devices_text} {' '.join(devices)}\n\n"
                f"**Custom Status**\n{custom_status}\n\n"
                f"**Badges**\n{badges_text}"
            ),
            inline=False
        )

        embed.add_field(
            name="Joined",
            value=(
                f"<:discord_logo:1139666250008381440> **Discord** <t:{discord_join}:R>\n"
                f"<:server_icon:1139666252000694272> **Server** <t:{server_join}:R>"
            ),
            inline=True
        )

        embed.add_field(name="\u200b", value="\u200b", inline=True)  # Espaciador

        embed.add_field(
            name="Roles",
            value=roles_text,
            inline=True
        )

        # === BOTONES ===
        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            label="User Avatar", 
            url=avatar_url, 
            emoji="<:avatar_icon:1139666254001672192>"
        ))
        if banner_url:
            view.add_item(discord.ui.Button(
                label="User Banner", 
                url=banner_url, 
                emoji="<:banner_icon:1139666256002363392>"
            ))

        await ctx.send(embed=embed, view=view)

    # =====================================================
    # Server Info
    # =====================================================
    @commands.command(aliases=["serverinfo", "guildinfo", "sv"])
    async def server(self, ctx):
        guild = ctx.guild
        embed = discord.Embed(
            title=f"Información del servidor **{guild.name}**",
            color=discord.Color.blue(),
            timestamp=datetime.now(timezone.utc)
        )
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        if guild.banner:
            embed.set_image(url=guild.banner.url)

        total = guild.member_count
        humans = len([m for m in guild.members if not m.bot])
        bots = total - humans

        embed.add_field(name="ID", value=guild.id, inline=True)
        embed.add_field(name="Dueño", value=guild.owner.mention, inline=True)
        embed.add_field(name="Región", value=str(guild.preferred_locale).upper(), inline=True)
        embed.add_field(name="Miembros", value=f"Total: **{total}**\n{humans}\n{bots}", inline=True)
        embed.add_field(name="Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="Canales", value=f"Texto: {len(guild.text_channels)}\nVoz: {len(guild.voice_channels)}\nCategorías: {len(guild.categories)}", inline=True)
        embed.add_field(name="Boosts", value=f"Nivel: {guild.premium_tier}\nTotal: {guild.premium_subscription_count}", inline=True)
        embed.add_field(name="Creado", value=f"<t:{int(guild.created_at.timestamp())}:R>", inline=True)
        await ctx.send(embed=embed)

    # =====================================================
    # Role Info
    # =====================================================
    @commands.command()
    async def roleinfo(self, ctx, role: discord.Role):
        embed = discord.Embed(
            title=f"Info del rol {role.name}",
            color=role.color
        )
        embed.add_field(name="ID", value=role.id, inline=False)
        embed.add_field(name="Mencionable", value="Sí" if role.mentionable else "No", inline=False)
        embed.add_field(name="Miembros", value=len(role.members), inline=False)
        embed.add_field(name="Creado", value=role.created_at.strftime("%d/%m/%Y %H:%M"), inline=False)
        await ctx.send(embed=embed)

    # =====================================================
    # Bot Info
    # =====================================================
    @commands.command()
    async def botinfo(self, ctx):
        embed = discord.Embed(
            title="Información del Bot",
            color=discord.Color.purple(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="Nombre", value=self.bot.user.name, inline=True)
        embed.add_field(name="Tag", value=f"#{self.bot.user.discriminator}", inline=True)
        embed.add_field(name="Developer", value="sq3j", inline=True)
        embed.add_field(name="Servidores", value=len(self.bot.guilds), inline=True)
        embed.add_field(name="Usuarios", value=len(self.bot.users), inline=True)
        embed.add_field(name="Creación", value=self.bot.user.created_at.strftime("%d/%m/%Y %H:%M"), inline=False)
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        await ctx.send(embed=embed)

    # =====================================================
    # Find User
    # =====================================================
    @commands.command()
    async def finduser(self, ctx, *, name: str = None):
        if not name:
            return await ctx.send("Formato: `$finduser <nombre>`")
        results = [m for m in ctx.guild.members if name.lower() in m.display_name.lower() or name.lower() in m.name.lower()]
        if not results:
            return await ctx.send("No encontré usuarios con ese nombre.")
        embed = discord.Embed(
            title=f"Usuarios encontrados con: {name}",
            description="\n".join([f"{m.mention} (`{m}`)" for m in results[:15]]),
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)

    # =====================================================
    # Bot Language
    # =====================================================
    @commands.command(name="botlang")
    @commands.is_owner()
    async def botlang(self, ctx, lang: str):
        global bot_language
        lang = lang.lower()
        if lang not in translations:
            return await ctx.send("Idioma no soportado. Usa `es` o `en`.")
        bot_language = lang
        await ctx.send(f"Idioma cambiado a **{'Español' if lang == 'es' else 'English'}**.")

# =====================================================
# Setup
# =====================================================
async def setup(bot):
    await bot.add_cog(Utils(bot))
