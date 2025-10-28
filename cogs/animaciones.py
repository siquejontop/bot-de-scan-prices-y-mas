import discord
from discord.ext import commands
from discord import app_commands
import random
import motor.motor_asyncio
import os
import asyncio

# ===============================
# 🔗 Conexión con MongoDB
# ===============================
mongo_uri = os.getenv("MONGO_URI")
client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
db = client["nekotina_clone"]
coleccion = db["interacciones"]

# ===============================
# 💞 Diccionario de acciones
# ===============================
ACCIONES = {
    "kiss": {
        "emoji": "💋",
        "color": discord.Color.pink(),
        "gifs": [
            "https://media.tenor.com/0Z0pF4b5bxUAAAAC/kiss-anime.gif",
            "https://media.tenor.com/lwBILh_E1CMAAAAC/anime-kiss.gif",
            "https://media.tenor.com/IH8Z-NHtQvAAAAAC/anime-romance-kiss.gif",
            "https://media.tenor.com/9E2i8PMmF5wAAAAC/anime-couple-kiss.gif",
            "https://media.tenor.com/6czlwEJmXRUAAAAC/sweet-kiss.gif",
        ],
    },
    "hug": {
        "emoji": "🤗",
        "color": discord.Color.blurple(),
        "gifs": [
            "https://media.tenor.com/2roX3uxz_68AAAAC/anime-hug.gif",
            "https://media.tenor.com/eTjX0EYcV1kAAAAC/hug-anime.gif",
            "https://media.tenor.com/0K1Qv6lCQzYAAAAC/anime-hug-love.gif",
        ],
    },
    "pat": {
        "emoji": "✨",
        "color": discord.Color.gold(),
        "gifs": [
            "https://media.tenor.com/AW5zk8FfGnoAAAAC/headpat.gif",
            "https://media.tenor.com/MYjCChfTbkoAAAAC/anime-headpat.gif",
        ],
    },
    "slap": {
        "emoji": "💢",
        "color": discord.Color.red(),
        "gifs": [
            "https://media.tenor.com/vYFJYVgY8qsAAAAC/slap-anime.gif",
            "https://media.tenor.com/GfSX-u7VGM4AAAAC/slap.gif",
            "https://media.tenor.com/F4vA1z_9OKoAAAAC/anime-hit.gif",
        ],
    },
    "bite": {
        "emoji": "🩸",
        "color": discord.Color.dark_red(),
        "gifs": [
            "https://media.tenor.com/L8j36e0cU6IAAAAC/anime-bite.gif",
            "https://media.tenor.com/ZtNU3M6V4aUAAAAC/anime-vampire-bite.gif",
        ],
    },
}

# ===============================
# 💬 Vista interactiva con botones
# ===============================
class ReactionView(discord.ui.View):
    def __init__(self, autor, objetivo, tipo):
        super().__init__(timeout=30)  # tiempo de respuesta
        self.autor = autor
        self.objetivo = objetivo
        self.tipo = tipo

    @discord.ui.button(label="💞 Corresponder", style=discord.ButtonStyle.success)
    async def corresponder(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.objetivo.id:
            return await interaction.response.send_message(
                "💢 Solo la persona mencionada puede responder.", ephemeral=True
            )

        gif = random.choice(ACCIONES[self.tipo]["gifs"])
        embed = discord.Embed(
            description=f"{ACCIONES[self.tipo]['emoji']} **{self.objetivo.name}** correspondió a **{self.autor.name}** 💖",
            color=ACCIONES[self.tipo]["color"]
        )
        embed.set_image(url=gif)
        await interaction.response.send_message(embed=embed)
        self.stop()

    @discord.ui.button(label="💔 Rechazar", style=discord.ButtonStyle.danger)
    async def rechazar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.objetivo.id:
            return await interaction.response.send_message(
                "💢 Solo la persona mencionada puede responder.", ephemeral=True
            )

        await interaction.response.send_message(
            f"💔 **{self.objetivo.name}** rechazó a **{self.autor.name}**...", ephemeral=False
        )
        self.stop()

# ===============================
# 💞 Cog principal
# ===============================
class Interacciones(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ========================================
    # 🔧 Método general para ejecutar acciones
    # ========================================
    async def ejecutar(self, ctx_or_inter, tipo, usuario):
        autor = ctx_or_inter.user if isinstance(ctx_or_inter, discord.Interaction) else ctx_or_inter.author

        if usuario.id == autor.id:
            msg = "😳 No puedes hacerlo contigo mismo..."
            if isinstance(ctx_or_inter, discord.Interaction):
                return await ctx_or_inter.response.send_message(msg, ephemeral=True)
            return await ctx_or_inter.reply(msg)

        accion = ACCIONES[tipo]
        gif = random.choice(accion["gifs"])
        color = accion["color"]

        # Guardar en MongoDB
        await coleccion.update_one(
            {"user_id": str(autor.id), "action": tipo},
            {"$inc": {"count": 1}},
            upsert=True
        )

        embed = discord.Embed(
            description=f"{accion['emoji']} **{autor.name}** {tipo} a **{usuario.name}**!",
            color=color
        )
        embed.set_image(url=gif)
        view = ReactionView(autor, usuario, tipo)

        # Enviar según tipo de contexto
        if isinstance(ctx_or_inter, discord.Interaction):
            await ctx_or_inter.response.send_message(embed=embed, view=view)
        else:
            await ctx_or_inter.reply(embed=embed, view=view)

    # ========================================
    # 🔹 Comandos con prefijo
    # ========================================
    @commands.command()
    async def kiss(self, ctx, usuario: discord.Member):
        await self.ejecutar(ctx, "kiss", usuario)

    @commands.command()
    async def hug(self, ctx, usuario: discord.Member):
        await self.ejecutar(ctx, "hug", usuario)

    @commands.command()
    async def pat(self, ctx, usuario: discord.Member):
        await self.ejecutar(ctx, "pat", usuario)

    @commands.command()
    async def slap(self, ctx, usuario: discord.Member):
        await self.ejecutar(ctx, "slap", usuario)

    @commands.command()
    async def bite(self, ctx, usuario: discord.Member):
        await self.ejecutar(ctx, "bite", usuario)

    # ========================================
    # 🔹 Slash Commands (interactions)
    # ========================================
    @app_commands.command(name="kiss", description="Dale un beso a alguien 💋")
    async def slash_kiss(self, inter: discord.Interaction, usuario: discord.Member):
        await self.ejecutar(inter, "kiss", usuario)

    @app_commands.command(name="hug", description="Abraza a alguien 🤗")
    async def slash_hug(self, inter: discord.Interaction, usuario: discord.Member):
        await self.ejecutar(inter, "hug", usuario)

    @app_commands.command(name="pat", description="Dale una caricia ✨")
    async def slash_pat(self, inter: discord.Interaction, usuario: discord.Member):
        await self.ejecutar(inter, "pat", usuario)

    @app_commands.command(name="slap", description="Dale una bofetada 💢")
    async def slash_slap(self, inter: discord.Interaction, usuario: discord.Member):
        await self.ejecutar(inter, "slap", usuario)

    @app_commands.command(name="bite", description="Muérdele 🩸")
    async def slash_bite(self, inter: discord.Interaction, usuario: discord.Member):
        await self.ejecutar(inter, "bite", usuario)

# ===============================
# ⚙️ Setup del cog
# ===============================
async def setup(bot):
    await bot.add_cog(Interacciones(bot))
    print("💞 Cog de interacciones mejorado y cargado correctamente.")
