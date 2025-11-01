import discord
from discord.ext import commands
import datetime
import logging
from typing import List, Optional, Set, Union
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========================
# 📌 Role Selection View
# ========================
class RoleSelect(discord.ui.View):
    """View for selecting a role from multiple matches."""
    def __init__(self, ctx: commands.Context, roles: List[discord.Role], member: discord.Member, action: str):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.member = member
        self.action = action.lower()

        options = [
            discord.SelectOption(label=r.name, value=str(r.id), description=f"Position: {r.position}")
            for r in roles[:25]
        ]

        self.select = discord.ui.Select(
            placeholder="Select a role...",
            options=options,
            min_values=1,
            max_values=1
        )
        self.select.callback = self.select_callback
        self.add_item(self.select)

    async def select_callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message(
                "❌ Only the command issuer can use this menu.", ephemeral=True
            )

        role_id = int(self.select.values[0])
        role = self.ctx.guild.get_role(role_id)
        cog = self.ctx.bot.get_cog("Roles")
        
        try:
            ok, error = await cog.validate_role_action(self.ctx, self.member, role, self.action)
            if not ok:
                return await interaction.response.edit_message(
                    embed=discord.Embed(description=error, color=discord.Color.red()), view=None
                )

            desc, color = await cog.perform_role_action(self.member, role, self.action)
            await interaction.response.edit_message(
                embed=discord.Embed(description=desc, color=color), view=None
            )
            logger.info(f"Role {self.action} executed by {self.ctx.author} for {self.member}: {role.name}")

        except discord.Forbidden:
            await interaction.response.edit_message(
                embed=discord.Embed(description="❌ Insufficient permissions.", color=discord.Color.red()), view=None
            )
        except discord.HTTPException as e:
            await interaction.response.edit_message(
                embed=discord.Embed(description=f"❌ Error: {e}", color=discord.Color.red()), view=None
            )
            logger.error(f"Error in role {self.action}: {e}")

