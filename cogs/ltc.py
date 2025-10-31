import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import json
import os
import qrcode
import io
from typing import Tuple


class LTC(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.file_path = "ltc_addresses.json"
        self.addresses = self.load_addresses()

    def load_addresses(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_addresses(self):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.addresses, f, indent=2)

    async def get_ltc_price(self) -> Tuple[float, float]:
        try:
            async with self.session.get(
                "https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=usd,eur",
                timeout=10
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["litecoin"]["usd"], data["litecoin"]["eur"]
        except:
            pass
        return 75.0, 69.0

    async def get_ltc_balance(self, address):
        try:
            url = f"https://api.blockcypher.com/v1/ltc/main/addrs/{address}/balance"
            async with self.session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return (
                        data.get("balance", 0) / 1e8,
                        data.get("unconfirmed_balance", 0) / 1e8,
                        data.get("total_received", 0) / 1e8
                    )
        except:
            pass
        return None, None, None

    async def get_ltc_transactions(self, address):
        try:
            url = f"https://api.blockcypher.com/v1/ltc/main/addrs/{address}/full"
            async with self.session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    txs = data.get("txs", [])[:5]
                    return [
                        {
                            "hash": tx["hash"][:10] + "...",
                            "value": sum(
                                o.get("value", 0) for o in tx.get("outputs", [])
                                if o.get("addresses") and address in o["addresses"]
                            ) / 1e8
                        }
                        for tx in txs
                    ]
        except:
            pass
        return []

    def generate_qr(self, address):
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(address)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        bio = io.BytesIO()
        img.save(bio, "PNG")
        bio.seek(0)
        return bio

    # =====================================================
    # /setltc
    # =====================================================
    @app_commands.command(name="setltc", description="Establece tu dirección de pago LTC.")
    @app_commands.describe(address="Tu dirección LTC (empieza con L o M)")
    async def setltc(self, interaction: discord.Interaction, address: str):
        address = address.strip()
        if not (address.startswith("L") or address.startswith("M")) or len(address) < 26:
            await interaction.response.send_message(
                "Dirección LTC inválida. Debe empezar con `L` o `M`."
            )
            return

        await interaction.response.defer()

        user_id = str(interaction.user.id)
        self.addresses[user_id] = address
        self.save_addresses()

        qr_bio = self.generate_qr(address)
        file = discord.File(qr_bio, "ltc_qr.png")

        embed = discord.Embed(
            title="Dirección LTC Guardada",
            description=f"**Dirección:** `{address}`\nUsa `/mybal` para ver tu balance.",
            color=discord.Color.green()
        )
        embed.set_image(url="attachment://ltc_qr.png")
        embed.set_footer(text=f"Guardado por {interaction.user.display_name}")

        await interaction.followup.send(embed=embed, file=file)

    # =====================================================
    # /mybal
    # =====================================================
    @app_commands.command(name="mybal", description="Muestra tu balance LTC (usa /setltc primero).")
    async def mybal(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        address = self.addresses.get(user_id)
        if not address:
            await interaction.response.send_message(
                "No has establecido tu dirección. Usa `/setltc <dirección>` primero."
            )
            return

        await interaction.response.defer()

        loading = discord.Embed(title="Cargando balance LTC...", color=discord.Color.blue())
        await interaction.followup.send(embed=loading)

        usd, eur = await self.get_ltc_price()
        confirmed, unconfirmed, total_received = await self.get_ltc_balance(address)
        txs = await self.get_ltc_transactions(address)

        if confirmed is None:
            error = discord.Embed(title="Error", description="No se pudo obtener el balance.", color=discord.Color.red())
            await interaction.followup.send(embed=error)
            return

        # === EMBED DE TEXTO PLANO ===
        embed = discord.Embed(
            title="Balance LTC",
            color=discord.Color.from_rgb(52, 152, 219)
        )

        # Dirección
        embed.add_field(name="Dirección", value=f"`{address}`", inline=False)

        # Balances
        embed.add_field(
            name="Confirmed Balance",
            value=f"**{confirmed:,.8f} LTC**\n"
                  f"${confirmed * usd:,.2f} USD\n"
                  f"€{confirmed * eur:,.2f} EUR",
            inline=True
        )
        embed.add_field(
            name="Unconfirmed Balance",
            value=f"**{unconfirmed:,.8f} LTC**\n"
                  f"${unconfirmed * usd:,.2f} USD\n"
                  f"€{unconfirmed * eur:,.2f} EUR",
            inline=True
        )
        embed.add_field(
            name="Total Received",
            value=f"**{total_received:,.8f} LTC**\n"
                  f"${total_received * usd:,.2f} USD\n"
                  f"€{total_received * eur:,.2f} EUR",
            inline=True
        )

        # Transacciones
        tx_text = ""
        for tx in txs[:5]:
            tx_text += f"`{tx['hash']}` → **{tx['value']:.8f} LTC** (${tx['value'] * usd:.2f})\n"
        if not tx_text:
            tx_text = "*Sin transacciones recientes.*"

        embed.add_field(name="Últimas 5 Transacciones", value=tx_text, inline=False)

        # QR
        qr_bio = self.generate_qr(address)
        file = discord.File(qr_bio, "ltc_qr.png")
        embed.set_image(url="attachment://ltc_qr.png")

        # Footer
        embed.set_footer(text=f"Balance de {interaction.user.display_name}")

        # Botones
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(
            label="Get Transaction Info", url=f"https://blockchair.com/litecoin/address/{address}", emoji="i"
        ))
        view.add_item(discord.ui.Button(
            label="View on Explorer", url=f"https://blockchair.com/litecoin/address/{address}", emoji="Search"
        ))

        await interaction.followup.send(embed=embed, file=file, view=view)

    async def cog_unload(self):
        await self.session.close()


async def setup(bot):
    cog = LTC(bot)
    await bot.add_cog(cog)
    print("Cog 'ltc' cargado (TEXTO PLANO + QR)")
