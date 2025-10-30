import discord
from discord.ext import commands
from datetime import datetime, timezone

from config import get_log_channel

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # === EVENTOS ===
    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = get_log_channel(member.guild)
        if channel:
            embed = discord.Embed(
                title=f"✅ {member} se unió",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="Cuenta creada", value=member.created_at.strftime("%d/%m/%Y %H:%M"))
            embed.add_field(name="ID", value=member.id)
            embed.set_thumbnail(url=member.display_avatar.url)
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        channel = get_log_channel(member.guild)
        if channel:
            embed = discord.Embed(
                title=f"❌ {member} salió",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="Se unió el", value=member.joined_at.strftime("%d/%m/%Y %H:%M") if member.joined_at else "Desconocido")
            embed.add_field(name="ID", value=member.id)
            embed.set_thumbnail(url=member.display_avatar.url)
            await channel.send(embed=embed)

    # === COMANDO UID ===
    @commands.command(name="uid")
    async def uid(self, ctx, member: discord.Member = None):
        member = member or ctx.author

        created_ago = datetime.now(timezone.utc) - member.created_at
        joined_ago = datetime.now(timezone.utc) - (member.joined_at or datetime.now(timezone.utc))

        embed = discord.Embed(
            title=f"{member}",
            color=discord.Color.blurple(),
            timestamp=datetime.now(timezone.utc)
        )

        embed.set_author(
            name=member.name,
            icon_url=member.display_avatar.url
        )
        embed.set_thumbnail(url=member.display_avatar.url)

        # Datos del usuario
        embed.add_field(
            name="🆔 ID",
            value=f"`{member.id}`",
            inline=False
        )

        embed.add_field(
            name="🗓️ Cuenta creada",
            value=f"<t:{int(member.created_at.timestamp())}:F>\n({created_ago.days} días atrás)",
            inline=True
        )

        embed.add_field(
            name="📥 Se unió al servidor",
            value=(f"<t:{int(member.joined_at.timestamp())}:F>\n({joined_ago.days} días atrás)"
                   if member.joined_at else "Desconocido"),
            inline=True
        )

        # Avatar y Banner (si hay)
        avatar_url = member.avatar.url if member.avatar else None
        banner_url = None
        try:
            user = await ctx.bot.fetch_user(member.id)
            banner_url = user.banner.url if user.banner else None
        except:
            pass

        links = []
        if avatar_url:
            links.append(f"[Avatar]({avatar_url})")
        if banner_url:
            links.append(f"[Banner]({banner_url})")

        embed.add_field(name="🔗 Links", value=" | ".join(links) if links else "Ninguno", inline=False)

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Events(bot))