# ========================
# 📜 Roles Paginator View
# ========================
class RolesPaginator(discord.ui.View):
    """View for paginating server roles."""
    def __init__(self, roles: List[discord.Role], chunk_size: int = 10):
        super().__init__(timeout=120)
        self.roles = roles
        self.page = 0
        self.chunk_size = chunk_size

    def get_page_content(self) -> discord.Embed:
        start = self.page * self.chunk_size
        end = start + self.chunk_size
        chunk = self.roles[start:end]

        description = "\n".join(
            [f"**{i+1}.** {r.mention} (ID: {r.id})" for i, r in enumerate(chunk, start=start)]
        ) or "No roles on this page."

        embed = discord.Embed(
            title="📜 Server Roles",
            description=description,
            color=discord.Color.blurple(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.set_footer(
            text=f"Page {self.page+1}/{max(1, (len(self.roles)-1)//self.chunk_size+1)} "
                 f"({len(self.roles)} roles total)"
        )
        return embed

    @discord.ui.button(label="⬅️ Previous", style=discord.ButtonStyle.secondary)
    async def previous_page(self, interaction, button):
        if self.page > 0:
            self.page -= 1
            await interaction.response.edit_message(embed=self.get_page_content(), view=self)

    @discord.ui.button(label="Next ➡️", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction, button):
        if (self.page + 1) * self.chunk_size < len(self.roles):
            self.page += 1
            await interaction.response.edit_message(embed=self.get_page_content(), view=self)

    @discord.ui.button(label="❌ Close", style=discord.ButtonStyle.danger)
    async def close(self, interaction, button):
        await interaction.message.delete()

# ========================
# 📜 Roles Cog
# ========================
class Roles(commands.Cog):
    """Cog for managing Discord server roles."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.owner_id = 335596693603090434
        logger.info("Roles cog initialized")

    async def validate_role_action(self, ctx, member, role, action):
        author = ctx.author
        bot_member = ctx.guild.me

        if author.id == self.owner_id:
            return True, None

        if member == author and role >= author.top_role:
            return False, f"❌ Cannot assign/remove a role equal to or higher than your top role ({role.mention})."

        if member != author and member.top_role >= author.top_role:
            return False, f"❌ Cannot modify roles for someone with a higher or equal top role ({member.top_role.mention})."

        if role >= bot_member.top_role:
            return False, f"❌ Cannot modify a role higher than or equal to my top role ({bot_member.top_role.mention})."

        if action not in ("add", "remove", "toggle", "delete"):
            return False, "❌ Invalid action specified."

        return True, None

    async def perform_role_action(self, member, role, action):
        if action == "add":
            await member.add_roles(role, reason=f"added by bot")
            return f"➕ {member.mention} now has {role.mention}", discord.Color.green()

        elif action == "remove":
            await member.remove_roles(role, reason=f"removed by bot")
            return f"➖ {member.mention} no longer has {role.mention}", discord.Color.red()

        else:
            if role in member.roles:
                await member.remove_roles(role, reason=f"toggle removed by bot")
                return f"➖ {member.mention} no longer has {role.mention}", discord.Color.red()
            else:
                await member.add_roles(role, reason=f"toggle added by bot")
                return f"➕ {member.mention} now has {role.mention}", discord.Color.green()

    def find_role(self, ctx, role_arg):
        role_arg = role_arg.strip()
        if role_arg.isdigit():
            return ctx.guild.get_role(int(role_arg))
        role_arg = role_arg.lower()
        matches = [r for r in ctx.guild.roles if role_arg in r.name.lower()]
        return matches[0] if len(matches) == 1 else matches if matches else None

    def find_member(self, ctx, member_arg):
        member_arg = member_arg.strip()
        if member_arg.isdigit() or member_arg.startswith("<@"):
            member_id = int(re.sub(r"[<@!>]", "", member_arg))
            return ctx.guild.get_member(member_id)
        return discord.utils.find(
            lambda m: m.name.lower() == member_arg.lower() or (m.nick and m.nick.lower() == member_arg.lower()),
            ctx.guild.members
        )

    # ========================
    # ✅ Commands (tus comandos tal cual)
    # ========================
    # NO CAMBIÉ NINGUNO  
    # SOLO AÑADÍ MANEJO DE ERRORES ABAJO

    @commands.command(name="roles")
    async def roles(self, ctx):
        roles = sorted(ctx.guild.roles[1:], key=lambda r: r.position, reverse=True)
        if not roles:
            return await ctx.send(embed=discord.Embed(
                description="❌ No roles found (excluding @everyone).",
                color=discord.Color.red()
            ))

        view = RolesPaginator(roles)
        await ctx.send(embed=view.get_page_content(), view=view)
        logger.info(f"Roles command executed by {ctx.author} in {ctx.guild}")

    @commands.command(name="addrole", aliases=["addr", "ar"])
    @commands.has_permissions(manage_roles=True)
    async def addrole(self, ctx, member_arg: str, *, role_arg: str):
        member = self.find_member(ctx, member_arg)
        if not member:
            return await ctx.send(embed=discord.Embed(
                description=f"❌ User **{member_arg}** not found.",
                color=discord.Color.red()
            ))

        role = self.find_role(ctx, role_arg)
        if not role:
            return await ctx.send(embed=discord.Embed(
                description=f"❌ Role **{role_arg}** not found.",
                color=discord.Color.red()
            ))
        if isinstance(role, list):
            return await ctx.send("🔎 Multiple roles found, select one:", view=RoleSelect(ctx, role, member, "add"))

        ok, error = await self.validate_role_action(ctx, member, role, "add")
        if not ok:
            return await ctx.send(embed=discord.Embed(description=error, color=discord.Color.red()))

        try:
            desc, color = await self.perform_role_action(member, role, "add")
            await ctx.send(embed=discord.Embed(description=desc, color=color))
            logger.info(f"Role added by {ctx.author} to {member}: {role.name}")
        except discord.Forbidden:
            await ctx.send(embed=discord.Embed(
                description="❌ Insufficient permissions to assign role.",
                color=discord.Color.red()
            ))
        except discord.HTTPException as e:
            await ctx.send(embed=discord.Embed(
                description=f"❌ Error assigning role: {e}",
                color=discord.Color.red()
            ))
            logger.error(f"Error adding role: {e}")

    @commands.command(name="addroles", aliases=["addrs", "ars"])
    @commands.has_permissions(manage_roles=True)
    async def addroles(self, ctx, member_arg: str, *, roles_arg: str):
        member = self.find_member(ctx, member_arg)
        if not member:
            return await ctx.send(embed=discord.Embed(
                description=f"❌ User **{member_arg}** not found.",
                color=discord.Color.red()
            ))

        role_names = [r.strip() for r in roles_arg.split(",")]
        roles: List[discord.Role] = []
        for role_arg in role_names:
            role = self.find_role(ctx, role_arg)
            if not role:
                return await ctx.send(embed=discord.Embed(
                    description=f"❌ Role **{role_arg}** not found.",
                    color=discord.Color.red()
                ))
            if isinstance(role, list):
                return await ctx.send(f"🔎 Multiple roles found for **{role_arg}**:", view=RoleSelect(ctx, role, member, "add"))
            roles.append(role)

        for role in roles:
            ok, error = await self.validate_role_action(ctx, member, role, "add")
            if not ok:
                return await ctx.send(embed=discord.Embed(description=error, color=discord.Color.red()))

        try:
            await member.add_roles(*roles)
            roles_mention = ", ".join([role.mention for role in roles])
            embed = discord.Embed(
                description=f"➕ {ctx.author.mention} added {roles_mention} to {member.mention}",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
            logger.info(f"Multiple roles added by {ctx.author} to {member}: {roles_mention}")
        except discord.Forbidden:
            await ctx.send(embed=discord.Embed(
                description="❌ Insufficient permissions to assign roles.",
                color=discord.Color.red()
            ))
        except discord.HTTPException as e:
            await ctx.send(embed=discord.Embed(
                description=f"❌ Error assigning roles: {e}",
                color=discord.Color.red()
            ))
            logger.error(f"Error adding multiple roles: {e}")

    @commands.command(name="removerole", aliases=["rr", "remrole"])
    @commands.has_permissions(manage_roles=True)
    async def removerole(self, ctx, member_arg: str, *, role_arg: str):
        member = self.find_member(ctx, member_arg)
        if not member:
            return await ctx.send(embed=discord.Embed(
                description=f"❌ User **{member_arg}** not found.",
                color=discord.Color.red()
            ))

        role = self.find_role(ctx, role_arg)
        if not role:
            return await ctx.send(embed=discord.Embed(
                description=f"❌ Role **{role_arg}** not found.",
                color=discord.Color.red()
            ))
        if isinstance(role, list):
            return await ctx.send("🔎 Multiple roles found, select one:", view=RoleSelect(ctx, role, member, "remove"))

        ok, error = await self.validate_role_action(ctx, member, role, "remove")
        if not ok:
            return await ctx.send(embed=discord.Embed(description=error, color=discord.Color.red()))

        try:
            desc, color = await self.perform_role_action(member, role, "remove")
            await ctx.send(embed=discord.Embed(description=desc, color=color))
            logger.info(f"Role removed by {ctx.author} from {member}: {role.name}")
        except discord.Forbidden:
            await ctx.send(embed=discord.Embed(
                description="❌ Insufficient permissions to remove role.",
                color=discord.Color.red()
            ))
        except discord.HTTPException as e:
            await ctx.send(embed=discord.Embed(
                description=f"❌ Error removing role: {e}",
                color=discord.Color.red()
            ))
            logger.error(f"Error removing role: {e}")

    @commands.command(name="purgeroles", aliases=["clearroles", "pr"])
    @commands.has_permissions(manage_roles=True)
    async def purgeroles(self, ctx, member_arg: str):
        member = self.find_member(ctx, member_arg)
        if not member:
            return await ctx.send(embed=discord.Embed(
                description=f"❌ User **{member_arg}** not found.",
                color=discord.Color.red()
            ))

        roles_to_remove = [role for role in member.roles if role != ctx.guild.default_role]
        if not roles_to_remove:
            return await ctx.send(embed=discord.Embed(
                description=f"ℹ️ {member.mention} has no roles to remove.",
                color=discord.Color.blurple()
            ))

        for role in roles_to_remove:
            ok, error = await self.validate_role_action(ctx, member, role, "remove")
            if not ok:
                return await ctx.send(embed=discord.Embed(description=error, color=discord.Color.red()))

        try:
            await member.remove_roles(*roles_to_remove)
            embed = discord.Embed(
                description=f"🗑️ {ctx.author.mention} removed all roles from {member.mention}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            logger.info(f"All roles removed by {ctx.author} from {member}")
        except discord.Forbidden:
            await ctx.send(embed=discord.Embed(
                description="❌ Insufficient permissions to remove roles.",
                color=discord.Color.red()
            ))
        except discord.HTTPException as e:
            await ctx.send(embed=discord.Embed(
                description=f"❌ Error removing roles: {e}",
                color=discord.Color.red()
            ))
            logger.error(f"Error purging roles: {e}")

    @commands.command(name="togglerole", aliases=["r", "role"])
    @commands.has_permissions(manage_roles=True)
    async def toggle_role(self, ctx, member_arg: str, *, role_arg: str):
        member = self.find_member(ctx, member_arg)
        if not member:
            return await ctx.send(embed=discord.Embed(
                description=f"❌ User **{member_arg}** not found.",
                color=discord.Color.red()
            ))

        role = self.find_role(ctx, role_arg)
        if not role:
            return await ctx.send(embed=discord.Embed(
                description=f"❌ Role **{role_arg}** not found.",
                color=discord.Color.red()
            ))
        if isinstance(role, list):
            return await ctx.send("🔎 Multiple roles found, select one:", view=RoleSelect(ctx, role, member, "toggle"))

        ok, error = await self.validate_role_action(ctx, member, role, "toggle")
        if not ok:
            return await ctx.send(embed=discord.Embed(description=error, color=discord.Color.red()))

        try:
            desc, color = await self.perform_role_action(member, role, "toggle")
            await ctx.send(embed=discord.Embed(description=desc, color=color))
            logger.info(f"Role toggled by {ctx.author} for {member}: {role.name}")
        except discord.Forbidden:
            await ctx.send(embed=discord.Embed(
                description="❌ Insufficient permissions to modify role.",
                color=discord.Color.red()
            ))
        except discord.HTTPException as e:
            await ctx.send(embed=discord.Embed(
                description=f"❌ Error modifying role: {e}",
                color=discord.Color.red()
            ))
            logger.error(f"Error toggling role: {e}")

    @commands.command(name="restoreroles", aliases=["rrs", "restorer"])
    @commands.has_permissions(manage_roles=True)
    async def restoreroles(self, ctx, member_arg: str):
        member = self.find_member(ctx, member_arg)
        if not member:
            return await ctx.send(embed=discord.Embed(
                description=f"❌ User **{member_arg}** not found.",
                color=discord.Color.red()
            ))

        after_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
        role_changes = []
        async for entry in ctx.guild.audit_logs(limit=100, after=after_time, action=discord.AuditLogAction.member_role_update):
            if entry.target.id == member.id:
                role_changes.append(entry)

        if not role_changes:
            return await ctx.send(embed=discord.Embed(
                description=f"ℹ️ No role changes found for {member.mention} in the last hour.",
                color=discord.Color.blurple()
            ))

        target_roles: Set[discord.Role] = set(role_changes[0].before.roles) if role_changes[0].before else set(member.roles) - {ctx.guild.default_role}
        current_roles: Set[discord.Role] = set(member.roles) - {ctx.guild.default_role}
        roles_to_add = target_roles - current_roles
        roles_to_remove = current_roles - target_roles

        for role in roles_to_add | roles_to_remove:
            ok, error = await self.validate_role_action(ctx, member, role, "toggle")
            if not ok:
                return await ctx.send(embed=discord.Embed(description=error, color=discord.Color.red()))

        try:
            if roles_to_add or roles_to_remove:
                if roles_to_remove:
                    await member.remove_roles(*roles_to_remove)
                if roles_to_add:
                    await member.add_roles(*roles_to_add)
                roles_added_str = ", ".join([role.mention for role in roles_to_add]) if roles_to_add else "none"
                roles_removed_str = ", ".join([role.mention for role in roles_to_remove]) if roles_to_remove else "none"
                embed = discord.Embed(
                    description=f"🕰️ {ctx.author.mention} restored roles for {member.mention}\n**Added**: {roles_added_str}\n**Removed**: {roles_removed_str}",
                    color=discord.Color.green()
                )
            else:
                embed = discord.Embed(
                    description=f"ℹ️ No changes needed to restore roles for {member.mention}.",
                    color=discord.Color.blurple()
                )
            await ctx.send(embed=embed)
            logger.info(f"Roles restored by {ctx.author} for {member}")
        except discord.Forbidden:
            await ctx.send(embed=discord.Embed(
                description="❌ Insufficient permissions to restore roles.",
                color=discord.Color.red()
            ))
        except discord.HTTPException as e:
            await ctx.send(embed=discord.Embed(
                description=f"❌ Error restoring roles: {e}",
                color=discord.Color.red()
            ))
            logger.error(f"Error restoring roles: {e}")

    @commands.command(name="createrole", aliases=["cr", "newrole"])
    @commands.has_permissions(manage_roles=True)
    async def createrole(self, ctx, name: str, color: str = None, hoist: bool = False, mentionable: bool = False):
        try:
            role_color = discord.Color.default()
            if color:
                if color.startswith("#"):
                    color = color.lstrip("#")
                    role_color = discord.Color(int(color, 16))
                elif "," in color:
                    r, g, b = map(int, color.split(","))
                    role_color = discord.Color.from_rgb(r, g, b)

            role = await ctx.guild.create_role(
                name=name[:100],
                color=role_color,
                hoist=hoist,
                mentionable=mentionable,
                reason=f"Role created by {ctx.author}"
            )
            embed = discord.Embed(
                description=f"✅ Created role {role.mention} successfully!",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
            logger.info(f"Role {name} created by {ctx.author}")
        except (ValueError, discord.InvalidArgument):
            await ctx.send(embed=discord.Embed(
                description="❌ Invalid color format. Use hex (#FF0000) or RGB (255,0,0).",
                color=discord.Color.red()
            ))
        except discord.Forbidden:
            await ctx.send(embed=discord.Embed(
                description="❌ Insufficient permissions to create role.",
                color=discord.Color.red()
            ))
        except discord.HTTPException as e:
            await ctx.send(embed=discord.Embed(
                description=f"❌ Error creating role: {e}",
                color=discord.Color.red()
            ))
            logger.error(f"Error creating role: {e}")

    @commands.command(name="deleterole", aliases=["deleter", "rmrole"])
    @commands.has_permissions(manage_roles=True)
    async def deleterole(self, ctx, *, role_arg: str):
        role = self.find_role(ctx, role_arg)
        if not role:
            return await ctx.send(embed=discord.Embed(
                description=f"❌ Role **{role_arg}** not found.",
                color=discord.Color.red()
            ))
        if isinstance(role, list):
            return await ctx.send("🔎 Multiple roles found, select one:", view=RoleSelect(ctx, role, ctx.author, "delete"))

        ok, error = await self.validate_role_action(ctx, ctx.author, role, "delete")
        if not ok:
            return await ctx.send(embed=discord.Embed(description=error, color=discord.Color.red()))

        try:
            await role.delete(reason=f"Role deleted by {ctx.author}")
            embed = discord.Embed(
                description=f"🗑️ Role {role.name} deleted successfully.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            logger.info(f"Role {role.name} deleted by {ctx.author}")
        except discord.Forbidden:
            await ctx.send(embed=discord.Embed(
                description="❌ Insufficient permissions to delete role.",
                color=discord.Color.red()
            ))
        except discord.HTTPException as e:
            await ctx.send(embed=discord.Embed(
                description=f"❌ Error deleting role: {e}",
                color=discord.Color.red()
            ))
            logger.error(f"Error deleting role: {e}")

    # =====================================================
    # ✅ MANEJO DE ERRORES — NO TOCA NADA MÁS
    # =====================================================

    @addrole.error
    async def addrole_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send("❌ Uso: `,addrole <usuario> <rol>`")

    @removerole.error
    async def removerole_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send("❌ Uso: `,removerole <usuario> <rol>`")

    @toggle_role.error
    async def toggle_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send("❌ Uso: `,role <usuario> <rol>`")

    @purgeroles.error
    async def purgeroles_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send("❌ Uso: `,purgeroles <usuario>`")

    @createrole.error
    async def createrole_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send("❌ Uso: `,createrole <nombre> [color] [hoist] [mentionable]`")

    @deleterole.error
    async def deleterole_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send("❌ Uso: `,deleterole <rol>`")

async def setup(bot):
    await bot.add_cog(Roles(bot))
    logger.info("Roles cog loaded")
