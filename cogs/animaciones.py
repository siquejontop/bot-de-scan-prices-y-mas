import discord
from discord.ext import commands
from discord import app_commands
import random
import motor.motor_asyncio
import aiohttp
import os

# === Configuración MongoDB ===
mongo_uri = os.getenv("MONGO_URI")
if mongo_uri:
    client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
    db = client["nekotina_clone"]
    interacciones_db = db["interacciones"]
else:
    interacciones_db = None
    print("⚠️ MongoDB no configurado, las estadísticas no se guardarán.")


# === Diccionario de acciones ===
acciones = {
    "kiss": {
        "desc": "💋 **{a}** besó a **{b}** 💞",
        "color": discord.Color.pink(),
        "gifs": [
            "https://media1.tenor.com/m/kmxEaVuW8AoAAAAC/kiss-gentle-kiss.gif",
        ]
    },
    "hug": {
        "desc": "🤗 **{a}** abrazó a **{b}** 💞",
        "color": discord.Color.blurple(),
        "gifs": [
            "https://media.tenor.com/2roX3uxz_68AAAAC/anime-hug.gif",
            "https://media.tenor.com/Wx9IEmZZXSoAAAAC/hug-anime.gif",
            "https://media.tenor.com/eTjX0EYcV1kAAAAC/hug-anime.gif",
            "https://media.tenor.com/Sdw6kN9nHysAAAAC/hug-cute.gif",
            "https://media.tenor.com/0K1Qv6lCQzYAAAAC/anime-hug-love.gif",
        ]
    },
    "pat": {
        "desc": "✨ **{a}** acarició a **{b}** 🥺",
        "color": discord.Color.gold(),
        "gifs": [
            "https://media.tenor.com/AW5zk8FfGnoAAAAC/headpat.gif",
            "https://media.tenor.com/MYjCChfTbkoAAAAC/anime-headpat.gif",
            "https://media.tenor.com/XgEMy7QDb0AAAAAC/anime-pat.gif",
            "https://media.tenor.com/Rm5yL4kD45sAAAAC/pat-anime.gif",
        ]
    },
    "slap": {
        "desc": "👋 **{a}** abofeteó a **{b}** 😡",
        "color": discord.Color.red(),
        "gifs": [
            "https://media.tenor.com/vYFJYVgY8qsAAAAC/slap-anime.gif",
            "https://media.tenor.com/GfSX-u7VGM4AAAAC/slap.gif",
            "https://media.tenor.com/XiYuUqzJdLwAAAAC/anime-girl-slap.gif",
            "https://media.tenor.com/F4vA1z_9OKoAAAAC/anime-hit.gif",
        ]
    },
    "bite": {
        "desc": "🩸 **{a}** mordió a **{b}** 😳",
        "color": discord.Color.dark_red(),
        "gifs": [
            "https://media.tenor.com/L8j36e0cU6IAAAAC/anime-bite.gif",
            "https://media.tenor.com/ZtNU3M6V4aUAAAAC/anime-vampire-bite.gif",
            "https://media.tenor.com/nP2xyvYJ4zMAAAAC/anime-bite.gif",
            "https://media.tenor.com/TlT2QIR0vL4AAAAC/anime-bite-cute.gif",
        ]
    }
}


