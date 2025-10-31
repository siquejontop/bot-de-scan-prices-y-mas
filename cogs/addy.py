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
from datetime import datetime

class LTC(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        # Almacenamiento simple (user_id: address). En producción, usa DB.
        self.addresses = {}  # Carga desde JSON si existe

    def cog_load(self):
        # Cargar direcciones desde archivo (opcional)
        try:
            with open("ltc_addresses.json", "r") as f:
                self.addresses = json.load(f)
        except FileNotFoundError:
            self.addresses = {}

    def cog_unload(self):
        # Guardar direcciones
        with open("ltc_addresses.json", "w") as f:
            json.dump(self.addresses, f)
        asyncio.create_task(self.session.close())

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
                            "hash": tx["hash"],
                            "time": tx.get("confirmed", tx.get("received", "")),
                            "value": sum(out["value"] for out in tx["outputs"] if out["addresses"] and out["addresses"][0] == address) / 1e8
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

    @app_commands.command(name="setltc", description="Establece tu dirección de pago LTC.")
    @app_commands.describe(address="Tu dirección LTC (empieza con L o M)")
    async def setltc(self, interaction: discord.Interaction, address: str):
        if not (address.startswith("L") or address.startswith("M")) or len(address) < 26:
            return await interaction.response.send_message("❌ Dirección LTC inválida. Debe empezar con `L` o `M` y tener al menos 26 caracteres.", ephemeral=True)

        user_id = str(interaction.user.id)
        self.addresses[user_id] = address

        # Generar QR
        qr_bytes = self.generate_qr(address)
        file = discord.File(qr_bytes, filename="ltc_qr.png")

        embed = discord.Embed(
            title="✅ Dirección LTC Establecida",
            description=f"Tu dirección de pago LTC ha sido guardada.\n\n**Dirección:** `{address}`",
            color=discord.Color.green()
        )
        embed.set_image(url="attachment://ltc_qr.png")
        embed.set_footer(text="Usa /mybal para ver tu balance.")

        await interaction.response.send_message(embed=embed, file=file, ephemeral=True)

    @app_commands.command(name="mybal", description="Obtiene el balance LTC de tu dirección (usa /setltc primero).")
    async def mybal(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        address = self.addresses.get(user_id)
        if not address:
            return await interaction.response.send_message("❌ No has establecido tu dirección LTC. Usa `/setltc <dirección>` primero.", ephemeral=True)

        embed = discord.Embed(title="⏳ Cargando Balance LTC...", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        msg = await interaction.original_response()

        # Obtener precio real
        ltc_usd, ltc_eur = await self.get_ltc_price()

        # Obtener balance
        confirmed, unconfirmed, total_received = await self.get_ltc_balance(address)
        txs = await self.get_ltc_transactions(address)

        if confirmed is None:
            embed = discord.Embed(title="❌ Error", description="No se pudo obtener el balance. Verifica la dirección.", color=discord.Color.red())
            return await msg.edit(embed=embed)

        # Calcular valores
        usd_confirmed = confirmed * ltc_usd
        eur_confirmed = confirmed * ltc_eur
        usd_unconfirmed = unconfirmed * ltc_usd
        eur_unconfirmed = unconfirmed * ltc_eur
        usd_total = total_received * ltc_usd
        eur_total = total_received * ltc_eur

        embed = discord.Embed(
            title="💰 Balance LTC",
            color=discord.Color.from_rgb(52, 152, 219)
        )
        embed.add_field(name="Dirección", value=f"`{address}`", inline=False)
        embed.add_field(
            name="Balance Confirmado",
            value=f"{confirmed:,.8f} LTC\n${usd_confirmed:,.2f} USD\n€{eur_confirmed:,.2f} EUR",
            inline=True
        )
        embed.add_field(
            name="Balance Sin Confirmar",
            value=f"{unconfirmed:,.8f} LTC\n${usd_unconfirmed:,.2f} USD\n€{eur_unconfirmed:,.2f} EUR",
            inline=True
        )
        embed.add_field(
            name="Total Recibido",
            value=f"{total_received:,.8f} LTC\n${usd_total:,.2f} USD\n€{eur_total:,.2f} EUR",
            inline=False
        )

        # Transacciones
        if txs:
            tx_text = ""
            for tx in txs:
                time = f"<t:{int(tx['time'] / 1000)}:R>" if isinstance(tx['time'], str) and tx['time'].isdigit() else "Desconocido"
                tx_text += f"`{tx['hash'][:8]}...` {tx['value']:,.4f} LTC {time}\n"
            embed.add_field(name="Últimas 5 Transacciones", value=tx_text or "No hay detalles.", inline=False)
        else:
            embed.add_field(name="Últimas 5 Transacciones", value="No se encontraron transacciones.", inline=False)

        # Botones
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Ver en Explorer", url=f"https://blockchair.com/litecoin/address/{address}", emoji="🔍"))
        view.add_item(discord.ui.Button(label="Info de Transacción", url=f"https://blockchair.com/litecoin/address/{address}", emoji="ℹ️"))

        # QR
        qr_bytes = self.generate_qr(address)
        file = discord.File(qr_bytes, filename="ltc_qr.png")
        embed.set_image(url="attachment://ltc_qr.png")

        await msg.edit(embed=embed, view=view, attachments=[file])

async def setup(bot):
    await bot.add_cog(LTC(bot))
    print("Cog 'ltc' cargado correctamente")
