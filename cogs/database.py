import motor.motor_asyncio
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

class Database(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            raise ValueError("⚠️ No se encontró MONGO_URI en las variables de entorno.")
        self.client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
        self.db = self.client["siquej_db"]  # nombre de tu base de datos
        print("✅ Conectado a MongoDB correctamente.")

    @commands.Cog.listener()
    async def on_ready(self):
        print("🗃️ Cog Database cargado correctamente.")

    async def get_user_data(self, user_id: int):
        """Obtiene los datos del usuario, o los crea si no existen"""
        users = self.db["users"]
        user = await users.find_one({"_id": user_id})
        if not user:
            user = {"_id": user_id, "kisses": 0, "hugs": 0, "slaps": 0}
            await users.insert_one(user)
        return user

    async def add_interaction(self, user_id: int, field: str):
        """Suma 1 al contador indicado (por ejemplo, 'kisses' o 'hugs')"""
        users = self.db["users"]
        await users.update_one(
            {"_id": user_id},
            {"$inc": {field: 1}},
            upsert=True
        )

# 👇 ESTA PARTE ES LA QUE FALTABA 👇
async def setup(bot):
    await bot.add_cog(Database(bot))
