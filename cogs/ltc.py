import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import asyncio
from PIL import Image, ImageDraw, ImageFont
import io
import qrcode
import json
import os
from typing import Optional

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
            except Exception as e:
                print(f"[LTC] Error cargando direcciones: {e}")
                return {}
        return {}

    def save_addresses(self):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.addresses, f, indent=2)
        except Exception as e:
            print(f"[LTC] Error guardando direcciones: {e}")

    async def get_ltc_price(self):
        try:
            async with self.session.get(
                "https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=usd,eur",
                timeout=10
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["litecoin"]["usd"], data["litecoin"]["eur"]
        except Exception as e:
            print(f"[LTC] Error obteniendo precio: {e}")
        return 75.0, 69.0  # fallback

    async def get_ltc_balance(self, address):
        try:
            url = f"https://api.blockcypher.com/v1/ltc/main/addrs/{address}/balance"
            async with self.session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    confirmed = data.get("balance", 0) / 1e8
                    unconfirmed = data.get("unconfirmed_balance", 0) / 1e8
                    total_received = data.get("total_received", 0) / 1e8
                    return confirmed, unconfirmed, total_received
        except Exception as e:
            print(f"[LTC] Error balance: {e}")
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
                            "hash": tx["hash"][:8] + "..."[:3],
                            "value": sum(
                                out["value"] for out in tx["outputs"]
                                if out.get("addresses") and address in out["addresses"]
                            ) / 1e8
                        }
                        for tx in txs if tx.get("outputs")
                    ]
        except Exception as e:
            print(f"[LTC] Error transacciones: {e}")
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
        address = address.strip()
        if not (address.startswith("L") or address.startswith("M")) or len(address) < 26:
            return await interaction.response.send_message(
                "Dirección LTC inválida. Debe empezar con `L` o `M` y tener al menos 26 caracteres.",
                ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)
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

        await interaction.followup.send(embed=embed, file=file, ephemeral=True)

    # =====================================================
    # /mybal
    # =====================================================
    @app_commands.command(name="mybal", description="Muestra tu balance LTC (usa /setltc primero).")
    async def mybal(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        address = self.addresses.get(user_id)

        if not address:
            return await interaction.response.send_message(
                "No has establecido tu dirección. Usa `/setltc <dirección>` primero.",
                ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)

        # Mensaje de carga
        loading_embed = discord.Embed(title="Cargando balance LTC...", color=discord.Color.blue())
        await interaction.followup.send(embed=loading_embed, ephemeral=True)

        # Obtener datos
        ltc_usd, ltc_eur = await self.get_ltc_price()
        confirmed, unconfirmed, total_received = await self.get_ltc_balance(address)
        txs = await self.get_ltc_transactions(address)

        if confirmed is None:
            error_embed = discord.Embed(
                title="Error",
                description="No se pudo obtener el balance. Dirección inválida o API caída.",
                color=discord.Color.red()
            )
            return await interaction.followup.send(embed=error_embed, ephemeral=True)

        # Calcular valores
        usd_c = confirmed * ltc_usd
        eur_c = confirmed * ltc_eur
        usd_u = unconfirmed * ltc_usd
        eur_u = unconfirmed * ltc_eur
        usd_t = total_received * ltc_usd
        eur_t = total_received * ltc_eur

        # Embed principal
        embed = discord.Embed(
            title="Litecoin Balance",
            color=discord.Color.from_rgb(52, 152, 219)
        )
        embed.add_field(name="Address", value=f"`{address}`", inline=False)

        embed.add_field(
            name="Confirmed Balance",
            value=f"{confirmed:,.8f} LTC\n"
                  f"${usd_c:,.2f} USD | €{eur_c:,.2f} EUR",
            inline=True
        )
        embed.add_field(
            name="Unconfirmed Balance",
            value=f"{unconfirmed:,.8f} LTC\n"
                  f"${usd_u:,.2f} USD | €{eur_u:,.2f} EUR",
            inline=True
        )
        embed.add_field(
            name="Total Received",
            value=f"{total_received:,.8f} LTC\n"
                  f"${usd_t:,.2f} USD | €{eur_t:,.2f} EUR",
            inline=False
        )

        # Últimas transacciones
        if txs:
            tx_lines = [
                f"`{t['hash']}` {t['value']:,.8f} LTC"
                for t in txs
            ]
            tx_text = "\n".join(tx_lines)
        else:
            tx_text = "No se encontraron transacciones recientes."

        embed.add_field(name="Last 5 Transactions", value=tx_text, inline=False)

        # Botones
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(
            label="Get Transaction Info",
            url=f"https://blockchair.com/litecoin/address/{address}",
            emoji="Info"
        ))
        view.add_item(discord.ui.Button(
            label="View on Explorer",
            url=f"https://blockchair.com/litecoin/address/{address}",
            emoji="Search"
        ))

        # QR Code
        qr_bytes = self.generate_qr(address)
        file = discord.File(qr_bytes, filename="ltc_qr.png")
        embed.set_image(url="attachment://ltc_qr.png")

        # Enviar
        await interaction.followup.send(embed=embed, view=view, file=file, ephemeral=True)


# =====================================================
# SETUP
# =====================================================
async def setup(bot):
    await bot.add_cog(LTC(bot))
    print("Cog 'ltc' cargado correctamente")
