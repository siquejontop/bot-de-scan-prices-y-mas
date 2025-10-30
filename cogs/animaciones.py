import discord
from discord.ext import commands
from discord import app_commands
import random
import motor.motor_asyncio
import aiohttp
import os

# === MongoDB ===
mongo_uri = os.getenv("MONGO_URI")
if mongo_uri:
    client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
    db = client["nekotina_clone"]
    interacciones_db = db["interacciones"]
else:
    interacciones_db = None

# === Acciones ===
acciones = {
    "kiss": {
        "desc": "siquej besó a {b}",
        "color": discord.Color.pink(),
        "gifs": [
            "https://media1.tenor.com/m/kmxEaVuW8AoAAAAC/kiss-gentle-kiss.gif",
        ]
    },
    "hug": {
        "desc": "{a} abrazó a {b}",
        "color": discord.Color.blurple(),
        "gifs": [
            "https://media.tenor.com/2roX3uxz_68AAAAC/anime-hug.gif",
            "https://media.tenor.com/Wx9IEmZZXSoAAAAC/hug-anime.gif",
        ]
    },
    "pat": {
        "desc": "{a} acarició a {b}",
        "color": discord.Color.gold(),
        "gifs": [
            "https://media.tenor.com/AW5zk8FfGnoAAAAC/headpat.gif",
        ]
    },
    "slap": {
        "desc": "{a} abofeteó a {b}",
        "color": discord.Color.red(),
        "gifs": [
            "https://media.tenor.com/vYFJYVgY8qsAAAAC/slap-anime.gif",
        ]
    },
    "bite": {
        "desc": "{a} mordió a {b}",
        "color": discord.Color.dark_red(),
        "gifs": [
            "https://media.tenor.com/L8j36e0cU6IAAAAC/anime-bite.gif",
        ]
    }
}

# === View con botones ===
class ReactionView(discord.ui.View):
    def __init__(self, author, target, tipo):
        super().__init__(timeout=300)
        self.author = author
        self.target = target
        self.tipo = tipo

    @discord.ui.button(label="Corresponder", style=discord.ButtonStyle.green)
    async def corresponder(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.target:
            return await interaction.response.send_message("Solo el mencionado puede responder.", ephemeral=True)
        
        data = acciones[self.tipo]
        gif = random.choice(data["gifs"])
        desc = data["desc"].format(a=self.target.display_name, b=self.author.display_name)
        
        embed = discord.Embed(description=f"**{desc}**", color=data["color"])
        embed.set_image(url=gif)
        
        await interaction.response.send_message(embed=embed)
        self.stop()

    @discord.ui.button(label="Rechazar", style=discord.ButtonStyle.red)
    async def rechazar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.target:
            return await interaction.response.send_message("Solo el mencionado puede responder.", ephemeral=True)
        
        await interaction.response.send_message(f"**{self.target.display_name}** rechazó a **{self.author.display_name}**...")
        self.stop()

# === Cog ===
class Interacciones(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    async def enviar_con_fallback(self, destino, embed, view=None):
        """Envía embed con GIF. Si falla, envía como archivo."""
        gif_url = embed.image.url
        try:
            # Intento 1: Enviar embed normal
            return await destino.send(embed=embed, view=view)
        except:
            try:
                # Intento 2: Descargar y enviar como archivo
                async with self.session.get(gif_url) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        file = discord.File(fp=io.BytesIO(data), filename="interaction.gif")
                        embed.set_image(url="attachment://interaction.gif")
                        return await destino.send(file=file, embed=embed, view=view)
            except:
                pass
            # Intento 3: Solo texto
            embed.set_image(url=None)
            return await destino.send(embed=embed, view=view)

    async def ejecutar(self, ctx_or_inter, tipo, usuario):
        if isinstance(ctx_or_inter, commands.Context):
            autor = ctx_or_inter.author
            canal = ctx_or_inter.channel
            is_slash = False
        else:
            autor = ctx_or_inter.user
            canal = ctx_or_inter.channel
            is_slash = True

        if usuario.id == autor.id:
            msg = "No puedes interactuar contigo mismo."
            if is_slash:
                await ctx_or_inter.response.send_message(msg, ephemeral=True)
            else:
                await ctx_or_inter.send(msg)
            return

        data = acciones[tipo]
        gif = random.choice(data["gifs"])
        desc = data["desc"].format(a=autor.display_name, b=usuario.display_name)

        # MongoDB
        if interacciones_db:
            await interacciones_db.update_one(
                {"user1": str(autor.id), "user2": str(usuario.id), "action": tipo},
                {"$inc": {"count": 1}},
                upsert=True
            )

        # Embed
        embed = discord.Embed(
            description=f"**{desc}**",
            color=data["color"]
        )
        embed.set_image(url=gif)

        # View
        view = ReactionView(autor, usuario, tipo)

        # Enviar
        if is_slash:
            await ctx_or_inter.response.send_message(embed=embed, view=view)
        else:
            await self.enviar_con_fallback(canal, embed, view)

    # === Comandos prefijo ===
    @commands.command()
    async def kiss(self, ctx, usuario: discord.Member = None):
        if not usuario: return await ctx.send("Menciona a alguien: `,kiss @user`")
        await self.ejecutar(ctx, "kiss", usuario)

    @commands.command()
    async def hug(self, ctx, usuario: discord.Member = None):
        if not usuario: return await ctx.send("Menciona a alguien: `,hug @user`")
        await self.ejecutar(ctx, "hug", usuario)

    @commands.command()
    async def pat(self, ctx, usuario: discord.Member = None):
        if not usuario: return await ctx.send("Menciona a alguien: `,pat @user`")
        await self.ejecutar(ctx, "pat", usuario)

    @commands.command()
    async def slap(self, ctx, usuario: discord.Member = None):
        if not usuario: return await ctx.send("Menciona a alguien: `,slap @user`")
        await self.ejecutar(ctx, "slap", usuario)

    @commands.command()
    async def bite(self, ctx, usuario: discord.Member = None):
        if not usuario: return await ctx.send("Menciona a alguien: `,bite @user`")
        await self.ejecutar(ctx, "bite", usuario)

    # === Slash ===
    @app_commands.command(name="kiss", description="Besar a alguien")
    async def slash_kiss(self, inter: discord.Interaction, usuario: discord.Member):
        await self.ejecutar(inter, "kiss", usuario)

    @app_commands.command(name="hug", description="Abrazar a alguien")
    async def slash_hug(self, inter: discord.Interaction, usuario: discord.Member):
        await self.ejecutar(inter, "hug", usuario)

    @app_commands.command(name="pat", description="Acariciar a alguien")
    async def slash_pat(self, inter: discord.Interaction, usuario: discord.Member):
        await self.ejecutar(inter, "pat", usuario)

    @app_commands.command(name="slap", description="Abofetear a alguien")
    async def slash_slap(self, inter: discord.Interaction, usuario: discord.Member):
        await self.ejecutar(inter, "slap", usuario)

    @app_commands.command(name="bite", description="Morder a alguien")
    async def slash_bite(self, inter: discord.Interaction, usuario: discord.Member):
        await self.ejecutar(inter, "bite", usuario)

async def setup(bot):
    await bot.add_cog(Interacciones(bot))
