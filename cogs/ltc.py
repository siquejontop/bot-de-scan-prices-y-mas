import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import json
import os
from PIL import Image, ImageDraw, ImageFont, ImageOps
import io
import qrcode
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
        qr = qrcode.QRCode(version=1, box_size=6, border=3)
        qr.add_data(address)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        return img.convert("RGBA")

    async def generate_balance_image(self, address: str, confirmed: float, unconfirmed: float, total_received: float,
                                   usd_price: float, eur_price: float, txs):
        # === CARGAR FUENTES ===
        try:
            font_bold = ImageFont.truetype("fonts/Inter-Bold.ttf", 20)
            font_regular = ImageFont.truetype("fonts/Inter-Regular.ttf", 18)
            font_small = ImageFont.truetype("fonts/Inter-Regular.ttf", 16)
            font_mono = ImageFont.truetype("fonts/JetBrainsMono-Regular.ttf", 16)
        except:
            font_bold = ImageFont.load_default()
            font_regular = font_bold
            font_small = font_bold
            font_mono = font_bold

        # === DIMENSIONES ===
        width, height = 800, 600
        img = Image.new("RGBA", (width, height), (30, 33, 39))
        draw = ImageDraw.Draw(img)

        # === LOGO LITE //
        try:
            logo = Image.open("assets/ltc_logo.png").convert("RGBA")
            logo = logo.resize((40, 40), Image.Resampling.LANCZOS)
            img.paste(logo, (30, 25), logo)
        except:
            pass  # sin logo

        # === TÍTULO ===
        draw.text((85, 30), "Litecoin Balance", fill=(255, 255, 255), font=font_bold)
        draw.text((85, 58), f"Address: {address}", fill=(150, 170, 200), font=font_small)

        # === BALANCES ===
        def draw_balance_box(x, y, title, ltc, usd, eur):
            draw.rounded_rectangle([x, y, x+240, y+110], radius=12, fill=(40, 44, 52))
            draw.text((x+12, y+15), "◆", fill=(52, 152, 219), font=font_bold)
            draw.text((x+35, y+15), title, fill=(220, 220, 220), font=font_regular)
            draw.text((x+12, y+50), f"{ltc:,.8f} LTC", fill=(255, 255, 255), font=font_mono)
            draw.text((x+12, y+75), f"${usd:,.2f} USD", fill=(100, 200, 100), font=font_small)
            draw.text((x+12, y+95), f"€{eur:,.2f} EUR", fill=(100, 180, 255), font=font_small)

        usd_c, eur_c = confirmed * usd_price, confirmed * eur_price
        usd_u, eur_u = unconfirmed * usd_price, unconfirmed * eur_price
        usd_t, eur_t = total_received * usd_price, total_received * eur_price
        draw_balance_box(50, 130, "Confirmed Balance", confirmed, usd_c, eur_c)
        draw_balance_box(310, 130, "Unconfirmed Balance", unconfirmed, usd_u, eur_u)
        draw_balance_box(570, 130, "Total Received", total_received, usd_t, eur_t)

        # === TRANSACCIONES ===
        draw.rounded_rectangle([50, 260, 750, 460], radius=12, fill=(40, 44, 52))
        draw.text((65, 270), "Last 5 Transactions", fill=(220, 220, 220), font=font_regular)
        y = 310
        for tx in txs[:5]:
            hash_part = tx["hash"]
            value = tx["value"]
            usd_val = value * usd_price
            draw.text((65, y), f"{hash_part}", fill=(180, 180, 180), font=font_mono)
            draw.text((300, y), f"{value:,.8f} LTC", fill=(255, 255, 255), font=font_mono)
            draw.text((500, y), f"${usd_val:,.2f} USD", fill=(100, 200, 100), font=font_small)
            draw.ellipse([650, y+5, 670, y+25], fill=(0, 200, 0))
            draw.text((680, y), "Received", fill=(180, 255, 180), font=font_small)
            y += 35
        if not txs:
            draw.text((65, 310), "No recent transactions.", fill=(150, 150, 150), font=font_small)

        # === QR CODE ===
        qr_img = self.generate_qr(address)
        qr_img = qr_img.resize((120, 120), Image.Resampling.LANCZOS)
        img.paste(qr_img, (650, 470))

        # === BOTONES ===
        draw.rounded_rectangle([50, 520, 250, 570], radius=12, fill=(88, 101, 242))
        draw.text((80, 538), "Get Transaction Info", fill=(255, 255, 255), font=font_regular)
        draw.rounded_rectangle([280, 520, 520, 570], radius=12, fill=(52, 58, 64), outline=(100, 100, 100), width=2)
        draw.text((310, 538), "View on Explorer", fill=(200, 200, 200), font=font_regular)

        # === GUARDAR ===
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
            return await interaction.response.send_message(
                "Dirección LTC inválida. Debe empezar con `L` o `M`."
            )  # ← Público

        await interaction.response.defer()  # ← Público

        user_id = str(interaction.user.id)
        self.addresses[user_id] = address
        self.save_addresses()

        qr_img = self.generate_qr(address)
        qr_bio = io.BytesIO()
        qr_img.save(qr_bio, "PNG")
        qr_bio.seek(0)
        file = discord.File(qr_bio, "ltc_qr.png")

        embed = discord.Embed(title="Dirección LTC Guardada", color=discord.Color.green())
        embed.description = f"**Dirección:** `{address}`\nUsa `/mybal` para ver tu balance."
        embed.set_image(url="attachment://ltc_qr.png")
        embed.set_footer(text=f"Guardado por {interaction.user.display_name}")

        await interaction.followup.send(embed=embed, file=file)  # ← Público

    # =====================================================
    # /mybal
    # =====================================================
    @app_commands.command(name="mybal", description="Muestra tu balance LTC (usa /setltc primero).")
    async def mybal(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        address = self.addresses.get(user_id)
        if not address:
            return await interaction.response.send_message(
                "No has establecido tu dirección. Usa `/setltc <dirección>` primero."
            )  # ← Público

        await interaction.response.defer()  # ← Público

        loading = discord.Embed(title="Cargando balance LTC...", color=discord.Color.blue())
        await interaction.followup.send(embed=loading)  # ← Público

        # === DATOS ===
        usd, eur = await self.get_ltc_price()
        confirmed, unconfirmed, total_received = await self.get_ltc_balance(address)
        txs = await self.get_ltc_transactions(address)

        if confirmed is None:
            error = discord.Embed(title="Error", description="No se pudo obtener el balance.", color=discord.Color.red())
            return await interaction.followup.send(embed=error)  # ← Público

        # === GENERAR IMAGEN ===
        img_bio = await self.bot.loop.run_in_executor(
            None, self.generate_balance_image, address, confirmed, unconfirmed, total_received, usd, eur, txs
        )
        file = discord.File(img_bio, filename="ltc_balance.png")

        # === ENVIAR ===
        embed = discord.Embed(title="Balance LTC", color=discord.Color.from_rgb(52, 152, 219))
        embed.set_image(url="attachment://ltc_balance.png")
        embed.set_footer(text=f"Balance de {interaction.user.display_name}")

        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(
            label="Get Transaction Info", url=f"https://blockchair.com/litecoin/address/{address}", emoji="Info"
        ))
        view.add_item(discord.ui.Button(
            label="View on Explorer", url=f"https://blockchair.com/litecoin/address/{address}", emoji="Search"
        ))

        await interaction.followup.send(embed=embed, file=file, view=view)  # ← Público


# =====================================================
# SETUP
# =====================================================
async def setup(bot):
    await bot.add_cog(LTC(bot))
    print("Cog 'ltc' cargado correctamente (MODO PÚBLICO)")
