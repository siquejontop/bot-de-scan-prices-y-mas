import discord
from discord.ext import commands
import asyncio

class Precios(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # ============================================
        #                   FORMULAS
        # ============================================
        self.formulas = {
            "esoksekolah": (30, 0.01, 1, "(M − 30) × 0.01 + 1", "Esok sekolah"),
            "loscombinasionas": (15, 0.01, 1.5, "(M − 15) × 0.01 + 1.5", "Los combinasionas"),
            "lagrandecombinasion": (10, 0.02, 1.5, "(M − 10) × 0.02 + 1.5", "La grande combinasion"),
            "loshotspositos": (20, 0.02, 2, "(M − 20) × 0.02 + 2", "Los hotspositos"),
            "losbros": (24, 0.02, 3, "(M − 24) × 0.02 + 3", "Los bros"),
            "ketupatkepat": (35, 0.02, 8, "(M − 35) × 0.02 + 8", "Ketupat kepat"),
            "nuclearodinossauro": (15, 0.03, 7, "(M − 15) × 0.03 + 7", "Nuclearo dinossauro"),
            "tralaledon": (27.5, 0.02, 7, "(M − 27.5) × 0.02 + 7", "Tralaledon"),
            "ketchuruandmusturu": (42.5, 0.03, 12, "(M − 42.5) × 0.03 + 12", "Ketchuru and musturu"),
            "lasupremecombinasion": (40, 0.11, 25, "(M − 40) × 0.11 + 25", "La supreme combinasion"),

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

            "chillinchili": (25, 0.02, 3, "(M − 25) × 0.02 + 3", "Chillin chili"),
            "eviledon": (31.5, 0.02, 4.5, "(M − 31.5) × 0.02 + 4.5", "Eviledon"),
            "tangtangkelentang": (33.5, 0.04, 5, "(M − 33.5) × 0.04 + 5", "Tang tang kelentang"),
            "moneymoneypuggy": (21, 0.03, 5, "(M − 21) × 0.03 + 5", "Money money puggy"),
            "lassecretcombinasion": (125, 0.05, 10, "(M − 125) × 0.05 + 10", "La secret combinasion"),
            "burguroandfryuro": (150, 0.05, 30, "(M − 150) × 0.05 + 30", "Burguro and fryuro"),
            "strawberryelephant": (350, 0.30, 700, "(M − 350) × 0.30 + 700", "Strawberry elephant"),

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

        # ============================================
        #                ALIASES MEGAPACK
        # ============================================
        self.aliases = {
            # Esok sekolah
            "es": "esoksekolah", "sek": "esoksekolah", "sekolah": "esoksekolah",
            "esok": "esoksekolah", "esoksk": "esoksekolah", "skl": "esoksekolah",

            # Los combinasionas
            "lc": "loscombinasionas", "comb": "loscombinasionas",
            "combi": "loscombinasionas", "combina": "loscombinasionas",
            "lcmb": "loscombinasionas",

            # Grande combinasion
            "lgc": "lagrandecombinasion", "lg": "lagrandecombinasion",
            "bigcomb": "lagrandecombinasion",

            # Hotspósitos
            "lhp": "loshotspositos", "hots": "loshotspositos", "positos": "loshotspositos",
            "hotsp": "loshotspositos",

            # Bros
            "lb": "losbros", "bros": "losbros", "br": "losbros", "bro": "losbros",

            # Ketupat kepat
            "kk": "ketupatkepat", "ket": "ketupatkepat", "kep": "ketupatkepat",
            "ketupat": "ketupatkepat", "kepat": "ketupatkepat",

            # Nuclearo dinossauro
            "nd": "nuclearodinossauro", "nuke": "nuclearodinossauro",
            "dino": "nuclearodinossauro", "dn": "nuclearodinossauro",

            # Tralaledon
            "tr": "tralaledon", "tral": "tralaledon", "lale": "tralaledon",

            # Ketchuru & musturu
            "km": "ketchuruandmusturu", "musturu": "ketchuruandmusturu",
            "ketchuru": "ketchuruandmusturu",

            # Las sis
            "ls": "lassis", "sis": "lassis",

            # Tacorita bicicleta
            "tb": "tacoritabicicleta", "taco": "tacoritabicicleta",
            "bici": "tacoritabicicleta",

            # Extinct grande
            "leg": "laextinctgrande", "ext": "laextinctgrande",

            # Tacoritas
            "lt": "lostacoritas", "tacoritas": "lostacoritas",

            # Celularcini viciosini
            "ccv": "celularciniviciosini", "celular": "celularciniviciosini",
            "vicio": "celularciniviciosini",

            # Primos
            "lp": "losprimos", "prim": "losprimos",

            # Spaghetti tualetti
            "st": "spaghettitualetti",

            # Tictac sahur
            "ts": "tictacsahur",

            # Garama & madundung
            "gm": "garamaandmadundung",

            # Dragon cannelloni
            "dc": "dragoncannelloni", "dragon": "dragoncannelloni",

            # Chillin chili
            "cc": "chillinchili", "chili": "chillinchili",

            # Eviledon
            "ev": "eviledon",

            # Tang tang kelentang
            "ttk": "tangtangkelentang",

            # Money money puggy
            "mmp": "moneymoneypuggy", "puggy": "moneymoneypuggy",

            # Secret combinasion
            "lsec": "lassecretcombinasion",

            # Burguro & fryuro
            "bf": "burguroandfryuro",

            # Strawberry elephant
            "se": "strawberryelephant",

            # Spooky grande
            "lsg": "laspookygrande",

            # Spooky combinasionas
            "lsc": "losspookycombinasionas",

            # Bicicleteira
            "mb": "mieteteirabicicleteira",

            # Chipso y queso
            "cq": "chipsoandqueso",

            # Taco combinasion
            "ltc": "latacocombinasion",

            # Casa boo
            "lcb": "lacasa",

            # Spooky pumpky
            "sp": "spookyandpumpky",

            # Headless horseman
            "hh": "headless", "horseman": "headless",

            # Meowl  
            "meow": "meowl", "meo": "meowl", "miau": "meowl",
        }

        # ===============================================================
        # EMBED GENERATORS
        # ===============================================================

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

    # ===============================================================
    #                    COMANDO PRECIO
    # ===============================================================
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
            sugerencias = [k for k in self.formulas.keys() if nombre in k] or [
                k for k, v in self.aliases.items() if nombre in k
            ]
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

    # ===============================================================
    #                   LISTA DE PRECIOS
    # ===============================================================
    @commands.command(name="helpprices", aliases=["precios", "listaprecios"])
    async def helpprices(self, ctx):

        formulas_items = sorted(self.formulas.items(), key=lambda x: x[1][4])
        embeds = []

        pages = [formulas_items[i:i + 9] for i in range(0, len(formulas_items), 9)]
        left_arrow = "⬅️"
        right_arrow = "➡️"

        for i, page in enumerate(pages, start=1):
            embed = discord.Embed(
                title="📘 Lista de Precios Brainrots",
                description="Usa: `,precio <alias> <millones>`\nEj: `,precio meowl 300`",
                color=discord.Color.orange()
            )

            for key, (_, _, _, _, pretty) in page:
                aliases = [a for a, real in self.aliases.items() if real == key]

                alias_str = ", ".join([f"`{key}`"] + [f"`{a}`" for a in aliases][:4])
                if len(aliases) > 4:
                    alias_str += " …"

                ejemplo = aliases[0] if aliases else key

                embed.add_field(
                    name=f"⭐ {pretty}",
                    value=f"**Alias:** {alias_str}\n**Ejemplo:** `,precio {ejemplo} 100`",
                    inline=False
                )

            embed.set_footer(text=f"Página {i}/{len(pages)} • Total: {len(self.formulas)} ítems")
            embeds.append(embed)

        message = await ctx.send(embed=embeds[0])

        if len(embeds) == 1:
            return

        await message.add_reaction(left_arrow)
        await message.add_reaction(right_arrow)

        current_page = 0

        def check(reaction, user):
            return (
                user == ctx.author
                and reaction.message.id == message.id
                and str(reaction.emoji) in [left_arrow, right_arrow]
            )

        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=60, check=check)
            except asyncio.TimeoutError:
                await message.clear_reactions()
                break

            if str(reaction.emoji) == right_arrow and current_page < len(embeds) - 1:
                current_page += 1
                await message.edit(embed=embeds[current_page])

            elif str(reaction.emoji) == left_arrow and current_page > 0:
                current_page -= 1
                await message.edit(embed=embeds[current_page])

            try:
                await message.remove_reaction(reaction.emoji, user)
            except:
                pass


async def setup(bot):
    await bot.add_cog(Precios(bot))
