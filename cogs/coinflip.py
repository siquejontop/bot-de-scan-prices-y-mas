import discord
from discord.ext import commands
import logging
import random

logger = logging.getLogger(__name__)

class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games = {}  # {channel_id: {'board': list, 'player1': user, 'player2': user, 'turn': user, 'symbol': str}}
        logger.info("Games cog initialized")

    @commands.command(name="tictactoe", aliases=["ttt"])
    async def start_game(self, ctx, opponent: discord.Member):
        if ctx.author == opponent:
            await ctx.send("No puedes jugar contra ti mismo! 😅")
            return
        if ctx.channel.id in self.games:
            await ctx.send("Ya hay un juego en curso en este canal. Usa `,quit` para cancelarlo. 🚫")
            return

        self.games[ctx.channel.id] = {
            'board': [' ' for _ in range(9)],
            'player1': ctx.author,
            'player2': opponent,
            'turn': ctx.author,
            'symbol': 'X'
        }
        await self.display_board(ctx)
        await ctx.send(f"{ctx.author.mention} (🔴) vs {opponent.mention} (🔵). ¡Comienza {ctx.author.mention}! Usa `,move <1-9>` para jugar. 🎮")

    @commands.command(name="move")
    async def make_move(self, ctx, position: int):
        if ctx.channel.id not in self.games:
            await ctx.send("No hay un juego en curso. Usa `,tictactoe @opponent` para empezar. 🎲")
            return
        game = self.games[ctx.channel.id]

        if ctx.author != game['turn']:
            await ctx.send(f"Es el turno de {game['turn'].mention}. ⏳")
            return

        if position < 1 or position > 9 or game['board'][position - 1] != ' ':
            await ctx.send("Movimiento inválido. Elige un número del 1 al 9 en una posición vacía. ❌")
            return

        game['board'][position - 1] = game['symbol']
        winner = self.check_winner(game['board'], game)
        if winner:
            await self.display_board(ctx)
            await ctx.send(f"¡{winner.mention} ha ganado! 🏆🎉")
            del self.games[ctx.channel.id]
            return

        if ' ' not in game['board']:
            await self.display_board(ctx)
            await ctx.send("¡Empate! 🙌")
            del self.games[ctx.channel.id]
            return

        game['turn'] = game['player2'] if game['turn'] == game['player1'] else game['player1']
        game['symbol'] = 'O' if game['symbol'] == 'X' else 'X'
        await self.display_board(ctx)
        await ctx.send(f"Turno de {game['turn'].mention} ({'🔴' if game['symbol'] == 'X' else '🔵'}). ⏩")

    @commands.command(name="quit")
    async def quit_game(self, ctx):
        if ctx.channel.id in self.games:
            del self.games[ctx.channel.id]
            await ctx.send("Juego cancelado. 😔")
        else:
            await ctx.send("No hay un juego en curso en este canal. 🎲")

    def check_winner(self, board, game):
        # Verificar filas
        for i in range(0, 9, 3):
            if board[i] == board[i + 1] == board[i + 2] != ' ':
                return game['player1'] if board[i] == 'X' else game['player2']
        # Verificar columnas
        for i in range(3):
            if board[i] == board[i + 3] == board[i + 6] != ' ':
                return game['player1'] if board[i] == 'X' else game['player2']
        # Verificar diagonales
        if board[0] == board[4] == board[8] != ' ':
            return game['player1'] if board[0] == 'X' else game['player2']
        if board[2] == board[4] == board[6] != ' ':
            return game['player1'] if board[2] == 'X' else game['player2']
        return None

    async def display_board(self, ctx):
        game = self.games[ctx.channel.id]
        board = game['board']
        embed = discord.Embed(
            title="🎲 Tic Tac Toe 🎲",
            description="Juega con tus amigos en este clásico juego!",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Tablero",
            value=f"```🔲 | 🔲 | 🔲\n---------\n🔲 | 🔲 | 🔲\n---------\n🔲 | 🔲 | 🔲```" if all(x == ' ' for x in board) else \
                  f"```{board[0]} | {board[1]} | {board[2]}\n---------\n{board[3]} | {board[4]} | {board[5]}\n---------\n{board[6]} | {board[7]} | {board[8]}```",
            inline=False
        )
        embed.set_footer(text=f"Turno de {game['turn'].mention} ({'🔴' if game['symbol'] == 'X' else '🔵'}) | Usa `,move <1-9>`",
                         icon_url=ctx.author.avatar.url if ctx.author.avatar else discord.utils.MISSING)
        embed.set_author(name=f"{game['player1'].name} (🔴) vs {game['player2'].name} (🔵)",
                         icon_url=game['player1'].avatar.url if game['player1'].avatar else discord.utils.MISSING)
        await ctx.send(embed=embed)

    @commands.command(aliases=["flip", "coin"])
    async def coinflip(self, ctx):
        resultados = ["cara", "cruz"]
        resultado = random.choice(resultados)
        embed = discord.Embed(
            title="🎰 Lanzando la moneda... 🎰",
            description=f"**Resultado:** {resultado.capitalize()}! 💰\n({resultado})",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url="https://i.imgur.com/7kQPRf8.png")  # URL de una imagen de moneda (puedes cambiarla)
        embed.set_footer(
            text=f"Solicitado por {ctx.author.name} | ¡Suerte la próxima vez! 🍀",
            icon_url=ctx.author.avatar.url if ctx.author.avatar else discord.utils.MISSING
        )
        await ctx.send(embed=embed)
        logger.info(f"Coinflip command executed by {ctx.author} in {ctx.guild}")

async def setup(bot):
    await bot.add_cog(Games(bot))
    logger.info("Games cog loaded")
