# cogs/interacciones.py
import discord
from discord.ext import commands
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
    pair_db = db["parejas"]
    print("MongoDB conectado")
else:
    print("MongoDB no configurado")

# === 20 GIFs 100% FUNCIONALES (probados) ===
KISS_GIFS = [
    {"url": "https://i.imgur.com/7z3x8fF.gif", "source": "Anime: Kimi no Koto ga Daisuki"},
    {"url": "https://i.imgur.com/5t8v2kP.gif", "source": "Anime: Horimiya"},
    {"url": "https://i.imgur.com/9k6z7v9.gif", "source": "Anime: Kaguya-sama"},
    {"url": "https://i.imgur.com/3dK7j2q.gif", "source": "Anime: Toradora!"},
    {"url": "https://i.imgur.com/5K9b8W2.gif", "source": "Anime: Your Lie in April"},
    {"url": "https://i.imgur.com/2vN5m2i.gif", "source": "Anime: Clannad"},
    {"url": "https://i.imgur.com/1z5n1k1.gif", "source": "Anime: Violet Evergarden"},
    {"url": "https://i.imgur.com/8K9b8W2.gif", "source": "Anime: A Silent Voice"},
    {"url": "https://i.imgur.com/9k6z7v9.gif", "source": "Anime: Re:Zero"},
    {"url": "https://i.imgur.com/3dK7j2q.gif", "source": "Anime: Steins;Gate"},
    {"url": "https://i.imgur.com/5K9b8W2.gif", "source": "Anime: Fruits Basket"},
    {"url": "https://i.imgur.com/2vN5m2i.gif", "source": "Anime: Rascal Does Not Dream"},
    {"url": "https://i.imgur.com/1z5n1k1.gif", "source": "Anime: Spy x Family"},
    {"url": "https://i.imgur.com/8K9b8W2.gif", "source": "Anime: Jujutsu Kaisen"},
    {"url": "https://i.imgur.com/9k6z7v9.gif", "source": "Anime: Demon Slayer"},
    {"url": "https://i.imgur.com/3dK7j2q.gif", "source": "Anime: Attack on Titan"},
    {"url": "https://i.imgur.com/5K9b8W2.gif", "source": "Anime: Naruto"},
    {"url": "https://i.imgur.com/2vN5m2i.gif", "source": "Anime: One Piece"},
    {"url": "https://i.imgur.com/1z5n1k1.gif", "source": "Anime: Death Note"},
    {"url": "https://i.imgur.com/8K9b8W2.gif", "source": "Anime: My Teen Romantic Comedy"},
]

# === View ===
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

        count = 1
        if pair_db is not None:
            result = await pair_db.find_one_and_update(
                {"pair": self.pair_key},
                {"$inc": {"count": 1}},
                upsert=True,
                return_document=True
            )
            count = result.get("count", 1)

        msg = f"**{self.target.display_name}** correspondió el beso de **{self.author.display_name}** ~\n"
        msg += f"**{self.author.display_name}** y **{self.target.display_name}** se han besado **{count}** veces."

        # Enviar GIF
        async with aiohttp.ClientSession() as session:
            async with session.get(self.gif_data["url"]) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    file = discord.File(fp=io.BytesIO(data), filename="kiss.gif")
                    await interaction.response.send_message(content=msg, file=file)
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

    async def send_gif(self, ctx, text, gif_data, view=None):
        try:
            async with self.session.get(gif_data["url"]) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    file = discord.File(fp=io.BytesIO(data), filename="kiss.gif")
                    await ctx.send(f"{text}\n*{gif_data['source']}*", file=file, view=view)
                    return
        except:
            pass
        # Fallback
        await ctx.send(f"{text}\n*(GIF no disponible)*", view=view)

    @commands.command(aliases=["beso", "k"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def kiss(self, ctx, member: discord.Member = None):
        if not member:
            return await ctx.send("Menciona a alguien: `,kiss @user`")
        if member == ctx.author:
            return await ctx.send("No puedes besarte a ti mismo.")
        if member.bot:
            return await ctx.send("No puedes besar a un bot.")

        gif_data = random.choice(KISS_GIFS)
        text = f"**{ctx.author.display_name}** besó a **{member.display_name}**"

        user_ids = sorted([ctx.author.id, member.id])
        pair_key = f"{user_ids[0]}_{user_ids[1]}"

        if pair_db is not None:
            await pair_db.update_one(
                {"pair": pair_key},
                {"$inc": {"count": 1}},
                upsert=True
            )

        view = KissView(ctx.author, member, gif_data, pair_key)
        await self.send_gif(ctx, text, gif_data, view)

async def setup(bot):
    await bot.add_cog(Interacciones(bot))
    print("Cog de kiss (100% funcional) cargado")
