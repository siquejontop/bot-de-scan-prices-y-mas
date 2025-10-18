import discord
from discord.ext import commands

class Names(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # ID del rol protegido (créalo manualmente en Discord y actualiza este ID)
        self.protected_role_id = 123456789012345678  # Reemplaza con el ID real del rol
        # Diccionario para almacenar nombres fijos (user_id: nombre)
        self.fixed_names = {}

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Restaura el nombre fijo si se modifica y el usuario tiene el rol protegido."""
        protected_role = after.guild.get_role(self.protected_role_id)
        if not protected_role or protected_role not in after.roles:
            return

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
        """Establece un nombre permanente protegido. Solo para administradores."""
        try:
            # Obtener o crear el rol protegido
            guild = ctx.guild
            protected_role = guild.get_role(self.protected_role_id)
            if not protected_role:
                protected_role = await guild.create_role(name="ProtectedName", hoist=True, mentionable=False)
                self.protected_role_id = protected_role.id
                await protected_role.edit(position=guild.me.top_role.position - 1)  # Coloca el rol justo debajo del bot

            # Asignar el rol y el mote, y guardar el nombre fijo
            await member.edit(nick=new_nick)
            await member.add_roles(protected_role)
            self.fixed_names[member.id] = new_nick
            await ctx.send(f"✅ {member.mention} ahora tiene el nombre permanente {new_nick} protegido por el rol {protected_role.name}.")
        except discord.Forbidden:
            await ctx.send("❌ No tengo permisos suficientes para asignar roles o cambiar motes.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Ocurrió un error: {e}")

    @commands.command(name="removefn")
    @commands.has_permissions(administrator=True)
    async def remove_fixed_name(self, ctx, member: discord.Member):
        """Quita el nombre permanente y el rol protegido. Solo para administradores."""
        try:
            protected_role = ctx.guild.get_role(self.protected_role_id)
            if protected_role and protected_role in member.roles:
                await member.remove_roles(protected_role)
                if member.id in self.fixed_names:
                    del self.fixed_names[member.id]
                await member.edit(nick=None)  # Restaura el nombre original
                await ctx.send(f"✅ Se ha quitado el nombre permanente de {member.mention}.")
            else:
                await ctx.send(f"❌ {member.mention} no tiene un nombre permanente protegido.")
        except discord.Forbidden:
            await ctx.send("❌ No tengo permisos suficientes para quitar roles o cambiar motes.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Ocurrió un error: {e}")

async def setup(bot):
    await bot.add_cog(Names(bot))
