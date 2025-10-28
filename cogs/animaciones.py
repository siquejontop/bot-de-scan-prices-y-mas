import discord
from discord.ext import commands
from discord import app_commands
import random
import motor.motor_asyncio
import os

# --- Configuración global Mongo ---
mongo_uri = os.getenv("MONGO_URI")
client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
db = client["nekotina_clone"]
interacciones = db["interacciones"]


# --- Diccionario con acciones, colores y gifs ---
acciones = {
    "kiss": {
        "desc": "💋",
        "color": discord.Color.pink(),
        "gifs": [
            "https://media.tenor.com/0Z0pF4b5bxUAAAAC/kiss-anime.gif",
            "https://media.tenor.com/lwBILh_E1CMAAAAC/anime-kiss.gif",
            "https://media.tenor.com/3ZxfrtDZX8YAAAAC/anime-kiss-scene.gif",
            "https://media.tenor.com/IH8Z-NHtQvAAAAAC/anime-romance-kiss.gif",
            "https://media.tenor.com/pXoyhGEMa3AAAAAC/ano-kiss.gif",
            "https://media.tenor.com/9E2i8PMmF5wAAAAC/anime-couple-kiss.gif",
            "https://media.tenor.com/vVfsq1Gl8o4AAAAC/anime-cute.gif",
            "https://media.tenor.com/6czlwEJmXRUAAAAC/sweet-kiss.gif",
        ]
    },
    "hug": {
        "desc": "🤗",
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
        "desc": "✨",
        "color": discord.Color.gold(),
        "gifs": [
            "https://media.tenor.com/AW5zk8FfGnoAAAAC/headpat.gif",
            "https://media.tenor.com/MYjCChfTbkoAAAAC/anime-headpat.gif",
            "https://media.tenor.com/XgEMy7QDb0AAAAAC/anime-pat.gif",
            "https://media.tenor.com/Rm5yL4kD45sAAAAC/pat-anime.gif",
        ]
    },
    "slap": {
        "desc": "👋",
        "color": discord.Color.red(),
        "gifs": [
            "https://media.tenor.com/vYFJYVgY8qsAAAAC/slap-anime.gif",
            "https://media.tenor.com/GfSX-u7VGM4AAAAC/slap.gif",
            "https://media.tenor.com/XiYuUqzJdLwAAAAC/anime-girl-slap.gif",
            "https://media.tenor.com/F4vA1z_9OKoAAAAC/anime-hit.gif",
        ]
    },
    "bite": {
        "desc": "🩸",
        "color": discord.Color.dark_red(),
        "gifs": [
            "https://media.tenor.com/L8j36e0cU6IAAAAC/anime-bite.gif",
            "https://media.tenor.com/ZtNU3M6V4aUAAAAC/anime-vampire-bite.gif",
            "https://media.tenor.com/nP2xyvYJ4zMAAAAC/anime-bite.gif",
            "https://media.tenor.com/TlT2QIR0vL4AAAAC/anime-bite-cute.gif",
        ]
    }
}


# --- Clase con botones interactivos ---
class ReactionView(discord.ui.View):
    def __init__(self, author, target, tipo):
        super().__init__(timeout=None)
        self.author = author
        self.target = target
        self.tipo = tipo

    @discord.ui.button(label="💞 Corresponder", style=discord.ButtonStyle.green)
    async def corresponder(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.target:
            return await interaction.response.send_message(
                "Solo la persona mencionada puede responder 💋", ephemeral=True
            )
        gif = random.choice(acciones[self.tipo]["gifs"])
        embed = discord.Embed(
            description=f"{acciones[self.tipo]['desc']} **{self.target.name}** correspondió a **{self.author.name}** 💞",
            color=acciones[self.tipo]["color"]
        )
        embed.set_image(url=gif)
        await interaction.response.send_message(embed=embed)

    @discord.ui.button(label="🚫 Rechazar", style=discord.ButtonStyle.red)
    async def rechazar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.target:
            return await interaction.response.send_message(
                "Solo la persona mencionada puede responder.", ephemeral=True
            )
        await interaction.response.send_message(
            f"💔 **{self.target.name}** rechazó a **{self.author.name}**...", ephemeral=False
        )


# --- Cog principal ---
class Interacciones(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def ejecutar_interaccion(self, ctx, tipo, usuario):
        if usuario.id == ctx.author.id:
            return await ctx.send("😳 No puedes hacerlo contigo mismo...")

        data = acciones[tipo]
        gif = random.choice(data["gifs"])
        color = data["color"]

        # Guardar en MongoDB
        await interacciones.update_one(
            {"user1": str(ctx.author.id), "user2": str(usuario.id), "action": tipo},
            {"$inc": {"count": 1}},
            upsert=True
        )

        embed = discord.Embed(
            description=f"{data['desc']} **{ctx.author.name}** {tipo} a **{usuario.name}**!",
            color=color
        )
        embed.set_image(url=gif)
        view = ReactionView(ctx.author, usuario, tipo)
        await ctx.send(embed=embed, view=view)

    # ----- Comandos con prefijo -----
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

    # ----- Slash commands (iguales pero para / -----
    @app_commands.command(name="kiss", description="Dale un beso a alguien 💋")
    async def slash_kiss(self, interaction: discord.Interaction, usuario: discord.Member):
        ctx = await self.bot.get_context(interaction)
        await self.ejecutar_interaccion(ctx, "kiss", usuario)

    @app_commands.command(name="hug", description="Abraza a alguien 🤗")
    async def slash_hug(self, interaction: discord.Interaction, usuario: discord.Member):
        ctx = await self.bot.get_context(interaction)
        await self.ejecutar_interaccion(ctx, "hug", usuario)

    @app_commands.command(name="pat", description="Dale palmaditas a alguien ✨")
    async def slash_pat(self, interaction: discord.Interaction, usuario: discord.Member):
        ctx = await self.bot.get_context(interaction)
        await self.ejecutar_interaccion(ctx, "pat", usuario)

    @app_commands.command(name="slap", description="Dale una bofetada 👋")
    async def slash_slap(self, interaction: discord.Interaction, usuario: discord.Member):
        ctx = await self.bot.get_context(interaction)
        await self.ejecutar_interaccion(ctx, "slap", usuario)

    @app_commands.command(name="bite", description="Muérdele 🩸")
    async def slash_bite(self, interaction: discord.Interaction, usuario: discord.Member):
        ctx = await self.bot.get_context(interaction)
        await self.ejecutar_interaccion(ctx, "bite", usuario)


# --- Cargar el cog ---
async def setup(bot):
    await bot.add_cog(Interacciones(bot))
    print("💞 Cog de interacciones cargado correctamente.")
