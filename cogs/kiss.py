import discord
from discord.ext import commands

class Kiss(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["beso", "k"])
    async def kiss(self, ctx, member: discord.Member = None):
        if not member:
            return await ctx.send("Menciona a alguien: `,kiss @user`")
        if member == ctx.author:
            return await ctx.send("No puedes besarte a ti mismo.")
        if member.bot:
            return await ctx.send("No puedes besar a un bot.")

        text = f"**{ctx.author.display_name}** besó a **{member.display_name}**"
        file = discord.File("assets/kiss.gif", filename="kiss.gif")
        
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Corresponder", style=discord.ButtonStyle.green))
        view.add_item(discord.ui.Button(label="Rechazar", style=discord.ButtonStyle.red))
        
        await ctx.send(text, file=file, view=view)

async def setup(bot):
    await bot.add_cog(Kiss(bot))
