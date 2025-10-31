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

    async def get_ltc_price(self):
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
    @app_commands.command(name="setltc", description="Guarda tu dirección LTC")
    @app_commands.describe(address="Tu dirección (L o M)")
    async def setltc(self, interaction: discord.Interaction, address: str):
        address = address.strip()
        if not (address.startswith("L") or address.startswith("M")) or len(address) < 26:
            await interaction.response.send_message("Dirección inválida. Usa L o M.")
            return

        self.addresses[str(interaction.user.id)] = address
        self.save_addresses()

        qr = self.generate_qr(address)
        file = discord.File(qr, "qr.png")

        embed = discord.Embed(
            title="Dirección Guardada",
            description=f"`{address}`\nUsa `/mybal` para ver tu saldo.",
            color=discord.Color.green()
        )
        embed.set_image(url="attachment://qr.png")

        await interaction.response.send_message(embed=embed, file=file)

    # =====================================================
    # /mybal
    # =====================================================
    @app_commands.command(name="mybal", description="Muestra tu balance LTC")
    async def mybal(self, interaction: discord.Interaction):
        address = self.addresses.get(str(interaction.user.id))
        if not address:
            await interaction.response.send_message("Primero usa `/setltc <dirección>`")
            return

        await interaction.response.defer()  # Espera sin "cargando"

        usd, eur = await self.get_ltc_price()
        confirmed, unconfirmed, total = await self.get_ltc_balance(address)
        txs = await self.get_ltc_transactions(address)

        if confirmed is None:
            await interaction.followup.send("Error al obtener el balance.")
            return

        # === TEXTO SIMPLE ===
        embed = discord.Embed(title="Balance LTC", color=0x3498db)
        embed.add_field(name="Dirección", value=f"`{address}`", inline=False)

        embed.add_field(name="Confirmado", value=f"**{confirmed:,.8f} LTC**\n${confirmed*usd:,.2f}", inline=True)
        embed.add_field(name="Sin confirmar", value=f"**{unconfirmed:,.8f} LTC**\n${unconfirmed*usd:,.2f}", inline=True)
        embed.add_field(name="Total recibido", value=f"**{total:,.8f} LTC**\n${total*usd:,.2f}", inline=True)

        tx_text = "\n".join([f"`{t['hash']}` → {t['value']:.8f} LTC" for t in txs[:5]]) or "Sin transacciones"
        embed.add_field(name="Últimas 5 TX", value=tx_text, inline=False)

        # QR
        qr = self.generate_qr(address)
        file = discord.File(qr, "qr.png")
        embed.set_image(url="attachment://qr.png")

        # Botones
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(label="Blockchair", url=f"https://blockchair.com/litecoin/address/{address}", emoji="Link"))
        view.add_item(discord.ui.Button(label="Explorer", url=f"https://blockchair.com/litecoin/address/{address}", emoji="Magnifying Glass"))

        await interaction.followup.send(embed=embed, file=file, view=view)

    async def cog_unload(self):
        await self.session.close()


async def setup(bot):
    await bot.add_cog(LTC(bot))
