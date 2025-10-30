import discord
from discord.ext import commands
from datetime import datetime, timezone

from config import get_log_channel

# Función para calcular el tiempo en meses, días y horas
def time_difference_string(dt):
    now = datetime.now(timezone.utc)
    diff = now - dt
    months = diff.days // 30
    days = diff.days % 30
    hours = diff.seconds // 3600
    return f"{months} month(s) {days} day(s) and {hours} hour(s) ago"

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

        # Fetch del usuario completo (para obtener banner y nitro info)
        user = await self.bot.fetch_user(member.id)

        # === TIEMPOS ===
        created_diff = time_difference_string(member.created_at)
        joined_diff = time_difference_string(member.joined_at or datetime.now(timezone.utc))

        # === EMBED ===
        embed = discord.Embed(
            title=f"{member}",
            color=discord.Color.blurple(),
            timestamp=datetime.now(timezone.utc)
        )

        embed.set_author(name=member.name, icon_url=member.display_avatar.url)
        embed.set_thumbnail(url=member.display_avatar.url)

        # === FECHAS ===
        embed.add_field(
            name="Created",
            value=f"📅 {created_diff}\n`{member.created_at.strftime('%m/%d/%Y, %I:%M:%S %p')}`",
            inline=True
        )
        embed.add_field(
            name="Joined",
            value=f"📥 {joined_diff}\n`{member.joined_at.strftime('%m/%d/%Y, %I:%M:%S %p') if member.joined_at else 'Unknown'}`",
            inline=True
        )

        # === ID ===
        embed.add_field(name="ID", value=f"`{member.id}`", inline=False)

        # === ESTADO DE NITRO Y BADGES ===
        badges = []
        public_flags = getattr(user, "public_flags", None)
        if public_flags:
            flags = user.public_flags
            if flags.hypesquad_balance: badges.append("🏠 HypeSquad Balance")
            if flags.hypesquad_bravery: badges.append("🦁 HypeSquad Bravery")
            if flags.hypesquad_brilliance: badges.append("🦉 HypeSquad Brilliance")
            if flags.early_supporter: badges.append("🕊️ Early Supporter")
            if flags.verified_bot_developer or flags.early_verified_bot_developer: badges.append("👨‍💻 Verified Dev")
            if flags.staff: badges.append("🛠️ Discord Staff")

        # Nitro / Booster / Premium info
        if member.premium_since:
            badges.append("🚀 Server Booster")
        if user.avatar and user.avatar.is_animated():
            badges.append("💎 Nitro")

        embed.add_field(
            name="Badges",
            value=" | ".join(badges) if badges else "None",
            inline=False
        )

        # === LINKS ===
        avatar_url = user.display_avatar.url
        banner_url = user.banner.url if user.banner else None

        links = [f"[Avatar]({avatar_url})"]
        if banner_url:
            links.append(f"[Banner]({banner_url})")

        embed.add_field(
            name="Links",
            value=" | ".join(links),
            inline=False
        )

        # === FOOTER ===
        embed.set_footer(
            text=f"Account created {created_diff} | Joined {joined_diff}"
        )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Events(bot))
