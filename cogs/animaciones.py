# cogs/kiss.py
import discord
from discord.ext import commands
import aiohttp
import io
import random

class Kiss(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    async def send_gif(self, ctx, url, text):
        try:
            async with self.session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    file = discord.File(fp=io.BytesIO(data), filename="kiss.gif")
                    await ctx.send(text, file=file)
                else:
                    await ctx.send(text + "\n*(GIF no disponible)*")
        except:
            await ctx.send(text + "\n*(Error al cargar GIF)*")

    @commands.command()
    async def kiss(self, ctx, member: discord.Member = None):
        if not member:
            return await ctx.send("Menciona a alguien: `,kiss @user`")
        if member == ctx.author:
            return await ctx.send("No puedes besarte a ti mismo.")
        
        text = f"**{ctx.author.display_name}** besó a **{member.display_name}**"
        gif_url = "https://media1.tenor.com/m/kmxEaVuW8AoAAAAC/kiss-gentle-kiss.gif"
        await self.send_gif(ctx, gif_url, text)

    @commands.command()
    async def hug(self, ctx, member: discord.Member = None):
        if not member:
            return await ctx.send("Menciona a alguien: `,hug @user`")
        if member == ctx.author:
            return await ctx.send("No puedes abrazarte a ti mismo.")
        
        text = f"**{ctx.author.display_name}** abrazó a **{member.display_name}**"
        gif_url = "https://media.tenor.com/2roX3uxz_68AAAAC/anime-hug.gif"
        await self.send_gif(ctx, gif_url, text)

async def setup(bot):
    await bot.add_cog(Kiss(bot))
