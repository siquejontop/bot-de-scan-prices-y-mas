import discord
from discord.ext import commands
import pytesseract
from PIL import Image
import re
import aiohttp
import os
import cv2
import numpy as np

# 🔧 Render o Linux
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
# 🪟 En Windows (para pruebas locales):
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

class Scan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def extract_text_from_image(self, img):
        """Mejor OCR con preprocesamiento para texto brillante o pixelado."""
        cv_img = np.array(img)

        # Convertir a HSV para aislar colores de texto brillante (amarillo, blanco)
        hsv = cv2.cvtColor(cv_img, cv2.COLOR_RGB2HSV)
        mask = cv2.inRange(hsv, (0, 0, 200), (180, 80, 255))  # Rango de colores brillantes
        result = cv2.bitwise_and(cv_img, cv_img, mask=mask)

        # Convertir a escala de grises y limpiar
        gray = cv2.cvtColor(result, cv2.COLOR_RGB2GRAY)
        gray = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)[1]
        gray = cv2.medianBlur(gray, 3)

        # OCR optimizado
        text = pytesseract.image_to_string(
            gray, config="--psm 6 -c tessedit_char_whitelist=$0123456789MBQs./sABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        )

        # Limpieza de texto
        text = text.replace("\n", " ").replace(",", ".").strip()
        text = re.sub(r"\s+", " ", text)
        return text

    @commands.command()
    async def scan(self, ctx):
        """Escanea una imagen enviada y detecta nombres y valores de producción."""
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

        temp_path = "temp_scan.png"
        with open(temp_path, "wb") as f:
            f.write(data)

        # Abrir imagen y extraer texto con preprocesamiento
        img = Image.open(temp_path)
        text = self.extract_text_from_image(img)
        os.remove(temp_path)

        print("🧠 Texto detectado:", text)  # útil para debug

        # Buscar nombres y valores
        names = re.findall(r"[A-Z][A-Za-z\s]+", text)
        rates = re.findall(r"\$?\d+\.?\d*\s*[MBT]?/s", text)

        if not rates:
            await ctx.send("⚠️ No se detectaron valores de producción por segundo (`M/s`, `B/s`, etc.) en la imagen.")
            return

        result_lines = []
        for i in range(min(len(names), len(rates))):
            result_lines.append(f"**{names[i]}** → `{rates[i]}`")

        embed = discord.Embed(
            title="📊 Resultados del Escaneo",
            description="\n".join(result_lines) if result_lines else f"`{text}`",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Solicitado por {ctx.author}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Scan(bot))
