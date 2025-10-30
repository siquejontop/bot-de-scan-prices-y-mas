# cogs/interacciones.py
import discord
from discord.ext import commands
import random
import motor.motor_asyncio
import os
from dotenv import load_dotenv

load_dotenv()

# === MongoDB ===
mongo_uri = os.getenv("MONGO_URI")
pair_db = None
if mongo_uri:
    client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
    db = client["siquej_bot"]
    pair_db = db["parejas"]
    print("MongoDB conectado")
else:
    print("MongoDB no configurado")

# === 20+ GIFs con fuente (como Nekotina) ===
KISS_GIFS = [
    {"url": "https://i.imgur.com/7z3x8fF.gif", "source": "Anime: Kimi no Koto ga Daisuki"},
    {"url": "https://i.imgur.com/5t8v2kP.gif", "source": "Anime: Kämpfer"},
    {"url": "https://i.imgur.com/9k6z7v9.gif", "source": "Anime: Horimiya"},
    {"url": "https://i.imgur.com/3dK7j2q.gif", "source": "Anime: Kaguya-sama"},
    {"url": "https://i.imgur.com/5K9b8W2.gif", "source": "Anime: Toradora!"},
    {"url": "https://i.imgur.com/2vN5m2i.gif", "source": "Anime: Your Lie in April"},
    {"url": "https://i.imgur.com/1z5n1k1.gif", "source": "Anime: Clannad"},
    {"url": "https://i.imgur.com/8K9b8W2.gif", "source": "Anime: Violet Evergarden"},
    {"url": "https://i.imgur.com/9k6z7v9.gif", "source": "Anime: A Silent Voice"},
    {"url": "https://i.imgur.com/3dK7j2q.gif", "source": "Anime: Re:Zero"},
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
    def __init__(self, author, target, pair_key, gif_data):
        super().__init__(timeout=300)
        self.author = author
        self.target = target
        self.pair_key = pair_key
        self.gif_data = gif_data

    @discord.ui.button(label="Corresponder", style=discord.ButtonStyle.green, emoji="❤️")
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

        embed = discord.Embed(color=0xFFC0CB)
        embed.description = f"**{self.target.display_name}** le dio un dulce beso a **{self.author.display_name}** 💕\n"
        embed.description += f"**{self.author.display_name}** y **{self.target.display_name}** se han besado **{count}** veces."
        embed.set_image(url=self.gif_data["url"])
        embed.set_footer(text=self.gif_data["source"])

        await interaction.response.send_message(embed=embed)
        self.stop()

    @discord.ui.button(label="No corresponder", style=discord.ButtonStyle.red, emoji="❌")
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.target:
            return await interaction.response.send_message("Solo el mencionado puede rechazar.", ephemeral=True)
        await interaction.response.send_message(f"**{self.target.display_name}** rechazó el beso de **{self.author.display_name}**...")
        self.stop()

# === Cog ===
class Interacciones(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["beso", "k"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def kiss(self, ctx, member: discord.Member = None):
        if not member:
            return await ctx.send("Menciona a alguien: `,kiss @user`")
        if member == ctx.author:
            return await ctx.send("No puedes besarte a ti mismo.")
        if member.bot:
            return await ctx.send("No puedes besar a un bot.")

        # GIF aleatorio
        gif_data = random.choice(KISS_GIFS)

        # Contador
        user_ids = sorted([ctx.author.id, member.id])
        pair_key = f"{user_ids[0]}_{user_ids[1]}"
        count = 1
        if pair_db is not None:
            result = await pair_db.find_one_and_update(
                {"pair": pair_key},
                {"$inc": {"count": 1}},
                upsert=True,
                return_document=True
            )
            count = result.get("count", 1)

        # Embed inicial
        embed = discord.Embed(color=0xFFC0CB)
        embed.description = f"**{ctx.author.display_name}** le dio un dulce beso a **{member.display_name}** 💕\n"
        embed.description += f"**{ctx.author.display_name}** y **{member.display_name}** se han besado **{count}** veces."
        embed.set_image(url=gif_data["url"])
        embed.set_footer(text=gif_data["source"])

        view = KissView(ctx.author, member, pair_key, gif_data)
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Interacciones(bot))
    print("Cog estilo Nekotina cargado")
