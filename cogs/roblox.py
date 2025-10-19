import discord
from discord.ext import commands
import aiohttp  # Para hacer requests HTTP asíncronos

class RobloxCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="roblox", aliases=["rblx", "profile"])
    async def roblox_profile(self, ctx, *, username: str):
        """
        Muestra el perfil de un usuario de Roblox.
        Uso: !roblox <username>
        Ejemplo: !roblox Builderman
        """
        # Pasos para obtener el ID del usuario por username
        async with aiohttp.ClientSession() as session:
            # Endpoint para buscar usuario por username exacto
            search_url = f"https://users.roblox.com/v1/usernames/users"
            search_payload = {"usernames": [username], "excludeBannedUsers": False}
            async with session.post(search_url, json=search_payload) as resp:
                if resp.status != 200:
                    await ctx.send(f"❌ Error al buscar usuario: {resp.status}. Verifica el username.")
                    return
                data = await resp.json()
                if not data.get("data"):
                    await ctx.send(f"❌ Usuario '{username}' no encontrado en Roblox.")
                    return
                user = data["data"][0]
                user_id = user["id"]

            # Ahora obtener el perfil completo con el ID
            profile_url = f"https://users.roblox.com/v1/users/{user_id}"
            async with session.get(profile_url) as resp:
                if resp.status != 200:
                    await ctx.send(f"❌ Error al obtener perfil: {resp.status}.")
                    return
                profile_data = await resp.json()

            # Obtener la imagen de perfil (thumbnail)
            thumbnail_url = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=150x150&format=Png&isCircular=false"
            async with session.get(thumbnail_url) as resp:
                if resp.status == 200:
                    thumb_data = await resp.json()
                    avatar_url = thumb_data["data"][0]["imageUrl"] if thumb_data.get("data") else None
                else:
                    avatar_url = None

        # Crear el embed con la info
        embed = discord.Embed(title=f"👤 Perfil de Roblox: {profile_data['name']}", color=discord.Color.blue())
        embed.add_field(name="ID de Usuario", value=profile_data['id'], inline=True)
        embed.add_field(name="Descripción", value=profile_data.get('description', 'No disponible'), inline=False)
        embed.add_field(name="Creado el", value=profile_data['created'].split('T')[0], inline=True)
        embed.add_field(name="Verificado", value="Sí" if profile_data.get('isBanned') == False and profile_data.get('hasVerifiedBadge') else "No", inline=True)
        
        # Agregar la foto de perfil
        if avatar_url:
            embed.set_thumbnail(url=avatar_url)
        
        # Agregar enlace al perfil
        embed.add_field(name="Perfil Completo", value=f"[Ver en Roblox](https://www.roblox.com/users/{user_id}/profile)", inline=False)
        
        embed.set_footer(text="Datos obtenidos de la API oficial de Roblox")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(RobloxCog(bot))
