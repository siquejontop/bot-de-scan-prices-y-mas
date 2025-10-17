import discord
from discord.ext import commands
import os
import json
from datetime import datetime

# 📁 Carpeta donde se guardarán los backups
BACKUP_FOLDER = "/app/backups"

class BackupSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # =====================================================
    # 💾 GUARDAR BACKUP MANUAL
    # =====================================================
    @commands.command(name="backup")
    @commands.is_owner()
    async def backup(self, ctx):
        """Guarda un backup manual del servidor actual."""
        guild = ctx.guild

        await ctx.send("🧠 Creando backup, por favor espera...")

        data = {
            "guild_name": guild.name,
            "guild_description": guild.description,
            "roles": [],
            "categories": [],
            "channels": [],
        }

        # === Roles ===
        for role in guild.roles:
            data["roles"].append({
                "id": role.id,
                "name": role.name,
                "permissions": role.permissions.value,
                "color": role.color.value,
                "hoist": role.hoist,
                "mentionable": role.mentionable,
                "position": role.position
            })

        # === Categorías ===
        for category in guild.categories:
            data["categories"].append({
                "id": category.id,
                "name": category.name,
                "position": category.position
            })

        # === Canales ===
        for channel in guild.channels:
            overwrites = {}
            for target, perms in channel.overwrites.items():
                overwrites[str(target.id)] = perms._values

            channel_data = {
                "id": channel.id,
                "name": channel.name,
                "type": str(channel.type),
                "position": channel.position,
                "category": channel.category.id if channel.category else None,
                "overwrites": overwrites
            }

            if isinstance(channel, discord.TextChannel):
                channel_data.update({
                    "topic": channel.topic,
                    "nsfw": channel.nsfw,
                    "slowmode_delay": channel.slowmode_delay,
                })
            elif isinstance(channel, discord.VoiceChannel):
                channel_data.update({
                    "user_limit": channel.user_limit,
                    "bitrate": channel.bitrate,
                })

            data["channels"].append(channel_data)

        # === Guardar en archivo ===
        os.makedirs(BACKUP_FOLDER, exist_ok=True)
        file_name = f"{BACKUP_FOLDER}/backup_{guild.id}_{int(datetime.utcnow().timestamp())}.json"
        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        await ctx.send(f"✅ Backup guardado correctamente en `{file_name}`")

    # =====================================================
    # ♻️ RESTAURAR BACKUP
    # =====================================================
    @commands.command(name="restore")
    @commands.is_owner()
    async def restore(self, ctx, backup_file: str):
        """Restaura un backup desde un archivo JSON guardado en /app/backups."""
        if os.path.isabs(backup_file):
            path = backup_file
        else:
            path = os.path.join(BACKUP_FOLDER, backup_file)

        if not os.path.exists(path):
            return await ctx.send("❌ No encontré ese archivo de backup.")

        await ctx.send("⚙️ Restaurando backup, esto puede tardar un poco...")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            guild = ctx.guild

            # 1️⃣ Eliminar roles y canales existentes
            for channel in guild.channels:
                try:
                    await channel.delete()
                except:
                    pass
            for role in guild.roles:
                if not role.is_default():
                    try:
                        await role.delete()
                    except:
                        pass

            # 2️⃣ Restaurar roles
            role_map = {}
            for role_data in sorted(data["roles"], key=lambda r: r["position"]):
                try:
                    role = await guild.create_role(
                        name=role_data["name"],
                        permissions=discord.Permissions(role_data["permissions"]),
                        colour=discord.Colour(role_data["color"]),
                        hoist=role_data["hoist"],
                        mentionable=role_data["mentionable"]
                    )
                    role_map[str(role_data["id"])] = role
                except Exception as e:
                    print(f"❌ Error creando rol {role_data['name']}: {e}")

            # 3️⃣ Restaurar categorías
            category_map = {}
            for category_data in data["categories"]:
                try:
                    cat = await guild.create_category(
                        name=category_data["name"],
                        position=category_data["position"]
                    )
                    category_map[str(category_data["id"])] = cat
                except Exception as e:
                    print(f"❌ Error creando categoría {category_data['name']}: {e}")

            # 4️⃣ Restaurar canales
            for channel_data in data["channels"]:
                try:
                    category = category_map.get(str(channel_data["category"]))
                    overwrites = {}
                    for target_id, perm_values in channel_data["overwrites"].items():
                        target = role_map.get(target_id) or guild.get_member(int(target_id))
                        if target:
                            overwrites[target] = discord.PermissionOverwrite(**perm_values)

                    if "text" in channel_data["type"]:
                        await guild.create_text_channel(
                            name=channel_data["name"],
                            topic=channel_data.get("topic"),
                            nsfw=channel_data.get("nsfw", False),
                            slowmode_delay=channel_data.get("slowmode_delay", 0),
                            category=category,
                            overwrites=overwrites,
                            position=channel_data["position"]
                        )
                    elif "voice" in channel_data["type"]:
                        await guild.create_voice_channel(
                            name=channel_data["name"],
                            user_limit=channel_data.get("user_limit", 0),
                            bitrate=channel_data.get("bitrate", 64000),
                            category=category,
                            overwrites=overwrites,
                            position=channel_data["position"]
                        )
                except Exception as e:
                    print(f"❌ Error creando canal {channel_data['name']}: {e}")

            await ctx.send(f"✅ Backup restaurado correctamente desde `{backup_file}`")

        except Exception as e:
            await ctx.send(f"⚠️ Error restaurando backup: `{e}`")

async def setup(bot):
    await bot.add_cog(BackupSystem(bot))
