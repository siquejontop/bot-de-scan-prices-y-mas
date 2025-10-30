import discord
from discord.ext import commands

# Configura el prefijo directamente aquí o en tu bot principal
# Si usas bot = commands.Bot(command_prefix=',') en tu main.py, no necesitas nada más.

class Names(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.fixed_names = {}  # {user_id: "forced_nick"}

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if after.id in self.fixed_names and after.nick != self.fixed_names[after.id]:
            try:
                await after.edit(nick=self.fixed_names[after.id], reason="Restoring forced nickname")
            except discord.Forbidden:
                pass
            except discord.HTTPException:
                pass

    @commands.command(name="fn", aliases=["forcenickname"])
    @commands.has_permissions(administrator=True)
    async def force_nickname(self, ctx, member: discord.Member, *, new_nick: str = None):
        """
        ,fn @user <nombre> → Fuerza apodo permanente
        ,fn @user          → Quita el apodo forzado
        """
        author_name = ctx.author.name

        # QUITAR apodo
        if new_nick is None:
            if member.id not in self.fixed_names:
                return await ctx.send(f"@{author_name}: {member.display_name} no tiene apodo forzado.")
            
            try:
                del self.fixed_names[member.id]
                await member.edit(nick=None, reason="Removed forced nickname")
                await ctx.send(f"@{author_name}: Removed forced nickname for {member.display_name}")
            except discord.Forbidden:
                await ctx.send("No tengo permisos para restaurar el apodo.")
            except discord.HTTPException as e:
                await ctx.send(f"Error: {e}")
            return

        # PONER apodo
        if len(new_nick) > 32:
            return await ctx.send("El apodo no puede tener más de 32 caracteres.")

        try:
            await member.edit(nick=new_nick, reason="Forced nickname by admin")
            self.fixed_names[member.id] = new_nick
            await ctx.send(f"@{author_name}: Forced nickname for {member} to `{new_nick}`")
        except discord.Forbidden:
            await ctx.send("No tengo permisos para cambiar el apodo.")
        except discord.HTTPException as e:
            await ctx.send(f"Error: {e}")

    @commands.command(name="removefn")
    @commands.has_permissions(administrator=True)
    async def remove_forced_nickname(self, ctx, member: discord.Member):
        """Alias de ,fn @user (sin nombre)"""
        await ctx.invoke(self.force_nickname, member=member)

# Setup
async def setup(bot):
    await bot.add_cog(Names(bot))
