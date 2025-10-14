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
                img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
            
            # Convertir a HSV y crear máscaras optimizadas para texto brillante y colorido
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            masks = [
                cv2.inRange(hsv, (20, 50, 200), (40, 255, 255)),  # Amarillo/dorado (precios)
                cv2.inRange(hsv, (0, 0, 200), (180, 50, 255)),   # Blanco/texto claro
                cv2.inRange(hsv, (100, 50, 100), (140, 255, 255)) # Cian/azul (otros textos)
            ]
            
            mask = masks[0]
            for m in masks[1:]:
                mask = cv2.bitwise_or(mask, m)
            
            # Operaciones morfológicas para texto pequeño y estilizado
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            mask = cv2.erode(mask, kernel, iterations=1)  # Reducir ruido
            mask = cv2.dilate(mask, kernel, iterations=2)  # Expandir texto
            mask = cv2.medianBlur(mask, 3)
            
            # Aplicar máscara y convertir a escala de grises
            result = cv2.bitwise_and(img, img, mask=mask)
            gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
            
            # Umbral adaptativo optimizado
            thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 3
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
                
            # Configuración optimizada para texto monetario con énfasis en M/s
            config = "--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz$./MKBTS "
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
                logger.debug(f"OCR detected: '{txt}' at ({x}, {y}) with conf {conf}")  # Debug log
            return boxes
        except Exception as e:
            logger.error(f"❌ Error en OCR: {e}")
            return []

    def find_texts(self, boxes):
        """Detecta nombres, montos y rates, asociando precios a nombres"""
        name_re = re.compile(r"^[A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)*$")
        amount_re = re.compile(r"\$?\d{1,3}(?:[.,]\d{1,3})?\s*[MKBTS]?", re.IGNORECASE)
        rate_re = re.compile(r"\d{1,4}(?:[.,]\d+)?\s*[MKBTS]?/s", re.IGNORECASE)
        
        names, amounts, rates = [], [], []
        name_to_amount = {}  # Diccionario para asociar nombres con montos cercanos
        
        # Ordenar boxes por y y luego x para mejor alineación
        sorted_boxes = sorted(boxes, key=lambda b: (b["y"], b["x"]))
        i = 0
        while i < len(sorted_boxes):
            box = sorted_boxes[i]
            t = box["text"].replace(",", ".")
            if name_re.match(t):
                names.append(t)
                # Buscar monto o rate cercano (hasta 6 cajas siguientes)
                for j in range(i + 1, min(i + 7, len(sorted_boxes))):
                    next_text = sorted_boxes[j]["text"].replace(",", ".")
                    amount_match = amount_re.search(next_text)
                    rate_match = rate_re.search(next_text)
                    if amount_match:
                        name_to_amount[t] = amount_match.group(0)
                        i = j + 1  # Saltar al siguiente nombre
                        break
                    elif rate_match:
                        name_to_amount[t] = rate_match.group(0)
                        i = j + 1  # Saltar al siguiente nombre
                        break
            elif amount_re.search(t) and t not in names:
                amounts.append(amount_re.search(t).group(0))
            elif rate_re.search(t) and t not in names:
                rates.append(rate_re.search(t).group(0))
            i += 1
        
        return names, list(set(amounts)), list(set(rates)), name_to_amount

    @commands.command()
    async def scan(self, ctx):
        """Escanea imagen y detecta nombres, montos y rates, destacando precio de Brainrot"""
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
                names, amounts, rates, name_to_amount = self.find_texts(boxes)

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

                # Buscar precio de Brainrot (ajusta el nombre según el item)
                brainrot_price = None
                target_name = "Dragon Cannelloni"  # Ajusta si "Brainrot" es otro item
                if target_name in name_to_amount:
                    brainrot_price = name_to_amount[target_name]
                elif names:  # Fallback al primer nombre con precio
                    for name in names:
                        if name in name_to_amount:
                            brainrot_price = name_to_amount[name]
                            break

                # Crear resultado
                result_lines = []
                if brainrot_price:
                    result_lines.append(f"**Precio de Brainrot ({target_name if target_name in name_to_amount else names[0]}): {brainrot_price}**")
                for i in range(min(len(names), len(rates))):
                    if names[i] != target_name:  # Evitar duplicar Brainrot
                        result_lines.append(f"**{names[i]}** → {rates[i]}")
                if amounts and not brainrot_price:
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
