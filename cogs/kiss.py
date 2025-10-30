# cogs/interacciones.py
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import motor.motor_asyncio

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

# === View con botones (CORREGIDO) ===
class KissView(discord.ui.View):
    def __init__(self, author, target, pair_key):
        super().__init__(timeout=300)
        self.author = author
        self.target = target
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

        file = discord.File("assets/kiss.gif", filename="kiss.gif")
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

    @commands.command(aliases=["beso", "k"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def kiss(self, ctx, member: discord.Member = None):
        if not member:
            return await ctx.send("Menciona a alguien: `,kiss @user`")
        if member == ctx.author:
            return await ctx.send("No puedes besarte a ti mismo.")
        if member.bot:
            return await ctx.send("No puedes besar a un bot.")

        # Texto con fuente
        text = f"**{ctx.author.display_name}** besó a **{member.display_name}**\n*Anime: Kimi no Koto ga Daisuki*"

        # Clave de pareja
        user_ids = sorted([ctx.author.id, member.id])
        pair_key = f"{user_ids[0]}_{user_ids[1]}"

        # Guardar beso
        if pair_db is not None:
            await pair_db.update_one(
                {"pair": pair_key},
                {"$inc": {"count": 1}},
                upsert=True
            )

        # Archivo GIF
        file = discord.File("assets/kiss.gif", filename="kiss.gif")

        # View con botones
        view = KissView(ctx.author, member, pair_key)

        # ENVIAR MENSAJE CON VIEW
        await ctx.send(text, file=file, view=view)

async def setup(bot):
    await bot.add_cog(Interacciones(bot))
    print("Cog de interacciones COMPLETO cargado")