# === Botones ===
class ReactionView(discord.ui.View):
    def __init__(self, author, target, tipo):
        super().__init__(timeout=None)
        self.author = author
        self.target = target
        self.tipo = tipo

    @discord.ui.button(label="💞 Corresponder", style=discord.ButtonStyle.green)
    async def corresponder(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.target:
            return await interaction.response.send_message("Solo la persona mencionada puede responder 💋", ephemeral=True)
        data = acciones[self.tipo]
        gif = random.choice(data["gifs"])
        embed = discord.Embed(
            description=f"{data['desc'].format(a=self.target.name, b=self.author.name)} 💕",
            color=data["color"]
        )
        embed.set_image(url=gif)
        await interaction.response.send_message(embed=embed)

    @discord.ui.button(label="🚫 Rechazar", style=discord.ButtonStyle.red)
    async def rechazar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.target:
            return await interaction.response.send_message("Solo la persona mencionada puede responder.", ephemeral=True)
        await interaction.response.send_message(f"💔 **{self.target.name}** rechazó a **{self.author.name}**...", ephemeral=False)


# === Cog principal ===
class Interacciones(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def mostrar_gif(self, channel, embed, gif_url, view):
        """
        Envía el embed, y si Discord no carga el GIF, lo reenvía como archivo.
        """
        try:
            msg = await channel.send(embed=embed, view=view)
            return msg
        except discord.HTTPException:
            # Si falla el embed, baja el GIF y lo manda como archivo
            async with aiohttp.ClientSession() as session:
                async with session.get(gif_url) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        file = discord.File(fp=bytearray(data), filename="gif.gif")
                        embed.set_image(url="attachment://gif.gif")
                        await channel.send(embed=embed, view=view, file=file)

    async def ejecutar_interaccion(self, ctx_or_inter, tipo, usuario):
        autor = ctx_or_inter.author if hasattr(ctx_or_inter, "author") else ctx_or_inter.user

        if usuario.id == autor.id:
            msg = "😳 No puedes hacerlo contigo mismo..."
            if isinstance(ctx_or_inter, commands.Context):
                return await ctx_or_inter.send(msg)
            else:
                return await ctx_or_inter.response.send_message(msg, ephemeral=True)

        data = acciones[tipo]
        gif = random.choice(data["gifs"])
        desc = data["desc"].format(a=autor.name, b=usuario.name)

        # Guardar interacción
        if interacciones_db:
            await interacciones_db.update_one(
                {"user1": str(autor.id), "user2": str(usuario.id), "action": tipo},
                {"$inc": {"count": 1}},
                upsert=True
            )

        embed = discord.Embed(description=desc, color=data["color"])
        embed.set_image(url=gif)
        embed.set_footer(text=f"{tipo.title()} • {autor.name}", icon_url=autor.avatar.url if autor.avatar else None)

        view = ReactionView(autor, usuario, tipo)

        # Slash o prefijo
        if isinstance(ctx_or_inter, commands.Context):
            await self.mostrar_gif(ctx_or_inter.channel, embed, gif, view)
        else:
            await ctx_or_inter.response.defer()  # evita errores de interacción
            await self.mostrar_gif(ctx_or_inter.channel, embed, gif, view)

    # --- comandos prefijo ---
    @commands.command()
    async def kiss(self, ctx, usuario: discord.Member):
        await self.ejecutar_interaccion(ctx, "kiss", usuario)

    @commands.command()
    async def hug(self, ctx, usuario: discord.Member):
        await self.ejecutar_interaccion(ctx, "hug", usuario)

    @commands.command()
    async def pat(self, ctx, usuario: discord.Member):
        await self.ejecutar_interaccion(ctx, "pat", usuario)

    @commands.command()
    async def slap(self, ctx, usuario: discord.Member):
        await self.ejecutar_interaccion(ctx, "slap", usuario)

    @commands.command()
    async def bite(self, ctx, usuario: discord.Member):
        await self.ejecutar_interaccion(ctx, "bite", usuario)

    # --- slash ---
    @app_commands.command(name="kiss", description="Dale un beso a alguien 💋")
    async def slash_kiss(self, interaction: discord.Interaction, usuario: discord.Member):
        await self.ejecutar_interaccion(interaction, "kiss", usuario)

    @app_commands.command(name="hug", description="Abraza a alguien 🤗")
    async def slash_hug(self, interaction: discord.Interaction, usuario: discord.Member):
        await self.ejecutar_interaccion(interaction, "hug", usuario)

    @app_commands.command(name="pat", description="Dale palmaditas ✨")
    async def slash_pat(self, interaction: discord.Interaction, usuario: discord.Member):
        await self.ejecutar_interaccion(interaction, "pat", usuario)

    @app_commands.command(name="slap", description="Dale una bofetada 👋")
    async def slash_slap(self, interaction: discord.Interaction, usuario: discord.Member):
        await self.ejecutar_interaccion(interaction, "slap", usuario)

    @app_commands.command(name="bite", description="Muérdele 🩸")
    async def slash_bite(self, interaction: discord.Interaction, usuario: discord.Member):
        await self.ejecutar_interaccion(interaction, "bite", usuario)


async def setup(bot):
    await bot.add_cog(Interacciones(bot))
    print("💞 Cog de interacciones cargado correctamente.")
