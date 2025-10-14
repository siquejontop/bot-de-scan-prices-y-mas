import discord
from discord.ext import commands
import pytesseract
from PIL import Image
import re
import aiohttp
import os
import cv2
import numpy as np

# Ajusta si tu entorno usa otra ruta
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# Confianza mínima (0-100) para aceptar una caja de tesseract
MIN_CONF = 30

class Scan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def preprocess(self, pil_img):
        """Devuelve una imagen (BGR) preprocesada y una versión para debug."""
        # Convertir PIL->OpenCV BGR
        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        h, w = img.shape[:2]

        # Redimensionar si es muy grande (aumenta estabilidad del OCR)
        max_dim = 1280
        if max(h, w) > max_dim:
            scale = max_dim / max(h, w)
            img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

        # Convertir a HSV para aislar colores brillantes (amarillo/verde/blanco)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # Rango para blanco/amarillo/verdes usados en tu juego (ajusta si hace falta)
        masks = []
        # Blanco/claros
        masks.append(cv2.inRange(hsv, (0, 0, 180), (180, 60, 255)))
        # Amarillo (ej. $ en amarillo)
        masks.append(cv2.inRange(hsv, (15, 80, 120), (40, 255, 255)))
        # Verde (montos o texto verde)
        masks.append(cv2.inRange(hsv, (40, 50, 60), (90, 255, 255)))
        # Naranja rojizo (por si aparece)
        masks.append(cv2.inRange(hsv, (5, 50, 50), (20, 255, 255)))

        mask = masks[0]
        for m in masks[1:]:
            mask = cv2.bitwise_or(mask, m)

        # Refuerza texto: cierre/morphology to fill gaps
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
        mask = cv2.medianBlur(mask, 3)

        # Obtener imagen final en grayscale para tesseract
        gray = cv2.bitwise_and(img, img, mask=mask)
        gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)
        # Binarizar
        _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Ligero aumento de nitidez (opcional)
        th = cv2.medianBlur(th, 3)

        return th, img  # th: imagen para OCR, img: original redimensionado (para debug)

    def run_ocr_boxes(self, ocr_img):
        """Ejecuta pytesseract.image_to_data y devuelve lista de dicts con texto, conf y cajas."""
        custom_oem_psm = "--oem 3 --psm 6"
        # No usar whitelist demasiado restrictiva o se cortan cosas; lo filtramos por regex luego
        data = pytesseract.image_to_data(ocr_img, output_type=pytesseract.Output.DICT, config=custom_oem_psm)
        boxes = []
        n = len(data['text'])
        for i in range(n):
            txt = data['text'][i].strip()
            if txt == "":
                continue
            try:
                conf = int(data['conf'][i])
            except:
                # a veces conf viene como '-1' o string
                try:
                    conf = float(data['conf'][i])
                    conf = int(conf)
                except:
                    conf = 0
            if conf < MIN_CONF:
                continue
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
            boxes.append({"text": txt, "conf": conf, "x": x, "y": y, "w": w, "h": h})
        return boxes

    def find_amounts_and_rates(self, boxes):
        """Detecta montos $x, unidades por segundo y Collect/Recoger y los empareja."""
        text_all = " ".join(b["text"] for b in boxes)
        # regex para montos: $70.1B o 70.1B o $7.7B etc.
        amount_re = re.compile(r"\$?\d{1,3}(?:\.\d+)?\s*[KMBT]?B?\b", re.IGNORECASE)
        # productions tipo 132M/s, 24.5M/s, 60M/s
        rate_re = re.compile(r"\d{1,4}(?:\.\d+)?\s*[KMGT]?/s|\d{1,4}(?:\.\d+)?\s*[MBKT]?/s", re.IGNORECASE)

        amounts = []
        rates = []
        collects = []

        for b in boxes:
            t = b["text"]
            # normalizar comas -> puntos
            t_norm = t.replace(",", ".")
            # detect amounts inside each small text token (p.e. "$70.1B" as una caja)
            if amount_re.search(t_norm):
                match = amount_re.search(t_norm).group(0)
                amounts.append({"text": match, "box": b})
            if rate_re.search(t_norm):
                match = rate_re.search(t_norm).group(0)
                rates.append({"text": match, "box": b})
            # Detectar Collect / Recoger / Recoge
            if t_norm.lower() in ("collect", "recoger", "recoge", "collecto"):
                collects.append({"text": t_norm, "box": b})

        # Emparejar collects -> monto más cercano por Y (vertical)
        collect_results = []
        for c in collects:
            cy = c["box"]["y"] + c["box"]["h"] / 2
            # buscar amount cuyo centro Y esté cercano (normalmente amounts están encima o debajo)
            best = None
            best_d = 1e9
            for a in amounts:
                ay = a["box"]["y"] + a["box"]["h"] / 2
                d = abs(ay - cy)
                if d < best_d:
                    best_d = d
                    best = a
            if best:
                collect_results.append({"collect_box": c["box"], "amount": best["text"]})

        # También devolver rates y free amounts (sin collect)
        free_amounts = [a["text"] for a in amounts]
        free_rates = [r["text"] for r in rates]

        return collect_results, free_amounts, free_rates

    @commands.command()
    async def scan(self, ctx):
        """Escanea una imagen enviada y detecta nombres, 'Collect' y montos/rates."""
        if not ctx.message.attachments:
            await ctx.send("📸 Por favor envía una imagen junto con el comando, ejemplo: `,scan` + imagen.")
            return

        image_url = ctx.message.attachments[0].url
        await ctx.send("🧠 Analizando la imagen, por favor espera...")

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

        # Abrir imagen y preprocesar
        pil = Image.open(temp_path).convert("RGB")
        ocr_img, debug_img = self.preprocess(pil)

        # OCR: cajas con confidencias
        boxes = self.run_ocr_boxes(ocr_img)

        # DEBUG: imprime lo que encontró
        print("=== OCR BOXES ===")
        for b in boxes:
            print(f'text="{b["text"]}" conf={b["conf"]} box=({b["x"]},{b["y"]},{b["w"]},{b["h"]})')
        print("=== END BOXES ===")

        collect_results, free_amounts, free_rates = self.find_amounts_and_rates(boxes)

        # Borrar temp
        try:
            os.remove(temp_path)
        except:
            pass

        # Si no encontró ni montos ni rates
        if not collect_results and not free_amounts and not free_rates:
            # guarda imagen procesada para debug (opcional)
            dbg_path = "ocr_debug.png"
            cv2.imwrite(dbg_path, debug_img)
            await ctx.send("⚠️ No se detectaron valores ($/s, M/s, etc.) en la imagen.\nHe subido una imagen de debug al servidor (si la quieres revisa logs).")
            print(f"[DEBUG] Imagen original guardada en: {dbg_path}")
            return

        # Construir mensaje
        lines = []
        if collect_results:
            for item in collect_results:
                lines.append(f"Collect detectado → **{item['amount']}**")
        if free_amounts:
            lines.append("Montos detectados: " + ", ".join(f"`{a}`" for a in sorted(set(free_amounts))))
        if free_rates:
            lines.append("Producciones detectadas: " + ", ".join(f"`{r}`" for r in sorted(set(free_rates))))

        desc = "\n".join(lines) if lines else "Se detectaron fragmentos de texto (revisa logs)."

        embed = discord.Embed(title="📊 Resultados del Escaneo", description=desc, color=discord.Color.green())
        embed.set_footer(text=f"Solicitado por {ctx.author}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Scan(bot))
