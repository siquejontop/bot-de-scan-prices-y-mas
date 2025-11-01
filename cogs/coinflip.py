import discord
from discord.ext import commands
import random
import logging

logger = logging.getLogger(__name__)

# ===============================
# 🎮 CLASE DE VISTA (BOTONES)
# ===============================
class TicTacToeView(discord.ui.View):
    def __init__(self, ctx, player1, player2):
        super().__init__(timeout=180)  # 3 min de inactividad
        self.ctx = ctx
        self.player1 = player1
        self.player2 = player2
        self.turn = player1
        self.symbols = {player1: "🔴", player2: "🔵"}
        self.board = [" " for _ in range(9)]
        self.game_over = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user not in [self.player1, self.player2]:
            await interaction.response.send_message("⚠️ No estás participando en esta partida.", ephemeral=True)
            return False
        if self.game_over:
            await interaction.response.send_message("🛑 El juego ya ha terminado.", ephemeral=True)
            return False
        if interaction.user != self.turn:
            await interaction.response.send_message(f"⏳ Es el turno de {self.turn.display_name}.", ephemeral=True)
            return False
        return True

    def check_winner(self):
        combos = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],
            [0, 3, 6], [1, 4, 7], [2, 5, 8],
            [0, 4, 8], [2, 4, 6]
        ]
        for combo in combos:
            if self.board[combo[0]] == self.board[combo[1]] == self.board[combo[2]] != " ":
                return True
        return False

    async def update_message(self, interaction):
        desc = (
            f"[ {self.player1.mention} vs {self.player2.mention} ]\n\n"
            f"Turno de {self.turn.mention} ({self.symbols[self.turn]})"
        )

        embed = discord.Embed(
            title="🎮 Tic Tac Toe",
            description=desc,
            color=discord.Color.pink()
        )
        await interaction.message.edit(embed=embed, view=self)

    @discord.ui.button(label=" ", style=discord.ButtonStyle.secondary, row=0)
    async def b1(self, interaction, button): await self.play(interaction, 0, button)

    @discord.ui.button(label=" ", style=discord.ButtonStyle.secondary, row=0)
    async def b2(self, interaction, button): await self.play(interaction, 1, button)

    @discord.ui.button(label=" ", style=discord.ButtonStyle.secondary, row=0)
    async def b3(self, interaction, button): await self.play(interaction, 2, button)

    @discord.ui.button(label=" ", style=discord.ButtonStyle.secondary, row=1)
    async def b4(self, interaction, button): await self.play(interaction, 3, button)

    @discord.ui.button(label=" ", style=discord.ButtonStyle.secondary, row=1)
    async def b5(self, interaction, button): await self.play(interaction, 4, button)

    @discord.ui.button(label=" ", style=discord.ButtonStyle.secondary, row=1)
    async def b6(self, interaction, button): await self.play(interaction, 5, button)

    @discord.ui.button(label=" ", style=discord.ButtonStyle.secondary, row=2)
    async def b7(self, interaction, button): await self.play(interaction, 6, button)

    @discord.ui.button(label=" ", style=discord.ButtonStyle.secondary, row=2)
    async def b8(self, interaction, button): await self.play(interaction, 7, button)

    @discord.ui.button(label=" ", style=discord.ButtonStyle.secondary, row=2)
    async def b9(self, interaction, button): await self.play(interaction, 8, button)

    async def play(self, interaction, index, button):
        # Movimiento
        if self.board[index] != " ":
            await interaction.response.send_message("🚫 Esa casilla ya está ocupada.", ephemeral=True)
            return

        symbol = self.symbols[self.turn]
        button.label = symbol
        button.disabled = True
        button.style = (
            discord.ButtonStyle.danger if symbol == "🔴" else discord.ButtonStyle.primary
        )
        self.board[index] = symbol

        # Verificar ganador
        if self.check_winner():
            self.game_over = True
            for b in self.children:
                b.disabled = True
            embed = discord.Embed(
                title="🏆 ¡Victoria!",
                description=f"{self.turn.mention} ha ganado la partida! 🎉",
                color=discord.Color.green()
            )
            await interaction.response.edit_message(embed=embed, view=self)
            return

        # Verificar empate
        if " " not in self.board:
            self.game_over = True
            for b in self.children:
                b.disabled = True
            embed = discord.Embed(
                title="🤝 ¡Empate!",
                description="No quedaron más movimientos disponibles.",
                color=discord.Color.orange()
            )
            await interaction.response.edit_message(embed=embed, view=self)
            return

        # Cambiar turno
        self.turn = self.player2 if self.turn == self.player1 else self.player1
        await interaction.response.defer()
        await self.update_message(interaction)

# ===============================
# ⚙️ COG PRINCIPAL
# ===============================
class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 🧩 Comando Tic Tac Toe
    @commands.command(name="tictactoe", aliases=["ttt"])
    async def tictactoe(self, ctx, opponent: discord.Member):
        if opponent == ctx.author:
            await ctx.send("❌ No puedes jugar contra ti mismo.")
            return
        if opponent.bot:
            await ctx.send("🤖 No puedes jugar contra bots.")
            return

        view = TicTacToeView(ctx, ctx.author, opponent)
        embed = discord.Embed(
            title="🎮 Tic Tac Toe",
            description=f"[ {ctx.author.mention} vs {opponent.mention} ]\n\nTurno de {ctx.author.mention} (🔴)",
            color=discord.Color.pink()
        )
        await ctx.send(embed=embed, view=view)

    # 💰 Comando Coinflip estilo Carl-bot
    @commands.command(aliases=["flip", "coin"])
    async def coinflip(self, ctx):
        resultado = random.choice(["Cara", "Cruz"])
        color = discord.Color.gold() if resultado == "Cara" else discord.Color.dark_gray()

        embed = discord.Embed(
            title="🪙 Lanzamiento de Moneda",
            description=f"{ctx.author.mention} lanzó una moneda y salió **{resultado}**!",
            color=color
        )
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/992/992703.png")
        embed.set_footer(
            text="Usa ,coinflip para volver a jugar",
            icon_url=ctx.author.avatar.url if ctx.author.avatar else discord.utils.MISSING
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Games(bot))
    logger.info("Games cog loaded")
