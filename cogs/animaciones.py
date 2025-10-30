# cogs/kiss.py
import discord
from discord.ext import commands

class Kiss(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def kiss(self, ctx, member: discord.Member):
        if member == ctx.author:
            return await ctx.send("No te beses a ti mismo.")
        if member.bot:
            return await ctx.send("No puedes besar a un bot.")

        text = f"**{ctx.author.display_name}** besó a **{member.display_name}**"
        file = discord.File("kiss.gif", filename="kiss.gif")
        await ctx.send(text, file=file)

async def setup(bot):
    await bot.add_cog(Kiss(bot))
