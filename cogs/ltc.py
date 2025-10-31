# cogs/ltc.py
import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import asyncio
from PIL import Image
import io
import qrcode
import json
import os

class LTC(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.file_path = "ltc_addresses.json"
        self.addresses = self.load_addresses()

    def load_addresses(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_addresses(self):
        with open(self.file_path, "w") as f:
            json.dump(self.addresses, f, indent=2)

    async def get_ltc_price(self):
        try:
            async with self.session.get("https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=usd,eur") as resp:
                data = await resp.json()
                return data["litecoin"]["usd"], data["litecoin"]["eur"]
        except:
            return 75.0, 69.0  # Fallback

    async def get_ltc_balance(self, address):
        try:
            url = f"https://api.blockcypher.com/v1/ltc/main/addrs/{address}/balance"
            async with self.session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    confirmed = data.get("balance", 0) / 1e8
                    unconfirmed = data.get("unconfirmed_balance", 0) / 1e8
                    total_received = data.get("total_received", 0) / 1e8
                    return confirmed, unconfirmed, total_received
        except:
            pass
        return None, None, None

    async def get_ltc_transactions(self, address):
        try:
            url = f"https://api.blockcypher.com/v1/ltc/main/addrs/{address}/full"
            async with self.session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    txs = data.get("txs", [])[:5]
                    return [
                        {
                            "hash": tx["hash"][:8],
                            "value": sum(out["value"] for out in tx["outputs"] if out["addresses"] and out["addresses"][0] == address) / 1e8,
                            "time": tx.get("confirmed", tx.get("received", ""))
                        }
                        for tx in txs
                    ]
        except:
            pass
        return []

    def generate_qr(self, address):
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(address)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        bio = io.BytesIO()
        img.save(bio, 'PNG')
        bio.seek(0)
        return bio

    # =====================================================
    # /setltc
    # =====================================================
    @app_commands.command(name="setltc", description="Establece tu dirección de pago LTC.")
    @app_commands.describe(address="Tu dirección LTC (empieza con L o M)")
    async def setltc(self, interaction: discord.Interaction, address: str):
        if not (address.startswith("L") or address.startswith("M")) or len(address) < 26:
            return await interaction.response.send_message("Dirección LTC inválida. Debe empezar con `L` o `M`.", ephemeral=True)

        user_id = str(interaction.user.id)
        self.addresses[user_id] = address
        self.save_addresses()

        qr_bytes = self.generate_qr(address)
        file = discord.File(qr_bytes, filename="ltc_qr.png")

        embed = discord.Embed(
            title="Dirección LTC Guardada",
            description=f"**Dirección:** `{address}`\nUsa `/mybal` para ver tu balance.",
            color=discord.Color.green()
        )
        embed.set_image(url="attachment://ltc_qr.png")
        embed.set_footer(text="Solo tú puedes ver este mensaje.")
        await interaction.response.send_message(embed=embed, file=file, ephemeral=True)

    # =====================================================
    # /mybal
    # =====================================================
    @app_commands.command(name="mybal", description="Muestra tu balance LTC (usa /setltc primero).")
    async def mybal(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        address = self.addresses.get(user_id)
        if not address:
            return await interaction.response.send_message("No has establecido tu dirección. Usa `/setltc <dirección>` primero.", ephemeral=True)

        embed = discord.Embed(title="Cargando balance LTC...", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        msg = await interaction.original_response()

        ltc_usd, ltc_eur = await self.get_ltc_price()
        confirmed, unconfirmed, total_received = await self.get_ltc_balance(address)
        txs = await self.get_ltc_transactions(address)

        if confirmed is None:
            embed = discord.Embed(title="Error", description="No se pudo obtener el balance. Dirección inválida o API caída.", color=discord.Color.red())
            return await msg.edit(embed=embed)

        usd_c = confirmed * ltc_usd
        eur_c = confirmed * ltc_eur
        usd_u = unconfirmed * ltc_usd
        eur_u = unconfirmed * ltc_eur
        usd_t = total_received * ltc_usd
        eur_t = total_received * ltc_eur

        embed = discord.Embed(title="Balance LTC", color=discord.Color.from_rgb(52, 152, 219))
        embed.add_field(name="Dirección", value=f"`{address}`", inline=False)
        embed.add_field(
            name="Confirmado",
            value=f"{confirmed:,.8f} LTC\n${usd_c:,.2f} USD\n€{eur_c:,.2f} EUR",
            inline=True
        )
        embed.add_field(
            name="Sin Confirmar",
            value=f"{unconfirmed:,.8f} LTC\n${usd_u:,.2f} USD\n€{eur_u:,.2f} EUR",
            inline=True
        )
        embed.add_field(
            name="Total Recibido",
            value=f"{total_received:,.8f} LTC\n${usd_t:,.2f} USD\n€{eur_t:,.2f} EUR",
            inline=False
        )

        if txs:
            tx_text = "\n".join([f"`{t['hash']}...` {t['value']:,.4f} LTC" for t in txs])
            embed.add_field(name="Últimas 5 Transacciones", value=tx_text or "Ninguna", inline=False)
        else:
            embed.add_field(name="Últimas 5 Transacciones", value="No se encontraron.", inline=False)

        # BOTONES CORREGIDOS (EMOJIS UNICODE)
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Ver en Explorer", url=f"https://blockchair.com/litecoin/address/{address}", emoji="🔍"))
        view.add_item(discord.ui.Button(label="Info de Tx", url=f"https://blockchair.com/litecoin/address/{address}", emoji="ℹ️"))

        qr_bytes = self.generate_qr(address)
        file = discord.File(qr_bytes, filename="ltc_qr.png")
        embed.set_image(url="attachment://ltc_qr.png")

        await msg.edit(embed=embed, view=view, attachments=[file])

# =====================================================
# SETUP
# =====================================================
async def setup(bot):
    await bot.add_cog(LTC(bot))
    print("Cog 'ltc' cargado correctamente")
