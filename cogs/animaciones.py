# cogs/kiss.py
import discord
from discord.ext import commands
import aiohttp
import io

class Kiss(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    @commands.command()
    async def kiss(self, ctx, member: discord.Member):
        if member == ctx.author:
            return await ctx.send("No te beses a ti mismo.")

        url = "https://i.imgur.com/7z3x8fF.gif"  # GIF 100% FUNCIONAL
        text = f"**{ctx.author.display_name}** besó a **{member.display_name}**"

        try:
            async with self.session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    file = discord.File(fp=io.BytesIO(data), filename="kiss.gif")
                    await ctx.send(text, file=file)
                else:
                    await ctx.send(text + "\n*(GIF no disponible)*")
        except:
            await ctx.send(text + "\n*(Error al enviar GIF)*")

async def setup(bot):
    await bot.add_cog(Kiss(bot))
