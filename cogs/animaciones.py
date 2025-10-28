import discord
from discord.ext import commands
from discord import app_commands
import random
import motor.motor_asyncio
import os

# ===============================
# 🔗 Configuración de MongoDB
# ===============================
mongo_uri = os.getenv("MONGO_URI")
mongo_enabled = bool(mongo_uri)

if mongo_enabled:
    client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
    db = client["nekotina_clone"]
    interacciones_db = db["interacciones"]
else:
    interacciones_db = None
    print("⚠️ MongoDB no configurado, las estadísticas no se guardarán.")


# ===============================
# 💞 Diccionario de acciones
# ===============================
ACCIONES = {
    "kiss": {
        "emoji": "💋",
        "color": discord.Color.pink(),
        "desc": "le da un beso a",
        "gifs": [
            "https://media.tenor.com/0Z0pF4b5bxUAAAAC/kiss-anime.gif",
            "https://media.tenor.com/lwBILh_E1CMAAAAC/anime-kiss.gif",
            "https://media.tenor.com/3ZxfrtDZX8YAAAAC/anime-kiss-scene.gif",
            "https://media.tenor.com/IH8Z-NHtQvAAAAAC/anime-romance-kiss.gif",
            "https://media.tenor.com/9E2i8PMmF5wAAAAC/anime-couple-kiss.gif",
            "https://media.tenor.com/6czlwEJmXRUAAAAC/sweet-kiss.gif",
        ],
    },
    "hug": {
        "emoji": "🤗",
        "color": discord.Color.blurple(),
        "desc": "abraza fuertemente a",
        "gifs": [
            "https://media.tenor.com/2roX3uxz_68AAAAC/anime-hug.gif",
            "https://media.tenor.com/Wx9IEmZZXSoAAAAC/hug-anime.gif",
            "https://media.tenor.com/0K1Qv6lCQzYAAAAC/anime-hug-love.gif",
            "https://media.tenor.com/qWUEHZ2r6m8AAAAC/anime-hug.gif",
        ],
    },
    "pat": {
        "emoji": "✨",
        "color": discord.Color.gold(),
        "desc": "acaricia la cabeza de",
        "gifs": [
            "https://media.tenor.com/AW5zk8FfGnoAAAAC/headpat.gif",
            "https://media.tenor.com/MYjCChfTbkoAAAAC/anime-headpat.gif",
            "https://media.tenor.com/XgEMy7QDb0AAAAAC/anime-pat.gif",
        ],
    },
    "slap": {
        "emoji": "💢",
        "color": discord.Color.red(),
        "desc": "le da una bofetada a",
        "gifs": [
            "https://media.tenor.com/vYFJYVgY8qsAAAAC/slap-anime.gif",
            "https://media.tenor.com/GfSX-u7VGM4AAAAC/slap.gif",
            "https://media.tenor.com/XiYuUqzJdLwAAAAC/anime-girl-slap.gif",
        ],
    },
    "bite": {
        "emoji": "🩸",
        "color": discord.Color.dark_red(),
        "desc": "muérdele suavemente a",
        "gifs": [
            "https://media.tenor.com/L8j36e0cU6IAAAAC/anime-bite.gif",
            "https://media.tenor.com/TlT2QIR0vL4AAAAC/anime-bite-cute.gif",
        ],
    },
}


# ===============================
# 💬 Vista de botones
# ===============================
class ReactionView(discord.ui.View):
    def __init__(self, author, target, tipo):
        super().__init__(timeout=30)
        self.author = author
        self.target = target
        self.tipo = tipo

    @discord.ui.button(label="💞 Corresponder", style=discord.ButtonStyle.success)
    async def corresponder(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.target:
            return await interaction.response.send_message("❌ No puedes usar este botón.", ephemeral=True)

        gif = random.choice(ACCIONES[self.tipo]["gifs"])
        embed = discord.Embed(
            description=f"{ACCIONES[self.tipo]['emoji']} **{self.target.display_name}** correspondió a **{self.author.display_name}** 💖",
            color=ACCIONES[self.tipo]["color"],
        )
        embed.set_image(url=gif)
        await interaction.response.send_message(embed=embed)
        self.stop()

    @discord.ui.button(label="💔 Rechazar", style=discord.ButtonStyle.danger)
    async def rechazar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.target:
            return await interaction.response.send_message("❌ No puedes usar este botón.", ephemeral=True)
        await interaction.response.send_message(
            f"💔 **{self.target.display_name}** rechazó a **{self.author.display_name}**...", ephemeral=False
        )
        self.stop()


# ===============================
# 💞 Cog de Interacciones
# ===============================
class Interacciones(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def ejecutar_interaccion(self, ctx_or_inter, tipo, usuario: discord.Member):
        autor = ctx_or_inter.user if isinstance(ctx_or_inter, discord.Interaction) else ctx_or_inter.author

        # --- Validación ---
        if usuario.id == autor.id:
            msg = "😳 No puedes hacerlo contigo mismo..."
            if isinstance(ctx_or_inter, discord.Interaction):
                return await ctx_or_inter.response.send_message(msg, ephemeral=True)
            return await ctx_or_inter.reply(msg)

        accion = ACCIONES[tipo]
        gif = random.choice(accion["gifs"])
        color = accion["color"]

        # --- Guardar en Mongo (si está activo) ---
        if interacciones_db:
            await interacciones_db.update_one(
                {"user_id": str(autor.id), "action": tipo},
                {"$inc": {"count": 1}},
                upsert=True
            )

        # --- Crear embed ---
        embed = discord.Embed(
            description=f"{accion['emoji']} **{autor.display_name}** {accion['desc']} **{usuario.display_name}**",
            color=color,
        )
        embed.set_image(url=gif)
        embed.set_footer(text="💞 Usa los botones para responder")

        view = ReactionView(autor, usuario, tipo)

        # --- Enviar ---
        if isinstance(ctx_or_inter, discord.Interaction):
            await ctx_or_inter.response.send_message(embed=embed, view=view)
        else:
            await ctx_or_inter.reply(embed=embed, view=view)

    # ==== Comandos de texto ====
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

    # ==== Slash Commands ====
    @app_commands.command(name="kiss", description="Dale un beso a alguien 💋")
    async def slash_kiss(self, inter: discord.Interaction, usuario: discord.Member):
        await self.ejecutar_interaccion(inter, "kiss", usuario)

    @app_commands.command(name="hug", description="Abraza a alguien 🤗")
    async def slash_hug(self, inter: discord.Interaction, usuario: discord.Member):
        await self.ejecutar_interaccion(inter, "hug", usuario)

    @app_commands.command(name="pat", description="Acaricia a alguien ✨")
    async def slash_pat(self, inter: discord.Interaction, usuario: discord.Member):
        await self.ejecutar_interaccion(inter, "pat", usuario)

    @app_commands.command(name="slap", description="Dale una bofetada 💢")
    async def slash_slap(self, inter: discord.Interaction, usuario: discord.Member):
        await self.ejecutar_interaccion(inter, "slap", usuario)

    @app_commands.command(name="bite", description="Muérdele 🩸")
    async def slash_bite(self, inter: discord.Interaction, usuario: discord.Member):
        await self.ejecutar_interaccion(inter, "bite", usuario)


# ===============================
# ⚙️ Setup del cog
# ===============================
async def setup(bot):
    await bot.add_cog(Interacciones(bot))
    print("💞 Cog de interacciones cargado correctamente.")
