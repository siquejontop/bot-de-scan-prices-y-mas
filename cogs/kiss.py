import discord
from discord.ext import commands
import random
import motor.motor_asyncio
import os
from dotenv import load_dotenv

load_dotenv()

mongo_uri = os.getenv("MONGO_URI")
pair_db = None
if mongo_uri:
    client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
    db = client["siquej_bot"]
    pair_db = db["parejas"]
    print("MongoDB conectado")
else:
    print("MongoDB no configurado")

KISS_GIFS = [
    {"url": "https://raw.githubusercontent.com/siquejontop/bot-de-scan-prices-y-mas/main/assets/kiss.gif", "source": "Anime: Kiss x Sis"},
]

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

        gif_data = random.choice(KISS_GIFS)

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

        embed = discord.Embed(color=0xFFC0CB)
        embed.description = f"**{ctx.author.display_name}** le dio un dulce beso a **{member.display_name}** 💕\n"
        embed.description += f"**{ctx.author.display_name}** y **{member.display_name}** se han besado **{count}** veces."
        embed.set_image(url=gif_data["url"])
        embed.set_footer(text=gif_data["source"])

        view = KissView(ctx.author, member, pair_key, gif_data)
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Interacciones(bot))
    print("Cog de besos cargados")
