import discord
from discord.ext import commands

class Names(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Diccionario para almacenar nombres fijos (user_id: nombre)
        self.fixed_names = {}

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Restaura el nombre fijo si se modifica."""
        user_id = after.id
        if user_id in self.fixed_names and after.nick != self.fixed_names[user_id]:
            try:
                await after.edit(nick=self.fixed_names[user_id])
                print(f"Restaurado nombre fijo para {after.name} a {self.fixed_names[user_id]}")
            except discord.Forbidden:
                print(f"No tengo permisos para restaurar el nombre de {after.name}")
            except discord.HTTPException as e:
                print(f"Error al restaurar nombre para {after.name}: {e}")

    @commands.command(name="rename")
    @commands.has_permissions(manage_nicknames=True)
    async def rename(self, ctx, member: discord.Member, *, new_nick):
        """Renombra a un usuario. Requiere permiso de gestionar motes."""
        try:
            await member.edit(nick=new_nick)
            await ctx.send(f"✅ {member.mention} ha sido renombrado a {new_nick}.")
        except discord.Forbidden:
            await ctx.send("❌ No tengo permisos para cambiar el mote de ese usuario.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Ocurrió un error: {e}")

    @commands.command(name="fn")
    @commands.has_permissions(administrator=True)
    async def fixed_name(self, ctx, member: discord.Member, *, new_nick):
        """Establece un nombre permanente. Solo para administradores."""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ Solo los administradores pueden usar este comando.")
            return
        try:
            await member.edit(nick=new_nick)
            self.fixed_names[member.id] = new_nick
            await ctx.send(f"✅ {member.mention} ahora tiene el nombre permanente {new_nick}.")
        except discord.Forbidden:
            await ctx.send("❌ No tengo permisos para cambiar el mote de ese usuario.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Ocurrió un error: {e}")

    @commands.command(name="removefn")
    @commands.has_permissions(administrator=True)
    async def remove_fixed_name(self, ctx, member: discord.Member):
        """Quita el nombre permanente. Solo para administradores."""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ Solo los administradores pueden usar este comando.")
            return
        try:
            if member.id in self.fixed_names:
                del self.fixed_names[member.id]
                await member.edit(nick=None)  # Restaura el nombre original
                await ctx.send(f"✅ Se ha quitado el nombre permanente de {member.mention}.")
            else:
                await ctx.send(f"❌ {member.mention} no tiene un nombre permanente.")
        except discord.Forbidden:
            await ctx.send("❌ No tengo permisos para cambiar el mote de ese usuario.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Ocurrió un error: {e}")

async def setup(bot):
    await bot.add_cog(Names(bot))
