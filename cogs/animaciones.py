# cogs/interacciones.py
import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import io
import random
import motor.motor_asyncio
import os
from dotenv import load_dotenv

load_dotenv()

# === MongoDB ===
mongo_uri = os.getenv("MONGO_URI")
db = None
pair_db = None
if mongo_uri:
    client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
    db = client["siquej_bot"]
    pair_db = db["parejas"]  # Contador de interacciones entre dos usuarios
    print("MongoDB conectado: estadísticas de parejas activadas")
else:
    print("MongoDB no configurado. Contador de parejas desactivado.")

# === 20+ GIFs con fuente (kiss) ===
KISS_GIFS = [
    {"url": "https://media1.tenor.com/m/kmxEaVuW8AoAAAAC/kiss-gentle-kiss.gif", "source": "Anime: Kimi no Koto ga Daisuki"},
    {"url": "https://media1.tenor.com/m/1pL8Mkkwz9UAAAAC/kiss-anime.gif", "source": "Anime: Horimiya"},
    {"url": "https://media1.tenor.com/m/9k6z7v9n5wMAAAAC/kiss.gif", "source": "Anime: Kaguya-sama"},
    {"url": "https://media1.tenor.com/m/3dK7j2qM0nUAAAAC/kiss-love.gif", "source": "Anime: My Teen Romantic Comedy"},
    {"url": "https://media1.tenor.com/m/5K9b8W2rLqUAAAAC/anime-kiss.gif", "source": "Anime: Toradora!"},
    {"url": "https://media1.tenor.com/m/2vN5m2iV2fUAAAAC/kiss.gif", "source": "Anime: Your Lie in April"},
    {"url": "https://media1.tenor.com/m/1z5n1k1t1sUAAAAC/kiss.gif", "source": "Anime: Clannad"},
    {"url": "https://media1.tenor.com/m/8K9b8W2rLqUAAAAC/kiss.gif", "source": "Anime: Violet Evergarden"},
    {"url": "https://media1.tenor.com/m/9k6z7v9n5wMAAAAC/kiss.gif", "source": "Anime: A Silent Voice"},
    {"url": "https://media1.tenor.com/m/3dK7j2qM0nUAAAAC/kiss.gif", "source": "Anime: Rascal Does Not Dream"},
    {"url": "https://media1.tenor.com/m/5K9b8W2rLqUAAAAC/kiss.gif", "source": "Anime: Fruits Basket"},
    {"url": "https://media1.tenor.com/m/2vN5m2iV2fUAAAAC/kiss.gif", "source": "Anime: Re:Zero"},
    {"url": "https://media1.tenor.com/m/1z5n1k1t1sUAAAAC/kiss.gif", "source": "Anime: Steins;Gate"},
    {"url": "https://media1.tenor.com/m/8K9b8W2rLqUAAAAC/kiss.gif", "source": "Anime: Death Note"},
    {"url": "https://media1.tenor.com/m/9k6z7v9n5wMAAAAC/kiss.gif", "source": "Anime: Naruto"},
    {"url": "https://media1.tenor.com/m/3dK7j2qM0nUAAAAC/kiss.gif", "source": "Anime: One Piece"},
    {"url": "https://media1.tenor.com/m/5K9b8W2rLqUAAAAC/kiss.gif", "source": "Anime: Attack on Titan"},
    {"url": "https://media1.tenor.com/m/2vN5m2iV2fUAAAAC/kiss.gif", "source": "Anime: Demon Slayer"},
    {"url": "https://media1.tenor.com/m/1z5n1k1t1sUAAAAC/kiss.gif", "source": "Anime: Jujutsu Kaisen"},
    {"url": "https://media1.tenor.com/m/8K9b8W2rLqUAAAAC/kiss.gif", "source": "Anime: Spy x Family"},
]

# === View con botones ===
class KissView(discord.ui.View):
    def __init__(self, author, target, gif_data, pair_key):
        super().__init__(timeout=300)
        self.author = author
        self.target = target
        self.gif_data = gif_data
        self.pair_key = pair_key

    @discord.ui.button(label="Corresponder", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.target:
            return await interaction.response.send_message("Solo el mencionado puede corresponder.", ephemeral=True)

        # Contador de pareja
        count = 1
        if pair_db:
            result = await pair_db.find_one_and_update(
                {"pair": self.pair_key},
                {"$inc": {"count": 1}},
                upsert=True,
                return_document=True
            )
            count = result["count"]

        # Mensaje de correspondencia
        msg = f"**{self.target.display_name}** correspondió el beso de **{self.author.display_name}** ~\n"
        msg += f"**{self.author.display_name}** y **{self.target.display_name}** se han besado **{count}** veces."

        # Enviar GIF como archivo
        async with aiohttp.ClientSession() as session:
            async with session.get(self.gif_data["url"]) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    file = discord.File(fp=io.BytesIO(data), filename="kiss.gif")
                    await interaction.response.send_message(
                        content=msg,
                        file=file
                    )
        self.stop()

    @discord.ui.button(label="Rechazar", style=discord.ButtonStyle.red)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.target:
            return await interaction.response.send_message("Solo el mencionado puede rechazar.", ephemeral=True)
        await interaction.response.send_message(f"**{self.target.display_name}** rechazó el beso de **{self.author.display_name}**...")
        self.stop()

# === Cog ===
class Interacciones(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    async def send_gif_with_source(self, ctx, text, gif_data, view=None):
        try:
            async with self.session.get(gif_data["url"]) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    file = discord.File(fp=io.BytesIO(data), filename="kiss.gif")
                    await ctx.send(f"{text}\n*{gif_data['source']}*", file=file, view=view)
                else:
                    await ctx.send(f"{text}\n*(GIF no disponible)*", view=view)
        except:
            await ctx.send(f"{text}\n*(Error al cargar GIF)*", view=view)

    @commands.command(aliases=["beso", "k"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def kiss(self, ctx, member: discord.Member = None):
        if not member:
            return await ctx.send("Menciona a alguien: `,kiss @user`")
        if member == ctx.author:
            return await ctx.send("No puedes besarte a ti mismo.")
        if member.bot:
            return await ctx.send("No puedes besar a un bot.")

        # Seleccionar GIF
        gif_data = random.choice(KISS_GIFS)
        text = f"**{ctx.author.display_name}** besó a **{member.display_name}**"

        # Clave única para la pareja
        user_ids = sorted([ctx.author.id, member.id])
        pair_key = f"{user_ids[0]}_{user_ids[1]}"

        # Guardar beso
        if pair_db:
            await pair_db.update_one(
                {"pair": pair_key},
                {"$inc": {"count": 1}},
                upsert=True
            )

        # View
        view = KissView(ctx.author, member, gif_data, pair_key)
        await self.send_gif_with_source(ctx, text, gif_data, view)

    # === Más comandos (hug, pat, etc.) puedes añadir igual ===
    # (Opcional: dime si quieres que los haga todos)

async def setup(bot):
    await bot.add_cog(Interacciones(bot))
    print("Cog de interacciones (estilo Nekotina) cargado")
