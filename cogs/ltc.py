import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import json
import os
import qrcode
import io


class LTC(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.file_path = "ltc_addresses.json"
        self.addresses = self.load_addresses()

        # Emojis personalizados del servidor
        self.emoji_flecha = "<:flecha:1433716388022718575>"
        self.emoji_ltc = "<:ltc:1433716731074969600>"

        # Emojis Unicode estándar
        self.emoji_point = "🔹"
        self.emoji_received = "🟢"
        self.emoji_sent = "🔴"

    # ==================================================================================
    # Cargar y guardar direcciones
    # ==================================================================================
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

    # ==================================================================================
    # API: Obtener precio LTC en USD/EUR
    # ==================================================================================
    async def get_ltc_price(self):
        try:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=usd,eur"
            async with self.session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["litecoin"]["usd"], data["litecoin"]["eur"]
        except:
            pass
        return 75.0, 69.0  # fallback

    # ==================================================================================
    # API: Balance de una wallet LTC
    # ==================================================================================
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

    # ==================================================================================
    # API: Últimas transacciones
    # ==================================================================================
    async def get_ltc_transactions(self, address):
        try:
            url = f"https://api.blockcypher.com/v1/ltc/main/addrs/{address}/full"
            async with self.session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    txs = data.get("txs", [])[:5]
                    formatted = []

                    for tx in txs:
                        value = sum(
                            o.get("value", 0) for o in tx.get("outputs", [])
                            if o.get("addresses") and address in o["addresses"]
                        ) / 1e8

                        status = self.emoji_received if value > 0 else self.emoji_sent

                        formatted.append({
                            "hash": tx["hash"],
                            "short": tx["hash"][:10] + "...",
                            "value": value,
                            "status": status,
                        })

                    return formatted
        except:
            pass
        return []

    # ==================================================================================
    # GENERAR QR
    # ==================================================================================
    def generate_qr(self, address):
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(address)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        bio = io.BytesIO()
        img.save(bio, "PNG")
        bio.seek(0)
        return bio

    # ==================================================================================
    # /setltc
    # ==================================================================================
    @app_commands.command(name="setltc", description="Guarda tu dirección LTC")
    async def setltc(self, interaction: discord.Interaction, address: str):
        address = address.strip()
        if not (address.startswith("L") or address.startswith("M")) or len(address) < 26:
            await interaction.response.send_message("Dirección inválida. Debe iniciar con L o M.")
            return

        self.addresses[str(interaction.user.id)] = address
        self.save_addresses()

        qr = self.generate_qr(address)
        file = discord.File(qr, "qr.png")

        embed = discord.Embed(
            title=f"{self.emoji_ltc} Dirección Guardada",
            description=f"`{address}`\nUsa `/mybal` para ver tu balance.",
            color=0x2ecc71
        )
        embed.set_image(url="attachment://qr.png")

        await interaction.response.send_message(embed=embed, file=file)

    # ==================================================================================
    # /mybal
    # ==================================================================================
    @app_commands.command(name="mybal", description="Muestra tu balance LTC con formato avanzado")
    async def mybal(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        address = self.addresses.get(user_id)

        if not address:
            await interaction.response.send_message("Primero usa `/setltc <dirección>`.")
            return

        await interaction.response.defer()

        usd, eur = await self.get_ltc_price()
        confirmed, unconfirmed, total = await self.get_ltc_balance(address)
        txs = await self.get_ltc_transactions(address)

        if confirmed is None:
            await interaction.followup.send("Error al obtener el balance.")
            return

        embed = discord.Embed(
            title=f"{self.emoji_ltc} Litecoin Balance {self.emoji_ltc}",
            color=0x3498db
        )

        # Dirección con flechita
        embed.add_field(
            name=f"{self.emoji_flecha} Address:",
            value=f"[`{address}`](https://blockchair.com/litecoin/address/{address})",
            inline=False
        )

        # Balances
        embed.add_field(
            name=f"{self.emoji_point} Confirmed Balance",
            value=f"**{confirmed:,.8f} LTC** | ${confirmed*usd:,.2f} USD\n€{confirmed*eur:,.2f} EUR",
            inline=True
        )
        embed.add_field(
            name=f"{self.emoji_point} Unconfirmed Balance",
            value=f"**{unconfirmed:,.8f} LTC** | ${unconfirmed*usd:,.2f} USD\n€{unconfirmed*eur:,.2f} EUR",
            inline=True
        )
        embed.add_field(
            name=f"{self.emoji_point} Total Received",
            value=f"**{total:,.8f} LTC** | ${total*usd:,.2f} USD\n€{total*eur:,.2f} EUR",
            inline=True
        )

        # Transacciones
        tx_block = ""
        for tx in txs:
            tx_block += (
                f"[`{tx['short']}`](https://blockchair.com/litecoin/transaction/{tx['hash']}) "
                f"• {tx['value']:.8f} LTC | ${tx['value']*usd:,.2f} USD "
                f"{tx['status']}\n"
            )

        embed.add_field(
            name="Last 5 Transactions",
            value=tx_block or "Sin transacciones",
            inline=False
        )

        # QR
        qr = self.generate_qr(address)
        file = discord.File(qr, "qr.png")
        embed.set_image(url="attachment://qr.png")

        # Botones
        view = discord.ui.View(timeout=None)

        view.add_item(discord.ui.Button(
            label="Get Transaction Info",
            url=f"https://blockchair.com/litecoin/address/{address}",
            emoji="🔍"
        ))

        view.add_item(discord.ui.Button(
            label="View on Explorer",
            url=f"https://live.blockcypher.com/ltc/address/{address}/",
            emoji="🔗"
        ))

        await interaction.followup.send(embed=embed, file=file, view=view)

    async def cog_unload(self):
        await self.session.close()


async def setup(bot):
    await bot.add_cog(LTC(bot))
