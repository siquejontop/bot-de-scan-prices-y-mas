import discord
from discord.ext import commands
import pytesseract
from PIL import Image
import re
import aiohttp
import os

# 🔧 Render o Linux usa esta ruta:
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
# 🪟 En Windows, podrías usar esta si pruebas localmente:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

class Scan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def scan(self, ctx):
        """
        Escanea una imagen enviada y detecta nombres y valores (por ejemplo 30M/s)
        """
        if not ctx.message.attachments:
            await ctx.send("📸 Por favor envía una imagen junto con el comando, ejemplo: `,scan` + imagen.")
            return

        image_url = ctx.message.attachments[0].url
        await ctx.send("🧠 Analizando la imagen, por favor espera...")

        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                if resp.status != 200:
                    await ctx.send("❌ No se pudo descargar la imagen.")
                    return
                data = await resp.read()

        with open("temp_scan.png", "wb") as f:
            f.write(data)

        # Leer texto con OCR
        img = Image.open("temp_scan.png")
        text = pytesseract.image_to_string(img)

        # Buscar nombres (letras y espacios)
        names = re.findall(r"[A-Z][A-Za-z\s]+", text)

        # Buscar producciones tipo 30M/s, 108.8M/s, 367.5M/s, etc.
        rates = re.findall(r"\d+\.?\d*\s*[MBT]?/s", text)

        os.remove("temp_scan.png")

        if not rates:
            await ctx.send("⚠️ No se detectaron valores de producción por segundo (`M/s`, `B/s`, etc.) en la imagen.")
            return

        # Emparejar nombres y valores según el orden en el texto
        result_lines = []
        for i in range(min(len(names), len(rates))):
            result_lines.append(f"**{names[i]}** → `{rates[i]}`")

        embed = discord.Embed(
            title="📊 Resultados del Escaneo",
            description="\n".join(result_lines),
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Solicitado por {ctx.author}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Scan(bot))
