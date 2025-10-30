import discord
from discord.ext import commands
import asyncio

class Precios(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.formulas = {
            # === LISTA 1 ===
            "esoksekolah": (30, 0.01, 1, "(M − 30) × 0.01 + 1", "Esok sekolah"),
            "loscombinasionas": (15, 0.01, 1.5, "(M − 15) × 0.01 + 1.5", "Los combinasionas"),
            "lagrandecombinasion": (10, 0.02, 1.5, "(M − 10) × 0.02 + 1.5", "La grande combinasion"),
            "loshotspositos": (20, 0.03, 2.5, "(M − 20) × 0.03 + 2.5", "Los hotspositos"),
            "losbros": (24, 0.02, 3, "(M − 24) × 0.02 + 3", "Los bros"),
            "ketupatkepat": (35, 0.03, 8, "(M − 35) × 0.03 + 8", "Ketupat kepat"),
            "nuclearodinossauro": (15, 0.05, 7, "(M − 15) × 0.05 + 7", "Nuclearo dinossauro"),
            "tralaledon": (27.5, 0.03, 10, "(M − 27.5) × 0.03 + 10", "Tralaledon"),
            "ketchuruandmusturu": (42.5, 0.03, 12, "(M − 42.5) × 0.03 + 12", "Ketchuru and musturu"),
            "lasupremecombinasion": (40, 0.11, 25, "(M − 40) × 0.11 + 25", "La supreme combinasion"),

            # === LISTA 2 ===
            "lassis": (17.5, 0.02, 1.5, "(M − 17.5) × 0.02 + 1.5", "Las sis"),
            "tacoritabicicleta": (16.5, 0.02, 2, "(M − 16.5) × 0.02 + 2", "Tacorita bicicleta"),
            "laextinctgrande": (23.5, 0.02, 3, "(M − 23.5) × 0.02 + 3", "La extinct grande"),
            "lostacoritas": (32, 0.03, 3, "(M − 32) × 0.03 + 3", "Los tacoritas"),
            "celularciniviciosini": (22.5, 0.02, 3, "(M − 22.5) × 0.02 + 3", "Celularcini viciosini"),
            "losprimos": (31, 0.02, 3.5, "(M − 31) × 0.02 + 3.5", "Los primos"),
            "spaghettitualetti": (60, 0.02, 5, "(M − 60) × 0.02 + 5", "Spaghetti tualetti"),
            "tictacsahur": (37.5, 0.04, 7, "(M − 37.5) × 0.04 + 7", "Tictac sahur"),
            "garamaandmadundung": (50, 0.05, 20, "(M − 50) × 0.05 + 20", "Garama and madundung"),
            "dragoncannelloni": (200, 0.08, 90, "(M − 200) × 0.08 + 90", "Dragon cannelloni"),

            # === LISTA 3 ===
            "chillinchili": (25, 0.02, 3, "(M − 25) × 0.02 + 3", "Chillin chili"),
            "eviledon": (31.5, 0.02, 4.5, "(M − 31.5) × 0.02 + 4.5", "Eviledon"),
            "tangtangkelentang": (33.5, 0.04, 5, "(M − 33.5) × 0.04 + 5", "Tang tang kelentang"),
            "moneymoneypuggy": (21, 0.03, 5, "(M − 21) × 0.03 + 5", "Money money puggy"),
            "lassecretcombinasion": (125, 0.05, 10, "(M − 125) × 0.05 + 10", "La secret combinasion"),
            "burguroandfryuro": (150, 0.05, 30, "(M − 150) × 0.05 + 30", "Burguro and fryuro"),
            "strawberryelephant": (350, 0.30, 700, "(M − 350) × 0.30 + 700", "Strawberry elephant"),

            # === LISTA 4 - HALLOWEEN ===
            "laspookygrande": (24.5, 0.02, 2.5, "(M − 24.5) × 0.02 + 2.5", "La spooky grande"),
            "losspookycombinasionas": (20, 0.02, 2, "(M − 20) × 0.02 + 2", "Los spooky combinasionas"),
            "mieteteirabicicleteira": (26, 0.02, 3, "(M − 26) × 0.02 + 3", "Mieteteira bicicleteira"),
            "chipsoandqueso": (25, 0.02, 4, "(M − 25) × 0.02 + 4", "Chipso and queso"),
            "latacocombinasion": (35, 0.03, 4, "(M − 35) × 0.03 + 4", "La taco combinasion"),
            "lacasa": (100, 0.05, 12, "(M − 100) × 0.05 + 12", "La casa boo"),
            "spookyandpumpky": (80, 0.05, 22, "(M − 80) × 0.05 + 22", "Spooky and pumpky"),
            "headless": (175, 0.08, 30, "(M − 175) × 0.08 + 30", "Headless horseman"),
            "meowl": (275, 0.30, 500, "(M − 275) × 0.30 + 500", "Meowl"),
        }

        self.aliases = {
            # === LISTA 1 ===
            "es": "esoksekolah", "sekolah": "esoksekolah", "esok": "esoksekolah",
            "lc": "loscombinasionas", "combinasionas": "loscombinasionas", "comb": "loscombinasionas", "combina": "loscombinasionas",
            "lgc": "lagrandecombinasion", "grande": "lagrandecombinasion", "lgr": "lagrandecombinasion",
            "lhp": "loshotspositos", "hots": "loshotspositos", "positos": "loshotspositos",
            "lb": "losbros", "bros": "losbros", "br": "losbros",
            "kk": "ketupatkepat", "ketupat": "ketupatkepat", "kepat": "ketupatkepat",
            "nd": "nuclearodinossauro", "nuclear": "nuclearodinossauro", "dino": "nuclearodinossauro",
            "tr": "tralaledon", "tralale": "tralaledon", "tral": "tralaledon",
            "km": "ketchuruandmusturu", "musturu": "ketchuruandmusturu", "ketchuru": "ketchuruandmusturu",
            "lsc": "lasupremecombinasion", "supreme": "lasupremecombinasion", "sup": "lasupremecombinasion",

            # === LISTA 2 ===
            "ls": "lassis", "sis": "lassis", "lasi": "lassis",
            "tb": "tacoritabicicleta", "taco": "tacoritabicicleta", "bici": "tacoritabicicleta",
            "leg": "laextinctgrande", "extinct": "laextinctgrande", "ext": "laextinctgrande",
            "lt": "lostacoritas", "tacoritas": "lostacoritas", "taco2": "lostacoritas",
            "ccv": "celularciniviciosini", "celular": "celularciniviciosini", "vicio": "celularciniviciosini",
            "lp": "losprimos", "primos": "losprimos", "prim": "losprimos",
            "st": "spaghettitualetti", "spaghetti": "spaghettitualetti", "tua": "spaghettitualetti",
            "ts": "tictacsahur", "tictac": "tictacsahur", "sahur": "tictacsahur",
            "gm": "garamaandmadundung", "garama": "garamaandmadundung", "madundung": "garamaandmadundung",
            "dc": "dragoncannelloni", "dragon": "dragoncannelloni", "drag": "dragoncannelloni",

            # === LISTA 3 ===
            "cc": "chillinchili", "chili": "chillinchili", "chill": "chillinchili",
            "ev": "eviledon", "evil": "eviledon", "edon": "eviledon",
            "ttk": "tangtangkelentang", "kelentang": "tangtangkelentang", "tang": "tangtangkelentang",
            "mmp": "moneymoneypuggy", "puggy": "moneymoneypuggy", "money": "moneymoneypuggy",
            "lsec": "lassecretcombinasion", "secret": "lassecretcombinasion", "sec": "lassecretcombinasion",
            "bf": "burguroandfryuro", "burguro": "burguroandfryuro", "fryuro": "burguroandfryuro",
            "se": "strawberryelephant", "straw": "strawberryelephant", "elephant": "strawberryelephant",

            # === LISTA 4 - HALLOWEEN ===
            "lsg": "laspookygrande", "spooky": "laspookygrande", "spook": "laspookygrande", "spookygrande": "laspookygrande",
            "lsc2": "losspookycombinasionas", "spookycomb": "losspookycombinasionas",
            "mb": "mieteteirabicicleteira", "miete": "mieteteirabicicleteira", "bicicleteira": "mieteteirabicicleteira",
            "cq": "chipsoandqueso", "chipso": "chipsoandqueso", "queso": "chipsoandqueso",
            "ltc": "latacocombinasion", "tacocomb": "latacocombinasion",
            "lcb": "lacasa", "boo": "lacasa", "casa": "lacasa",
            "sp": "spookyandpumpky", "pumpky": "spookyandpumpky", "spump": "spookyandpumpky", "spookypump": "spookyandpumpky",
            "hh": "headless", "horseman": "headless", "head": "headless",
            "meow": "meowl", "meo": "meowl", "miau": "meowl",
        }

    def make_embed(self, ctx, nombre: str, formula: str, operacion: str, resultado: float, pretty: str):
        embed = discord.Embed(
            title=f"Calculadora de Precios - {pretty}",
            description=f"Conversión automática usando la fórmula de **{pretty}**",
            color=discord.Color.blurple()
        )
        embed.add_field(name="Fórmula", value=f"`{formula}`", inline=False)
        embed.add_field(name="Operación", value=f"`{operacion}`", inline=False)
        embed.add_field(name="Resultado", value=f"**${resultado:.2f}**", inline=False)
        embed.set_footer(text=f"Pedido por {ctx.author}", icon_url=ctx.author.display_avatar.url)
        return embed

    def error_embed(self, ctx, msg: str):
        return discord.Embed(
            title="Error en el comando",
            description=msg,
            color=discord.Color.red()
        ).set_footer(text=f"Pedido por {ctx.author}", icon_url=ctx.author.display_avatar.url)

    @commands.command(name="precio", aliases=["price", "cost", "valor"])
    async def precio(self, ctx, nombre: str = None, m: float = None):
        if not nombre:
            return await ctx.send(embed=self.error_embed(
                ctx, f"Debes especificar el nombre. Ejemplo: `{ctx.prefix}{ctx.command} spooky 100`"
            ))
        nombre = nombre.lower()
        if nombre in self.aliases:
            nombre = self.aliases[nombre]
        if nombre not in self.formulas:
            sugerencias = [k for k in self.formulas.keys() if nombre in k] or [k for k, v in self.aliases.items() if nombre in k]
            sugerencia = f" ¿Quisiste decir `{sugerencias[0]}`?" if sugerencias else ""
            return await ctx.send(embed=self.error_embed(ctx, f"No encontré **{nombre}**.{sugerencia}"))
        if m is None:
            return await ctx.send(embed=self.error_embed(
                ctx, f"Debes especificar la cantidad de millones. Ejemplo: `{ctx.prefix}{ctx.command} {nombre} 100`"
            ))
        base, mult, suma, formula, pretty = self.formulas[nombre]
        result = max(0, (m - base) * mult + suma)
        operacion = f"( {m} − {base} ) × {mult} + {suma}"
        await ctx.send(embed=self.make_embed(ctx, nombre, formula, operacion, result, pretty))

    @commands.command(name="helpprices", aliases=["precios", "listaprecios"])
    async def helpprices(self, ctx):
        formulas_items = sorted(self.formulas.items(), key=lambda x: x[1][4])
        embeds = []
        prefixes = ["precio", "valor", "cost", "price"]
        pages = [formulas_items[i:i + 10] for i in range(0, len(formulas_items), 10)]
        for i, page in enumerate(pages, start=1):
            embed = discord.Embed(
                title="Lista de Precios Brainrots*",
                description="Usa: `,precio <alias> <millones>`\nEj: `,precio meowl 300`",
                color=discord.Color.orange()
            )
            for key, (_, _, _, _, pretty) in page:
                aliases = [a for a, real in self.aliases.items() if real == key]
                alias_str = f"`{', '.join([key] + aliases[:3])}`" + ("..." if len(aliases) > 3 else "")
                ejemplos = " | ".join([f"`${p} {aliases[0] if aliases else key} 100`" for p in prefixes[:2]])
                embed.add_field(
                    name=f"{pretty}",
                    value=f"**Alias:** {alias_str}\n**Ej:** {ejemplos}",
                    inline=False
                )
            embed.set_footer(text=f"Página {i}/{len(pages)} • Total: {len(self.formulas)} ítems")
            embeds.append(embed)
        message = await ctx.send(embed=embeds[0])
        if len(embeds) > 1:
            await message.add_reaction("Left Arrow")
            await message.add_reaction("Right Arrow")
            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["Left Arrow", "Right Arrow"] and reaction.message.id == message.id
            current_page = 0
            while True:
                try:
                    reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
                except asyncio.TimeoutError:
                    await message.clear_reactions()
                    break
                if str(reaction.emoji) == "Right Arrow" and current_page < len(embeds) - 1:
                    current_page += 1
                    await message.edit(embed=embeds[current_page])
                elif str(reaction.emoji) == "Left Arrow" and current_page > 0:
                    current_page -= 1
                    await message.edit(embed=embeds[current_page])
                try:
                    await message.remove_reaction(reaction, user)
                except:
                    pass

async def setup(bot):
    await bot.add_cog(Precios(bot))
