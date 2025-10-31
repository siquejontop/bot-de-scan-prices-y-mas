# cogs/sync.py
from discord.ext import commands

class Sync(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def sync(self, ctx):
        try:
            synced = await ctx.bot.tree.sync()
            await ctx.send(f"Sincronizados {len(synced)} comandos: {', '.join([c.name for c in synced])}")
        except Exception as e:
            await ctx.send(f"Error: {e}")

async def setup(bot):
    await bot.add_cog(Sync(bot))
