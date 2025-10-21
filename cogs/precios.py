import discord
from discord.ext import commands

# ============================================================
# 🧮 Precios Cog
# ============================================================
class Precios(commands.Cog):
    """A cog for calculating prices based on predefined formulas."""

    def __init__(self, bot):
        """Initialize the Precios cog with the bot instance and pricing data."""
        self.bot = bot

        # 🔥 Pricing formulas (base, multiplier, constant, formula string, display name)
        self.formulas = {
            "loscombinasionas": (15, 0.06, 2, "(M − 15) × 0.06 + 2", "Los combinasionas"),
            "esoksekolah": (30, 0.04, 2, "(M − 30) × 0.04 + 2", "Esok sekolah"),
            "losbros": (24, 0.05, 2.5, "(M − 24) × 0.05 + 2.5", "Los bros"),
            "lagrandecombinasion": (10, 0.07, 3, "(M − 10) × 0.07 + 3", "La grande combinasion"),
            "loshotspositos": (20, 0.05, 3.5, "(M − 20) × 0.05 + 3.5", "Los hotspositos"),
            "ketupatkepat": (35, 0.04, 10, "(M − 35) × 0.04 + 10", "Ketupat kepat"),
            "tralaledon": (27.5, 0.04, 11, "(M − 27.5) × 0.04 + 11", "Tralaledon"),
            "ketchuruandmusturu": (42.5, 0.08, 11.5, "(M − 42.5) × 0.08 + 11.5", "Ketchuru and musturu"),
            "nuclearodinossauro": (15, 0.10, 12, "(M − 15) × 0.10 + 12", "Nuclearo dinossauro"),
            "lasupremecombinasion": (40, 0.11, 15, "(M − 40) × 0.11 + 15", "La supreme combinasion"),
            "tacoritabicicleta": (16.5, 0.04, 2, "(M − 16.5) × 0.04 + 2", "Tacorita bicicleta"),
            "laextinctgrande": (23.5, 0.04, 3, "(M − 23.5) × 0.04 + 3", "La extinct grande"),
            "lassis": (17.5, 0.03, 3, "(M − 17.5) × 0.03 + 3", "Las sis"),
            "losprimos": (31, 0.03, 4, "(M − 31) × 0.03 + 4", "Los primos"),
            "lostacoritas": (32, 0.04, 3.5, "(M − 32) × 0.04 + 3.5", "Los tacoritas"),
            "celularciniviciosini": (22.5, 0.06, 5, "(M − 22.5) × 0.06 + 5", "Celularcini viciosini"),
            "spaghettitualetti": (60, 0.03, 7, "(M − 60) × 0.03 + 7", "Spaghetti tualetti"),
            "tictacsahur": (37.5, 0.06, 8, "(M − 37.5) × 0.06 + 8", "Tictac sahur"),
            "garamaandmadundung": (50, 0.08, 20, "(M − 50) × 0.08 + 20", "Garama and madundung"),
            "dragoncannelloni": (200, 0.30, 125, "(M − 200) × 0.30 + 125", "Dragon cannelloni"),
            "losmobilis": (22, 0.04, 1.5, "(M − 22) × 0.04 + 1.5", "Los mobilis"),
            "mariachicorazoni": (12.5, 0.05, 1.5, "(M − 12.5) × 0.05 + 1.5", "Mariachi corazoni"),
            "los67": (22.5, 0.03, 1.5, "(M − 22.5) × 0.03 + 1.5", "Los 67"),
            "chillinchili": (25, 0.04, 3, "(M − 25) × 0.04 + 3", "Chillin chili"),
            "tangtangkelentang": (33.5, 0.05, 5, "(M − 33.5) × 0.05 + 5", "Tang tang kelentang"),
            "eviledon": (31.5, 0.04, 6, "(M − 31.5) × 0.04 + 6", "Eviledon"),
            "moneymoneypuggy": (21, 0.06, 7, "(M − 21) × 0.06 + 7", "Money money puggy"),
            "lassecretcombinasion": (125, 0.06, 12, "(M − 125) × 0.06 + 12", "La secret combinasion"),
            "burguroandfryuro": (150, 0.12, 25, "(M − 150) × 0.12 + 25", "Burguro and fryuro"),
            "strawberryelephant": (350, 0.40, 300, "(M − 350) × 0.40 + 300", "Strawberry elephant"),
            "laspookygrande": (24.5, 0.03, 3, "(M − 24.5) × 0.03 + 3", "La spooky grande"),
            "spookyandpumpky": (80, 0.08, 24, "(M − 80) × 0.08 + 24", "Spooky and pumpky"),
        }

        # 📋 Aliases for pricing items
        self.aliases = {
            "lc": "loscombinasionas",
            "combinasionas": "loscombinasionas",
            "es": "esoksekolah",
            "sekolah": "esoksekolah",
            "lb": "losbros",
            "bros": "losbros",
            "lgc": "lagrandecombinasion",
            "grande": "lagrandecombinasion",
            "lhp": "loshotspositos",
            "hots": "loshotspositos",
            "kk": "ketupatkepat",
            "ketupat": "ketupatkepat",
            "tr": "tralaledon",
            "tralale": "tralaledon",
            "km": "ketchuruandmusturu",
            "musturu": "ketchuruandmusturu",
            "nd": "nuclearodinossauro",
            "nuclear": "nuclearodinossauro",
            "lsc": "lasupremecombinasion",
            "supreme": "lasupremecombinasion",
            "tb": "tacoritabicicleta",
            "taco": "tacoritabicicleta",
            "leg": "laextinctgrande",
            "extinct": "laextinctgrande",
            "ls": "lassis",
            "sis": "lassis",
            "lp": "losprimos",
            "primos": "losprimos",
            "lt": "lostacoritas",
            "tacoritas": "lostacoritas",
            "ccv": "celularciniviciosini",
            "celular": "celularciniviciosini",
            "st": "spaghettitualetti",
            "spaghetti": "spaghettitualetti",
            "ts": "tictacsahur",
            "tictac": "tictacsahur",
            "gm": "garamaandmadundung",
            "garama": "garamaandmadundung",
            "dc": "dragoncannelloni",
            "dragon": "dragoncannelloni",
            "mc": "mariachicorazoni",
            "mariachi": "mariachicorazoni",
            "l67": "los67",
            "cc": "chillinchili",
            "chili": "chillinchili",
            "ttk": "tangtangkelentang",
            "kelentang": "tangtangkelentang",
            "ev": "eviledon",
            "mmp": "moneymoneypuggy",
            "puggy": "moneymoneypuggy",
            "lsc2": "lassecretcombinasion",
            "secret": "lassecretcombinasion",
            "bf": "burguroandfryuro",
            "se": "strawberryelephant",
            "strawberry": "strawberryelephant",
            "elephant": "strawberryelephant",
            "spooky": "laspookygrande",
            "pumpky": "spookyandpumpky",
        }

    def make_embed(self, ctx, nombre: str, formula: str, operacion: str, resultado: float, pretty: str):
        """Create an embed for displaying price calculation results."""
        embed = discord.Embed(
            title=f"🧮 Calculadora de Precios - {pretty}",
            description=f"Conversión automática usando la fórmula de **{pretty}**",
            color=discord.Color.blurple()
        )
        embed.add_field(name="📌 Formula", value=formula, inline=False)
        embed.add_field(name="📊 Operación", value=operacion, inline=False)
        embed.add_field(name="💰 Resultado", value=f"**${resultado:.2f}**", inline=False)
        embed.set_footer(text=f"Pedido por {ctx.author}", icon_url=ctx.author.display_avatar.url)
        return embed

    def error_embed(self, ctx, msg: str):
        """Create an embed for displaying error messages."""
        return discord.Embed(
            title="⚠️ Error en el comando",
            description=msg,
            color=discord.Color.red()
        ).set_footer(text=f"Pedido por {ctx.author}", icon_url=ctx.author.display_avatar.url)

    @commands.command(name="precio", aliases=["price", "cost", "valor"])
    async def precio(self, ctx, nombre: str = None, m: float = None):
        """Calcula el precio de cada objeto en sab en millones a dolares."""
        if not nombre:
            return await ctx.send(embed=self.error_embed(
                ctx, f"Debes especificar el nombre. Ejemplo: `{ctx.prefix}{ctx.command} lagrandecombinasion 100`"
            ))

        nombre = nombre.lower()
        if nombre in self.aliases:
            nombre = self.aliases[nombre]

        if nombre not in self.formulas:
            lista = ", ".join(self.formulas.keys())
            return await ctx.send(embed=self.error_embed(ctx, f"❌ No encontré la fórmula **{nombre}**. Opciones: {lista}"))

        if m is None:
            return await ctx.send(embed=self.error_embed(
                ctx, f"Debes especificar la cantidad de millones. Ejemplo: `{ctx.prefix}{ctx.command} {nombre} 100`"
            ))

        base, mult, suma, formula, pretty = self.formulas[nombre]
        result = (m - base) * mult + suma
        operacion = f"( {m} - {base} ) × {mult} + {suma}"

        await ctx.send(embed=self.make_embed(ctx, nombre, formula, operacion, result, pretty))

    @commands.command(name="helpprices")
    async def helpprices(self, ctx):
        """Despliega una lista completa de todos los precios."""
        formulas_items = list(self.formulas.items())
        embeds = []
        prefixes = ["precio", "valor", "cost", "price"]

        # Compactar: 10 productos por página
        pages = [formulas_items[i:i+10] for i in range(0, len(formulas_items), 10)]

        for i, page in enumerate(pages, start=1):
            embed = discord.Embed(
                title="📖 Ayuda de precios",
                description="Lista de fórmulas y alias.\nUsa cualquiera de estos comandos: "
                            "`$precio`, `$valor`, `$cost`, `$price`.",
                color=discord.Color.blurple()
            )
            for key, (_, _, _, _, pretty) in page:
                aliases = [alias for alias, real in self.aliases.items() if real == key]
                ejemplos = " | ".join([f"${p} {aliases[0]} 100" for p in prefixes]) if aliases else f"{key} 100"
                embed.add_field(
                    name=f"🔹 {pretty}",
                    value=f"Alias: `{', '.join([key] + aliases)}`\nEjemplos: {ejemplos}",
                    inline=False
                )
            embed.set_footer(text=f"Página {i}/{len(pages)}")
            embeds.append(embed)

        message = await ctx.send(embed=embeds[0])

        if len(embeds) > 1:
            await message.add_reaction("⬅️")
            await message.add_reaction("➡️")

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️"] and reaction.message.id == message.id

            current_page = 0
            while True:
                try:
                    reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
                except asyncio.TimeoutError:
                    break

                if str(reaction.emoji) == "➡️" and current_page < len(embeds)-1:
                    current_page += 1
                    await message.edit(embed=embeds[current_page])
                elif str(reaction.emoji) == "⬅️" and current_page > 0:
                    current_page -= 1
                    await message.edit(embed=embeds[current_page])

                await message.remove_reaction(reaction, user)

async def setup(bot):
    """Set up the Precios cog for the bot."""
    await bot.add_cog(Precios(bot))
