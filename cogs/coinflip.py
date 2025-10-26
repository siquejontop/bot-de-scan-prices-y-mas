import random
import discord
from discord.ext import commands

class Coinflip(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @commands.command(aliases=["flip","coin"])
  async def coinflip(self, ctx):
    resultados = ["cara", "cruz"]
    resultado = random.choice(resultados)
    embed = discord.Embed(
      title="Lanzando la moneda...",
      description=f"**Resultado:**{resultado.capitalize()}
      ({[resultado]})",
      color=discord.Color.gold()
    )
    embed.set_footer(text=f"Comando solicitado por {ctx.author}",
                     icon_url=ctx.author.avatar.url)

    await ctx.send(embed=embed)

async def setup(bot):
  await. bot.add_cog(CoinFlip(bot))
      
