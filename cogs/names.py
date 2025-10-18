import discord
from discord.ext import commands

class Names(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # ID del rol protegido (créalo manualmente en Discord y actualiza este ID)
        self.protected_role_id = 123456789012345678  # Reemplaza con el ID real del rol

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
        """Establece un nombre permanente protegido. Solo para administradores."""
        try:
            # Obtener o crear el rol protegido
            guild = ctx.guild
            protected_role = guild.get_role(self.protected_role_id)
            if not protected_role:
                protected_role = await guild.create_role(name="ProtectedName", hoist=True, mentionable=False)
                self.protected_role_id = protected_role.id
                await protected_role.edit(position=guild.me.top_role.position - 1)  # Coloca el rol justo debajo del bot

            # Asignar el rol y el mote
            await member.edit(nick=new_nick)
            await member.add_roles(protected_role)
            await ctx.send(f"✅ {member.mention} ahora tiene el nombre permanente {new_nick} protegido por el rol {protected_role.name}.")
        except discord.Forbidden:
            await ctx.send("❌ No tengo permisos suficientes para asignar roles o cambiar motes.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Ocurrió un error: {e}")

async def setup(bot):
    await bot.add_cog(Names(bot))
