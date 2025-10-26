```python
import random
import discord
from discord.ext import commands
import logging

# Configure logging
logger = logging.getLogger(__name__)

class Coinflip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("Coinflip cog initialized")

    @commands.command(aliases=["flip", "coin"])
    async def coinflip(self, ctx):
        resultados = ["cara", "cruz"]
        resultado = random.choice(resultados)
        embed = discord.Embed(
            title="Lanzando la moneda...",
            description=f"**Resultado:** {resultado.capitalize()}\n({resultado})",
            color=discord.Color.gold()
        )
        # Safely handle the case where the user has no avatar
        avatar_url = ctx.author.avatar.url if ctx.author.avatar else discord.utils.MISSING
        embed.set_footer(
            text=f"Comando solicitado por {ctx.author}",
            icon_url=avatar_url
        )

        await ctx.send(embed=embed)
        logger.info(f"Coinflip command executed by {ctx.author} in {ctx.guild}")

async def setup(bot):
    await bot.add_cog(Coinflip(bot))
    logger.info("Coinflip cog loaded")
