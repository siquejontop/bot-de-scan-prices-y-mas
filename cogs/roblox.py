import discord
from discord.ext import commands
import aiohttp
import asyncio

class RobloxCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = None

    async def cog_load(self):
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        if self.session:
            await self.session.close()

    async def safe_request(self, method, url, **kwargs):
        for attempt in range(3):
            try:
                async with self.session.request(method, url, **kwargs) as resp:
                    if resp.status == 429:
                        retry_after = int(resp.headers.get("Retry-After", 5))
                        await asyncio.sleep(retry_after)
                        continue
                    if resp.status != 200:
                        return None, f"Error HTTP {resp.status}"
                    return await resp.json(), None
            except Exception as e:
                return None, f"Error de conexión: {str(e)}"
        return None, "Demasiadas solicitudes. Intenta más tarde."

    @commands.command(name="roblox", aliases=["rblx", "rbx"])
    async def roblox_profile(self, ctx, *, args: str = None):
        """Muestra un perfil detallado de Roblox con opciones avanzadas.
        Uso: !roblox <username> [--friends|--groups|--badges]
        Ejemplo: !roblox Builderman --friends"""
        if not args:
            await ctx.send("❌ Usa: `,roblox <username> [--friends|--groups|--badges]`")
            return

        # Separar username y argumentos
        parts = args.split()
        username = parts[0]
        options = [p.lower() for p in parts[1:] if p.startswith("--")]

        # Obtener ID del usuario
        search_url = "https://users.roblox.com/v1/usernames/users"
        search_payload = {"usernames": [username], "excludeBannedUsers": False}
        data, error = await self.safe_request("POST", search_url, json=search_payload)
        if error or not data.get("data"):
            await ctx.send(f"❌ Usuario '{username}' no encontrado o error: {error}")
            return
        user_id = data["data"][0]["id"]

        # Datos del perfil
        profile_url = f"https://users.roblox.com/v1/users/{user_id}"
        profile_data, error = await self.safe_request("GET", profile_url)
        if error:
            await ctx.send(f"❌ Error al obtener perfil: {error}")
            return

        # Thumbnail y banner
        thumbnail_url = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=420x420&format=Png&isCircular=false"
        thumb_data, error = await self.safe_request("GET", thumbnail_url)
        avatar_url = thumb_data["data"][0]["imageUrl"] if thumb_data and thumb_data.get("data") else None

        banner_url = f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=420x420&format=Png&isCircular=false"
        banner_data, error = await self.safe_request("GET", banner_url)
        banner_url = banner_data["data"][0]["imageUrl"] if banner_data and banner_data.get("data") else None

        # Estadísticas
        stats_url = f"https://users.roblox.com/v1/users/{user_id}/status"
        stats_data, error = await self.safe_request("GET", stats_url)
        status = stats_data.get("status", "No disponible") if stats_data else "No disponible"

        # Amigos
        friends_url = f"https://friends.roblox.com/v1/users/{user_id}/friends/count"
        friends_data, error = await self.safe_request("GET", friends_url)
        friends_count = friends_data.get("count", 0) if friends_data else 0

        # Seguidores y siguiente
        followers_url = f"https://friends.roblox.com/v1/users/{user_id}/followers/count"
        followers_data, error = await self.safe_request("GET", followers_url)
        followers_count = followers_data.get("count", 0) if followers_data else 0

        following_url = f"https://friends.roblox.com/v1/users/{user_id}/followings/count"
        following_data, error = await self.safe_request("GET", following_url)
        following_count = following_data.get("count", 0) if following_data else 0

        # Badges
        badges_url = f"https://badges.roblox.com/v1/users/{user_id}/badges"
        badges_data, error = await self.safe_request("GET", badges_url)
        badges = [badge["name"] for badge in badges_data.get("data", [])[:5]] if badges_data else []

        # Historial de nombres
        name_history_url = f"https://users.roblox.com/v1/users/{user_id}/username-history?limit=10&sortOrder=Desc"
        name_history_data, error = await self.safe_request("GET", name_history_url)
        name_history = [entry["name"] for entry in name_history_data.get("data", [])] if name_history_data else []

        # Grupos
        groups_url = f"https://groups.roblox.com/v1/users/{user_id}/groups/roles"
        groups_data, error = await self.safe_request("GET", groups_url)
        groups = [{"name": g["group"]["name"], "role": g["role"]["name"]} for g in groups_data.get("data", [])[:10]] if groups_data else []

        # Juegos favoritos (basado en visitas recientes, aproximado)
        games_url = f"https://games.roblox.com/v1/games?creatorId={user_id}&sortOrder=Desc&limit=3"
        games_data, error = await self.safe_request("GET", games_url)
        games = [f"{game['name']} (ID: {game['id']})" for game in games_data.get("data", [])] if games_data else []

        # Crear embeds paginados
        pages = []
        current_page = discord.Embed(title=f"👤 Perfil de {profile_data['name']}", color=discord.Color.blue())
        current_page.add_field(name="ID", value=profile_data['id'], inline=True)
        current_page.add_field(name="Creado", value=profile_data['created'].split('T')[0], inline=True)
        current_page.add_field(name="Estado", value=status, inline=True)
        current_page.add_field(name="Amigos", value=friends_count, inline=True)
        current_page.add_field(name="Seguidores", value=followers_count, inline=True)
        current_page.add_field(name="Siguiendo", value=following_count, inline=True)
        if avatar_url:
            current_page.set_thumbnail(url=avatar_url)
        if banner_url:
            current_page.set_image(url=banner_url)
        pages.append(current_page)

        if "--badges" in options or not options:
            badge_page = discord.Embed(title="🏅 Badges", color=discord.Color.gold())
            badge_page.add_field(name="Badges", value="\n".join(badges) or "Sin badges", inline=False)
            pages.append(badge_page)

        if "--friends" in options or not options:
            friend_page = discord.Embed(title="👥 Amigos", color=discord.Color.green())
            friend_page.add_field(name="Total", value=friends_count, inline=False)
            pages.append(friend_page)  # Podrías expandir esto con una API de amigos completa si está disponible

        if "--groups" in options or not options:
            group_page = discord.Embed(title="🏰 Grupos", color=discord.Color.purple())
            group_page.add_field(name="Grupos", value="\n".join([f"{g['name']} - {g['role']}" for g in groups]) or "Sin grupos", inline=False)
            pages.append(group_page)

        if name_history:
            history_page = discord.Embed(title="📜 Historial de Nombres", color=discord.Color.orange())
            history_page.add_field(name="Nombres", value="\n".join(name_history), inline=False)
            pages.append(history_page)

        if games:
            game_page = discord.Embed(title="🎮 Juegos Favoritos", color=discord.Color.red())
            game_page.add_field(name="Juegos", value="\n".join(games), inline=False)
            pages.append(game_page)

        # Paginación
        current_page = 0
        message = await ctx.send(embed=pages[current_page])
        if len(pages) > 1:
            await message.add_reaction("⬅️")
            await message.add_reaction("➡️")

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️"] and reaction.message.id == message.id

            while True:
                try:
                    reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
                    await message.remove_reaction(reaction.emoji, user)
                    if str(reaction.emoji) == "➡️" and current_page < len(pages) - 1:
                        current_page += 1
                        await message.edit(embed=pages[current_page])
                    elif str(reaction.emoji) == "⬅️" and current_page > 0:
                        current_page -= 1
                        await message.edit(embed=pages[current_page])
                except asyncio.TimeoutError:
                    await message.clear_reactions()
                    break

async def setup(bot):
    await bot.add_cog(RobloxCog(bot))
