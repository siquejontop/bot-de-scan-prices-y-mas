import discord
from discord.ext import commands
import pytesseract
from PIL import Image
import re
import aiohttp
import os
import cv2
import numpy as np
import logging

# Configuración de logging
logger = logging.getLogger("discord_bot")

# Ajusta según tu entorno
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
MIN_CONF = 30  # Confianza mínima OCR

class Scan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def preprocess(self, pil_img):
        """Preprocesa la imagen para mejorar la calidad del OCR"""
        try:
            img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            h, w = img.shape[:2]
            max_dim = 1280
            
            # Redimensionar manteniendo relación de aspecto
            if max(h, w) > max_dim:
                scale = max_dim / max(h, w)
                img = cv2.resize(img, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_AREA)
            
            # Convertir a HSV y crear máscaras para colores específicos
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            masks = [
                cv2.inRange(hsv, (0, 0, 180), (180, 60, 255)),  # blanco
                cv2.inRange(hsv, (15, 80, 120), (40, 255, 255)), # amarillo
                cv2.inRange(hsv, (40, 50, 60), (90, 255, 255)),  # verde
                cv2.inRange(hsv, (5, 50, 50), (20, 255, 255))   # naranja
            ]
            
            mask = masks[0]
            for m in masks[1:]:
                mask = cv2.bitwise_or(mask, m)
            
            # Operaciones morfológicas para limpiar la máscara
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
            mask = cv2.medianBlur(mask, 3)
            
            # Aplicar máscara y convertir a escala de grises
            result = cv2.bitwise_and(img, img, mask=mask)
            gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
            
            # Umbral adaptativo
            thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            thresh = cv2.medianBlur(thresh, 3)
            
            return thresh, img
        except Exception as e:
            logger.error(f"❌ Error en preprocesamiento de imagen: {e}")
            return None, None

    def run_ocr_boxes(self, ocr_img):
        """Ejecuta OCR y devuelve cajas con confianza mínima"""
        try:
            if ocr_img is None:
                return []
                
            config = "--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,$/ "
            data = pytesseract.image_to_data(ocr_img, output_type=pytesseract.Output.DICT, config=config)
            
            boxes = []
            for i in range(len(data["text"])):
                txt = data["text"][i].strip()
                if not txt:
                    continue
                try:
                    conf = float(data["conf"][i])
                except:
                    conf = 0
                if conf < MIN_CONF:
                    continue
                x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
                boxes.append({"text": txt, "conf": conf, "x": x, "y": y, "w": w, "h": h})
            return boxes
        except Exception as e:
            logger.error(f"❌ Error en OCR: {e}")
            return []

    def find_texts(self, boxes):
        """Detecta nombres, montos y rates"""
        name_re = re.compile(r"^[A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)*$")
        amount_re = re.compile(r"\$?\d{1,3}(?:[.,]\d{1,3})*\s*[KMBT]?B?", re.IGNORECASE)
        rate_re = re.compile(r"\d{1,4}(?:[.,]\d+)?\s*[KMGT]?/s", re.IGNORECASE)
        
        names, amounts, rates = [], [], []
        for b in boxes:
            t = b["text"].replace(",", ".")
            if name_re.match(t):
                names.append(t)
            amount_match = amount_re.search(t)
            if amount_match:
                amounts.append(amount_match.group(0))
            rate_match = rate_re.search(t)
            if rate_match:
                rates.append(rate_match.group(0))
        
        return names, list(set(amounts)), list(set(rates))

    @commands.command()
    async def scan(self, ctx):
        """Escanea imagen y detecta nombres, montos y rates"""
        if not ctx.message.attachments:
            await ctx.send("📸 Por favor envía una imagen junto con el comando.")
            return

        image_url = ctx.message.attachments[0].url
        await ctx.send("🧠 Analizando la imagen, por favor espera...")

        try:
            # Descargar imagen
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as resp:
                    if resp.status != 200:
                        await ctx.send("❌ No se pudo descargar la imagen.")
                        return
                    data = await resp.read()

            temp_path = "temp_scan.png"
            with open(temp_path, "wb") as f:
                f.write(data)

            try:
                pil = Image.open(temp_path).convert("RGB")
                ocr_img, debug_img = self.preprocess(pil)
                
                if ocr_img is None:
                    await ctx.send("❌ Error procesando la imagen.")
                    return

                boxes = self.run_ocr_boxes(ocr_img)
                names, amounts, rates = self.find_texts(boxes)

                # Limpiar archivo temporal
                try:
                    os.remove(temp_path)
                except:
                    pass

                if not any([names, amounts, rates]):
                    if debug_img is not None:
                        dbg_path = "ocr_debug.png"
                        cv2.imwrite(dbg_path, debug_img)
                        await ctx.send("⚠️ No se detectaron valores en la imagen. Imagen debug guardada.")
                    else:
                        await ctx.send("⚠️ No se detectaron valores en la imagen.")
                    return

                # Crear resultado
                result_lines = []
                for i in range(min(len(names), len(rates))):
                    result_lines.append(f"**{names[i]}** → {rates[i]}")
                if amounts:
                    result_lines.append("Montos detectados: " + ", ".join(f"{a}" for a in sorted(amounts)))

                embed = discord.Embed(
                    title="📊 Resultados del Escaneo",
                    description="\n".join(result_lines) if result_lines else "Se detectaron fragmentos de texto.",
                    color=discord.Color.green()
                )
                embed.set_footer(text=f"Solicitado por {ctx.author}", icon_url=ctx.author.display_avatar.url)
                await ctx.send(embed=embed)

            except Exception as e:
                logger.error(f"❌ Error procesando imagen: {e}")
                await ctx.send("❌ Error procesando la imagen.")
                try:
                    os.remove(temp_path)
                except:
                    pass

        except Exception as e:
            logger.error(f"❌ Error descargando imagen: {e}")
            await ctx.send("❌ Error descargando la imagen.")

async def setup(bot):
    await bot.add_cog(Scan(bot))
