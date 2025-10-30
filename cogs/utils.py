import discord
from discord.ext import commands
from datetime import datetime, timezone
import aiohttp  # Necesario para get_title_from_url

# Idioma global por defecto
bot_language = "es"

# =====================================================
# Traducciones
# =====================================================
translations = {
    "es": {
        "lang_changed": "Idioma global cambiado a **Español**.",
        "lang_invalid": "Idioma no soportado. Usa es o en.",
        # Avatar
        "avatar_title": "Avatar de {name}",
        # Banner
        "banner_title": "Banner de {name}",
        "banner_none": "{name} no tiene banner.",
        # User Info
        "user_not_found": "Usuario no encontrado",
        "user_not_found_desc": "Debes mencionar un usuario o poner un **ID válido** que esté en este servidor.",
        "userinfo_title": "Información de {name}",
        "userinfo_id": "ID",
        "userinfo_bot": "Bot",
        "userinfo_created": "Cuenta creada",
        "userinfo_joined": "Entró al servidor",
        "userinfo_roles": "Roles ({count})",
        "userinfo_status": "Estado",
        "userinfo_activity": "Actividad",
        "userinfo_custom": "Estado personalizado",
        "userinfo_none": "Ninguno",
        # Estados
        "status_online": "En línea",
        "status_offline": "Desconectado",
        "status_idle": "Ausente",
        "status_dnd": "No molestar",
        "status_unknown": "Desconocido",
        "device_desktop": "Desktop",
        "device_mobile": "Móvil",
        "device_web": "Web",
        "device_none": "No conectado",
        # Server Info
        "server_title": "Información del servidor **{name}**",
        "server_id": "ID",
        "server_owner": "Dueño",
        "server_region": "Región",
        "server_members": "Miembros",
        "server_roles": "Roles",
        "server_channels": "Canales",
        "server_boosts": "Boosts",
        "server_created": "Creado el",
        # Role Info
        "role_title": "Info del rol {name}",
        "role_id": "ID",
        "role_mentionable": "Mencionable",
        "role_members": "Miembros con este rol",
        "role_created": "Creado el",
        # Bot Info
        "botinfo_title": "Información del Bot",
        "botinfo_name": "Nombre",
        "botinfo_tag": "Tag",
        "botinfo_dev": "Developer",
        "botinfo_servers": "Servidores",
        "botinfo_users": "Usuarios",
        "botinfo_created": "Creación",
        # Find User
        "finduser_error": "Uso incorrecto de finduser",
        "finduser_usage": "Formato correcto:\n$finduser <nombre>",
        "finduser_none": "No encontré usuarios con ese nombre.",
        "finduser_title": "Usuarios encontrados con: {name}"
    },
    "en": {
        "lang_changed": "Global language changed to **English**.",
        "lang_invalid": "Unsupported language. Use es or en.",
        # Avatar
        "avatar_title": "Avatar of {name}",
        # Banner
        "banner_title": "Banner of {name}",
        "banner_none": "{name} has no banner.",
        # User Info
        "user_not_found": "User not found",
        "user_not_found_desc": "You must mention a user or provide a valid **ID** from this server.",
        "userinfo_title": "Information of {name}",
        "userinfo_id": "ID",
        "userinfo_bot": "Bot",
        "userinfo_created": "Account created",
        "userinfo_joined": "Joined the server",
        "userinfo_roles": "Roles ({count})",
        "userinfo_status": "Status",
        "userinfo_activity": "Activity",
        "userinfo_custom": "Custom Status",
        "userinfo_none": "None",
        # States
        "status_online": "Online",
        "status_offline": "Offline",
        "status_idle": "Idle",
        "status_dnd": "Do Not Disturb",
        "status_unknown": "Unknown",
        "device_desktop": "Desktop",
        "device_mobile": "Mobile",
        "device_web": "Web",
        "device_none": "Not connected",
        # Server Info
        "server_title": "Server Info **{name}**",
        "server_id": "ID",
        "server_owner": "Owner",
        "server_region": "Region",
        "server_members": "Members",
        "server_roles": "Roles",
        "server_channels": "Channels",
        "server_boosts": "Boosts",
        "server_created": "Created at",
        # Role Info
        "role_title": "Role Info {name}",
        "role_id": "ID",
        "role_mentionable": "Mentionable",
        "role_members": "Members with this role",
        "role_created": "Created at",
        # Bot Info
        "botinfo_title": "Bot Information",
        "botinfo_name": "Name",
        "botinfo_tag": "Tag",
        "botinfo_dev": "Developer",
        "botinfo_servers": "Servers",
        "botinfo_users": "Users",
        "botinfo_created": "Created at",
        # Find User
        "finduser_error": "Incorrect use of finduser",
        "finduser_usage": "Correct format:\n$finduser <name>",
        "finduser_none": "No users found with that name.",
        "finduser_title": "Users found with: {name}"
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
        lang = translations[bot_language]
        member = member or ctx.author
        embed = discord.Embed(
            title=lang["avatar_title"].format(name=member.display_name),
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
        lang = translations[bot_language]
        user = user or ctx.author
        user = await self.bot.fetch_user(user.id)
        if user.banner:
            embed = discord.Embed(
                title=lang["banner_title"].format(name=user.display_name),
                color=discord.Color.blurple(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_image(url=user.banner.url)
            embed.set_footer(text=f"{ctx.author}", icon_url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)
        else:
            await ctx.send(lang["banner_none"].format(name=user.display_name))

    # =====================================================
    # User Info (CORREGIDO: aliases y MemberConverter)
    # =====================================================
    @commands.command(aliases=["userinfo", "ui", "user", "w"])
    async def usuario(self, ctx, member: discord.Member = None):
        lang = translations[bot_language]
        member = member or ctx.author

        # Roles
        roles = [role.mention for role in member.roles if role != ctx.guild.default_role]
        roles_display = ", ".join(roles) if roles else lang["userinfo_none"]
        joined_at = member.joined_at.strftime("%d/%m/%Y %H:%M") if member.joined_at else "?"
        created_at = member.created_at.strftime("%d/%m/%Y %H:%M")

        # Estados
        status_map = {
            "online": lang["status_online"],
            "offline": lang["status_offline"],
            "idle": lang["status_idle"],
            "dnd": lang["status_dnd"]
        }
        status = status_map.get(str(member.status), lang["status_unknown"])

        dispositivos = []
        if str(member.desktop_status) != "offline":
            dispositivos.append(f"{lang['device_desktop']}: {status_map.get(str(member.desktop_status), lang['status_unknown'])}")
        if str(member.mobile_status) != "offline":
            dispositivos.append(f"{lang['device_mobile']}: {status_map.get(str(member.mobile_status), lang['status_unknown'])}")
        if str(member.web_status) != "offline":
            dispositivos.append(f"{lang['device_web']}: {status_map.get(str(member.web_status), lang['status_unknown'])}")
        dispositivo_text = "\n".join(dispositivos) if dispositivos else lang["device_none"]

        embed = discord.Embed(
            title=lang["userinfo_title"].format(name=member.display_name),
            color=discord.Color.blurple(),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name=lang["userinfo_id"], value=member.id, inline=True)
        embed.add_field(name=lang["userinfo_bot"], value="Sí" if member.bot else "No", inline=True)
        embed.add_field(name=lang["userinfo_created"], value=created_at, inline=False)
        embed.add_field(name=lang["userinfo_joined"], value=joined_at, inline=False)
        embed.add_field(name=lang["userinfo_roles"].format(count=len(roles)), value=roles_display, inline=False)
        embed.add_field(name=lang["userinfo_status"], value=f"{status}\n\n{dispositivo_text}", inline=False)

        # Custom status
        custom_status_text = None
        for actividad in member.activities:
            if actividad.type == discord.ActivityType.custom and actividad.name:
                custom_status_text = actividad.name
                break
        embed.add_field(
            name=lang["userinfo_custom"],
            value=custom_status_text or lang["userinfo_none"],
            inline=False
        )
        await ctx.send(embed=embed)

    # =====================================================
    # Server Info
    # =====================================================
    @commands.command(aliases=["serverinfo", "guildinfo", "sv"])
    async def server(self, ctx):
        lang = translations[bot_language]
        guild = ctx.guild
        embed = discord.Embed(
            title=lang["server_title"].format(name=guild.name),
            color=discord.Color.blue(),
            timestamp=datetime.now(timezone.utc)
        )
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        if guild.banner:
            embed.set_image(url=guild.banner.url)

        embed.add_field(name=lang["server_id"], value=guild.id, inline=True)
        embed.add_field(name=lang["server_owner"], value=guild.owner.mention, inline=True)
        embed.add_field(name=lang["server_region"], value=str(guild.preferred_locale).upper(), inline=True)

        total_members = guild.member_count
        humans = len([m for m in guild.members if not m.bot])
        bots = total_members - humans
        embed.add_field(name=lang["server_members"], value=f"Total: **{total_members}**\n{humans}\n{bots}", inline=True)
        embed.add_field(name=lang["server_roles"], value=len(guild.roles), inline=True)
        embed.add_field(name=lang["server_channels"], value=f"Texto: {len(guild.text_channels)}\nVoz: {len(guild.voice_channels)}\nCategorías: {len(guild.categories)}", inline=True)
        embed.add_field(name=lang["server_boosts"], value=f"Nivel: {guild.premium_tier}\nTotal: {guild.premium_subscription_count}", inline=True)
        embed.add_field(name=lang["server_created"], value=f"<t:{int(guild.created_at.timestamp())}:R>", inline=True)
        await ctx.send(embed=embed)

    # =====================================================
    # Role Info
    # =====================================================
    @commands.command()
    async def roleinfo(self, ctx, role: discord.Role):
        lang = translations[bot_language]
        embed = discord.Embed(
            title=lang["role_title"].format(name=role.name),
            color=role.color
        )
        embed.add_field(name=lang["role_id"], value=role.id, inline=False)
        embed.add_field(name=lang["role_mentionable"], value="Sí" if role.mentionable else "No", inline=False)
        embed.add_field(name=lang["role_members"], value=len(role.members), inline=False)
        embed.add_field(name=lang["role_created"], value=role.created_at.strftime("%d/%m/%Y %H:%M"), inline=False)
        await ctx.send(embed=embed)

    # =====================================================
    # Bot Info
    # =====================================================
    @commands.command()
    async def botinfo(self, ctx):
        lang = translations[bot_language]
        embed = discord.Embed(
            title=lang["botinfo_title"],
            color=discord.Color.purple(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name=lang["botinfo_name"], value=self.bot.user.name, inline=True)
        embed.add_field(name=lang["botinfo_tag"], value=f"#{self.bot.user.discriminator}", inline=True)
        embed.add_field(name=lang["botinfo_dev"], value="sq3j", inline=True)
        embed.add_field(name=lang["botinfo_servers"], value=len(self.bot.guilds), inline=True)
        embed.add_field(name=lang["botinfo_users"], value=len(self.bot.users), inline=True)
        embed.add_field(name=lang["botinfo_created"], value=self.bot.user.created_at.strftime("%d/%m/%Y %H:%M"), inline=False)
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        await ctx.send(embed=embed)

    # =====================================================
    # Find User
    # =====================================================
    @commands.command()
    async def finduser(self, ctx, *, name: str = None):
        lang = translations[bot_language]
        if not name:
            embed = discord.Embed(
                title=lang["finduser_error"],
                description=lang["finduser_usage"],
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        results = [m for m in ctx.guild.members if name.lower() in m.display_name.lower() or name.lower() in m.name.lower()]
        if not results:
            await ctx.send(lang["finduser_none"])
            return

        embed = discord.Embed(
            title=lang["finduser_title"].format(name=name),
            description="\n".join([f"{m.mention} (`{m}`)" for m in results[:15]]),
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)

    # =====================================================
    # Bot Language (solo owner)
    # =====================================================
    @commands.command(name="botlang")
    @commands.is_owner()
    async def botlang(self, ctx, lang: str):
        global bot_language
        lang = lang.lower()
        if lang not in translations:
            await ctx.send(translations[bot_language]["lang_invalid"])
            return
        bot_language = lang
        await ctx.send(translations[bot_language]["lang_changed"])

    # =====================================================
    # Extraer título de links
    # =====================================================
    async def get_title_from_url(self, url: str):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        if "spotify.com" in url:
                            start = text.find("<title>")
                            end = text.find("</title>")
                            if start != -1 and end != -1:
                                title = text[start+7:end]
                                return title.replace(" | Spotify", "").strip()
                        if "youtube.com" in url or "youtu.be" in url:
                            start = text.find("<title>")
                            end = text.find("</title>")
                            if start != -1 and end != -1:
                                title = text[start+7:end]
                                return title.replace(" - YouTube", "").strip()
        except Exception as e:
            print(f"Error obteniendo título: {e}")
        return None

    # =====================================================
    # Establecer estado del bot
    # =====================================================
    @commands.command()
    @commands.is_owner()
    async def setstatus(self, ctx, estado: str = None, tipo: str = None, *, mensaje: str = None):
        estados = {
            "online": discord.Status.online,
            "dnd": discord.Status.dnd,
            "idle": discord.Status.idle,
            "invisible": discord.Status.invisible
        }
        tipos = {
            "playing": discord.ActivityType.playing,
            "listening": discord.ActivityType.listening,
            "watching": discord.ActivityType.watching,
            "streaming": discord.ActivityType.streaming
        }

        if not estado or estado.lower() not in estados:
            return await ctx.send("Estados válidos: online, dnd, idle, invisible")
        if not tipo or tipo.lower() not in tipos:
            return await ctx.send("Tipos válidos: playing, listening, watching, streaming")
        if not mensaje:
            mensaje = "Sin actividad"

        url = None
        display_text = mensaje

        if mensaje.startswith("http://") or mensaje.startswith("https://"):
            url = mensaje
            title = await self.get_title_from_url(url)
            display_text = title or "Actividad personalizada"

        if tipo.lower() == "streaming":
            actividad = discord.Streaming(name=display_text, url=url or "https://twitch.tv/discord")
        else:
            actividad = discord.Activity(type=tipos[tipo.lower()], name=display_text)

        await self.bot.change_presence(status=estados[estado.lower()], activity=actividad)

        embed = discord.Embed(
            title="Estado actualizado",
            color=discord.Color.green()
        )
        embed.add_field(name="Estado", value=estado.lower(), inline=True)
        embed.add_field(name="Tipo", value=tipo.lower(), inline=True)
        embed.add_field(name="Mensaje", value=display_text, inline=False)
        if url:
            embed.add_field(name="Link", value=url, inline=False)
        embed.set_footer(text=f"Comando ejecutado por {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)


# =====================================================
# Setup obligatorio
# =====================================================
async def setup(bot):
    await bot.add_cog(Utils(bot))
