import discord
from discord.ext import commands
import requests
from datetime import datetime

class Crypto(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Lista de símbolos válidos (IDs de CoinGecko)
        self.valid_symbols = {
            "btc": "bitcoin", "eth": "ethereum", "ltc": "litecoin", "xmr": "monero",
            "doge": "dogecoin", "ada": "cardano", "sol": "solana", "bnb": "binancecoin"
        }

    @commands.command(name="helpcrypto")
    async def helpcrypto(self, ctx, *symbols):
        """
        Obtiene información detallada de criptomonedas.
        Uso: ,helpcrypto <símbolo1> [símbolo2 ...] (ej: ,helpcrypto eth ltc, ,helpcrypto btc)
        """
        if not symbols:
            embed = discord.Embed(
                title="ℹ️ Ayuda de ,helpcrypto",
                description="Usa este comando para ver precios y datos de criptomonedas.\n"
                            "Ejemplos: `,helpcrypto eth`, `,helpcrypto btc ltc`.\n"
                            "Símbolos válidos: btc, eth, ltc, xmr, doge, ada, sol, bnb.",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            await ctx.send(embed=embed)
            return

        # Normalizar y validar símbolos
        valid_symbols = []
        for sym in symbols:
            sym = sym.lower().strip()
            if sym in self.valid_symbols:
                valid_symbols.append(self.valid_symbols[sym])
            else:
                await ctx.send(f"⚠️ '{sym}' no es un símbolo válido. Usa: btc, eth, ltc, xmr, doge, ada, sol, bnb.")
                return

        if not valid_symbols:
            return

        # URL de la API de CoinGecko
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "ids": ",".join(valid_symbols),
            "price_change_percentage": "24h",
            "order": "market_cap_desc"
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data:
                embed = discord.Embed(
                    title="❌ Datos no encontrados",
                    description="No se pudo obtener información de las criptomonedas solicitadas.",
                    color=discord.Color.red(),
                    timestamp=datetime.utcnow()
                )
                await ctx.send(embed=embed)
                return

            for crypto in data:
                symbol = next(k for k, v in self.valid_symbols.items() if v == crypto["id"])
                price = crypto["current_price"]
                change_24h = crypto["price_change_percentage_24h"]
                high_24h = crypto["high_24h"]
                low_24h = crypto["low_24h"]
                market_cap = crypto["market_cap"]
                volume_24h = crypto["total_volume"]
                last_updated = datetime.fromtimestamp(crypto["last_updated"]).strftime("%Y-%m-%d %H:%M:%S UTC")

                # Color del embed basado en el cambio
                color = discord.Color.green() if change_24h >= 0 else discord.Color.red()

                embed = discord.Embed(
                    title=f"💰 {symbol.upper()} - Precio Actual",
                    description=f"**Precio:** ${price:,.2f} USD\n"
                                f"**Cambio 24h:** {change_24h:+.2f}%\n"
                                f"**Máximo 24h:** ${high_24h:,.2f} USD\n"
                                f"**Mínimo 24h:** ${low_24h:,.2f} USD\n"
                                f"**Market Cap:** ${market_cap:,.0f} USD\n"
                                f"**Volumen 24h:** ${volume_24h:,.0f} USD\n"
                                f"**Última actualización:** {last_updated}",
                    color=color,
                    timestamp=datetime.utcnow()
                )
                embed.set_thumbnail(url=crypto["image"])  # Icono dinámico de la cripto
                await ctx.send(embed=embed)

        except requests.exceptions.RequestException as e:
            embed = discord.Embed(
                title="⚠️ Error en la API",
                description="No pude obtener los datos en este momento. Intenta de nuevo más tarde.",
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
            await ctx.send(embed=embed)
            print(f"Error en helpcrypto command: {e}")  # Log para depuración

async def setup(bot):
    await bot.add_cog(Crypto(bot))
