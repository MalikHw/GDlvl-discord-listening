import os
import re
import json
import requests
import discord
from discord import app_commands
from dotenv import load_dotenv
from discord.ext import commands
from dashlib import fetchLevel, TYPE_LISTOFID

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents) # Wont be used anyway
tree = bot.tree

FACE_DIFFICULTY_NAMES = {
    1: "Easy",
    2: "Normal",
    3: "Hard",
    4: "Harder",
    5: "Insane",
}
DEMON_FACE_DIFFICULTY_NAMES = {
    3: "Easy Demon",
    4: "Medium Demon",
    0: "Hard Demon",
    5: "Insane Demon",
    6: "Extreme Demon",
}


DATA_FILE = "channels.json"
def load_channels() -> dict:
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading channels from {DATA_FILE}: {e}")
        return {}

target_channels = load_channels()

def save_channels(data: dict) -> None:
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

target_channels: dict = load_channels()

@tree.command(name="set_channel", description="Set here where GD level IDs will be detected+sent its info.")
@app_commands.describe(channel="the channel to monitor")
async def set_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    target_channels[str(interaction.guild_id)] = channel.id
    save_channels(target_channels)
    await interaction.response.send_message(f"Channel set to: {channel.mention}. Imma see shi here :3", ephemeral=True)

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    
    target_channel_id = target_channels.get(str(message.guild.id))
    if target_channel_id is None or message.channel.id != target_channel_id:
        return

    match = re.search(r'\b\d{6,10}\b', message.content)
    if not match:
        return

    level_id = match.group(0)
    try:
        level = fetchLevel(int(level_id))
    except Exception as e:
        print(f"error fetching level info for {level_id}: {e}")
        return

    if level.levelID == 0 or level.levelID != int(level_id):
        return

    creator = f"Creator's Player ID: {level.playerID}"
    try:
        user_resp = requests.post(
            "https://www.boomlings.com/database/getGJUsers20.php",
            data={"secret": "Wmfd2893gb7", "str": str(level.playerID), "gameVersion": "22",},
            headers={"User-Agent": ""},
            timeout=10
        )
        if user_resp.text and ":" in user_resp.text:
            parts = user_resp.text.split("#")[0].split(":") # # is leaderboard part anyway
            fields = dict(zip(parts[::2], parts[1::2]))
            if fields.get("1"):
                creator = fields["1"]
    except Exception as e:
        print(f"error fetching creator info for {level.playerID}: {e}")

    name = level.levelName
    stars = level.stars if hasattr(level, 'stars') and level.stars else 0
    is_rated = stars > 0
    likes = level.likes if hasattr(level, 'likes') and level.likes else 0
    downloads = level.downloads if hasattr(level, 'downloads') and level.downloads else 0 
    if level.isAuto:
        difficulty = "Auto"
    elif level.isDemon:
        difficulty = DEMON_FACE_DIFFICULTY_NAMES.get(level.demonDifficulty, "Demon")
    elif level.difficultyDenominator != 10:
        difficulty = "unrated"
    else:
        difficulty = FACE_DIFFICULTY_NAMES.get(level.difficultyNumerator // 10, "Unrated")

    # length int to str
    LENGTH_NAMES = {0: "Tiny", 1: "Short", 2: "Medium", 3: "Long", 4: "XL", 5: "Platformer"}
    length = LENGTH_NAMES.get(level.length, "Unknown") if hasattr(level, 'length') else "Unknown"

    description = level.description if hasattr(level, 'description') and level.description else "No description provided."
    # ok NOW we make the fucking message
    response = f"Level Name **{name}**\nMade by **{creator}**\n"
    if is_rated:
        response += f"\n**Got {stars} stars**."
    else:
        response += ""
    response += f"\n**{likes} likes** and **{downloads} downloads**.\n"
    response += f"\nDifficulty: **{difficulty}**\n"
    response += f"\nLength: **{length}**\n"
    response += f"\nDescription: **{description}**"
    response += f"\n-# Bot by [MalikHw47](https://malikhw.me). If you find this useful. Consider donating? [Donate to bot developer](https://malikhw.me/donate)"
    await message.reply(response, mention_author=False)

@bot.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    print(f"Synced slash commands i guess")
    print(f"If you find this useful. Consider donating? https://malikhw.me/donate")

if __name__ == "__main__":
    bot.run(TOKEN)