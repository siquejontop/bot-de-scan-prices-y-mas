import discord
from discord.ext import commands
import datetime

class Snipe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.owner_id = 335596693603090434  # 👑 ID del dueño del bot
        # Diccionario para mensajes eliminados: {guild_id: {channel_id: [(content, author, timestamp, attachments, embeds)]}}
        self.sniped_messages = {}
        # Diccionario para mensajes editados: {guild_id: {channel_id: [(before, after, author, timestamp)]}}
        self.edited_messages = {}

    # Evento: Detectar mensajes eliminados
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if not message.guild or message.author.bot or not message.content.strip():
            return

        guild_id = message.guild.id
        channel_id = message.channel.id

        # Inicializar estructuras si no existen
        if guild_id not in self.sniped_messages:
            self.sniped_messages[guild_id] = {}
        if channel_id not in self.sniped_messages[guild_id]:
            self.sniped_messages[guild_id][channel_id] = []

        # Guardar el mensaje eliminado con adjuntos y embeds
        attachments = [a.url for a in message.attachments] if message.attachments else []
        embeds = [e.to_dict() for e in message.embeds] if message.embeds else []
        self.sniped_messages[guild_id][channel_id].append((
            message.content,
            message.author,
            datetime.datetime.now(datetime.timezone.utc),
            attachments,
            embeds
        ))

        # Limitar a los últimos 5 mensajes eliminados por canal
        if len(self.sniped_messages[guild_id][channel_id]) > 5:
            self.sniped_messages[guild_id][channel_id].pop(0)

        # Limpiar mensajes antiguos (más de 5 minutos)
        self._clean_old_snipes(guild_id, channel_id)

    # Evento: Detectar mensajes editados
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if not before.guild or before.author.bot or before.content == after.content:
            return

        guild_id = before.guild.id
        channel_id = before.channel.id

        if guild_id not in self.edited_messages:
            self.edited_messages[guild_id] = {}
        if channel_id not in self.edited_messages[guild_id]:
            self.edited_messages[guild_id][channel_id] = []

        self.edited_messages[guild_id][channel_id].append((
            before.content,
            after.content,
            before.author,
            datetime.datetime.now(datetime.timezone.utc)
        ))

        # Limitar a los últimos 5 mensajes editados por canal
        if len(self.edited_messages[guild_id][channel_id]) > 5:
            self.edited_messages[guild_id][channel_id].pop(0)

        # Limpiar mensajes antiguos (más de 5 minutos)
        self._clean_old_edits(guild_id, channel_id)

    def _clean_old_snipes(self, guild_id, channel_id):
        """Limpia mensajes snipados que tengan más de 5 minutos."""
        if guild_id in self.sniped_messages and channel_id in self.sniped_messages[guild_id]:
            self.sniped_messages[guild_id][channel_id] = [
                s for s in self.sniped_messages[guild_id][channel_id]
                if (datetime.datetime.now(datetime.timezone.utc) - s[2]).total_seconds() <= 300
            ]

    def _clean_old_edits(self, guild_id, channel_id):
        """Limpia mensajes editados que tengan más de 5 minutos."""
        if guild_id in self.edited_messages and channel_id in self.edited_messages[guild_id]:
            self.edited_messages[guild_id][channel_id] = [
                e for e in self.edited_messages[guild_id][channel_id]
                if (datetime.datetime.now(datetime.timezone.utc) - e[3]).total_seconds() <= 300
            ]

    # Comando: snipe (último mensaje eliminado)
    @commands.command(name="snipe")
    @commands.has_permissions(manage_messages=True)
    async def snipe(self, ctx):
        if ctx.author.id != self.owner_id and not ctx.author.guild_permissions.manage_messages:
            return await ctx.send(embed=discord.Embed(
                description="❌ No tienes permisos para usar este comando. (Requiere `manage_messages` o ser el dueño del bot)",
                color=discord.Color.red()
            ))

        guild_id = ctx.guild.id
        channel_id = ctx.channel.id

        if guild_id not in self.sniped_messages or not self.sniped_messages[guild_id].get(channel_id):
            return await ctx.send(embed=discord.Embed(
                description="ℹ️ No hay mensajes eliminados recientes en este canal.",
                color=discord.Color.blurple()
            ))

        content, author, timestamp, attachments, embeds = self.sniped_messages[guild_id][channel_id][-1]
        if not content and not attachments and not embeds:
            return await ctx.send(embed=discord.Embed(
                description="ℹ️ El último mensaje eliminado no tiene contenido, adjuntos ni embeds.",
                color=discord.Color.blurple()
            ))

        embed = discord.Embed(
            title="📡 Mensaje Snipado",
            description=content if content else "Sin contenido de texto",
            color=discord.Color.orange(),
            timestamp=timestamp
        )
        embed.set_author(name=f"{author.name}#{author.discriminator}", icon_url=author.avatar.url if author.avatar else None)
        embed.set_footer(text=f"Eliminado hace {(datetime.datetime.now(datetime.timezone.utc) - timestamp).total_seconds():.0f} segundos")

        if attachments:
            embed.add_field(name="Adjuntos", value="\n".join([f"[Archivo]({a})" for a in attachments]), inline=False)
        if embeds:
            embed.add_field(name="Embeds", value=f"Contiene {len(embeds)} embed(s)", inline=False)

        await ctx.send(embed=embed)
        self.sniped_messages[guild_id][channel_id].pop()  # Limpiar después de sniparlo

    # Comando: snipeall (historial de mensajes eliminados)
    @commands.command(name="snipeall")
    @commands.has_permissions(manage_messages=True)
    async def snipeall(self, ctx):
        if ctx.author.id != self.owner_id and not ctx.author.guild_permissions.manage_messages:
            return await ctx.send(embed=discord.Embed(
                description="❌ No tienes permisos para usar este comando. (Requiere `manage_messages` o ser el dueño del bot)",
                color=discord.Color.red()
            ))

        guild_id = ctx.guild.id
        channel_id = ctx.channel.id

        if guild_id not in self.sniped_messages or not self.sniped_messages[guild_id].get(channel_id):
            return await ctx.send(embed=discord.Embed(
                description="ℹ️ No hay mensajes eliminados recientes en este canal.",
                color=discord.Color.blurple()
            ))

        messages = self.sniped_messages[guild_id][channel_id]
        if not messages:
            return await ctx.send(embed=discord.Embed(
                description="ℹ️ No hay mensajes eliminados para mostrar.",
                color=discord.Color.blurple()
            ))

        class SnipePaginator(discord.ui.View):
            def __init__(self, messages):
                super().__init__(timeout=60)
                self.messages = messages
                self.page = 0

            async def update_message(self, interaction):
                msg = self.messages[self.page]
                content, author, timestamp, attachments, embeds = msg
                embed = discord.Embed(
                    title=f"📡 Mensaje Snipado (Página {self.page + 1}/{len(self.messages)})",
                    description=content if content else "Sin contenido de texto",
                    color=discord.Color.orange(),
                    timestamp=timestamp
                )
                embed.set_author(name=f"{author.name}#{author.discriminator}", icon_url=author.avatar.url if author.avatar else None)
                embed.set_footer(text=f"Eliminado hace {(datetime.datetime.now(datetime.timezone.utc) - timestamp).total_seconds():.0f} segundos")

                if attachments:
                    embed.add_field(name="Adjuntos", value="\n".join([f"[Archivo]({a})" for a in attachments]), inline=False)
                if embeds:
                    embed.add_field(name="Embeds", value=f"Contiene {len(embeds)} embed(s)", inline=False)

                await interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary)
            async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
                if self.page > 0:
                    self.page -= 1
                    await self.update_message(interaction)

            @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary)
            async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
                if self.page < len(self.messages) - 1:
                    self.page += 1
                    await self.update_message(interaction)

            @discord.ui.button(label="❌", style=discord.ButtonStyle.danger)
            async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.message.delete()

        view = SnipePaginator(messages)
        await view.update_message(ctx.interaction or await ctx.send(embed=discord.Embed(), view=view))

    # Comando: editsnipe (último mensaje editado)
    @commands.command(name="editsnipe")
    @commands.has_permissions(manage_messages=True)
    async def editsnipe(self, ctx):
        if ctx.author.id != self.owner_id and not ctx.author.guild_permissions.manage_messages:
            return await ctx.send(embed=discord.Embed(
                description="❌ No tienes permisos para usar este comando. (Requiere `manage_messages` o ser el dueño del bot)",
                color=discord.Color.red()
            ))

        guild_id = ctx.guild.id
        channel_id = ctx.channel.id

        if guild_id not in self.edited_messages or not self.edited_messages[guild_id].get(channel_id):
            return await ctx.send(embed=discord.Embed(
                description="ℹ️ No hay mensajes editados recientes en este canal.",
                color=discord.Color.blurple()
            ))

        before, after, author, timestamp = self.edited_messages[guild_id][channel_id][-1]
        if not before and not after:
            return await ctx.send(embed=discord.Embed(
                description="ℹ️ El último mensaje editado no tiene cambios significativos.",
                color=discord.Color.blurple()
            ))

        embed = discord.Embed(
            title="✍️ Mensaje Editado",
            description=f"**Antes:** {before or 'Sin contenido'}\n**Después:** {after or 'Sin contenido'}",
            color=discord.Color.purple(),
            timestamp=timestamp
        )
        embed.set_author(name=f"{author.name}#{author.discriminator}", icon_url=author.avatar.url if author.avatar else None)
        embed.set_footer(text=f"Editado hace {(datetime.datetime.now(datetime.timezone.utc) - timestamp).total_seconds():.0f} segundos")

        await ctx.send(embed=embed)
        self.edited_messages[guild_id][channel_id].pop()  # Limpiar después de sniparlo

async def setup(bot):
    await bot.add_cog(Snipe(bot))
  
