import discord
import random
import time
import re
from discord.ext import commands
import asyncio


class Reaction(commands.Cog, name="message_reactions"):
    """Reacts to various chat messages with emotes or messages."""
    prefix = "react"
    
    def __init__(self, bot):
        self.bot = bot
        self.init_db(self.bot.cursor)

    def init_db(self, cursor):
        cursor.execute("begin")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS react_timer ("
            "guild INTEGER,"  # Snowflake of the guild.
            "reaction_id INTEGER,"  # Snowflake of the emoji, or unicode emoji hashed.
            "last_react INTEGER,"  # Timestamp of when this was last triggered; UTC seconds.
            "reactions_today INTEGER"  # MISNOMER: "Today" is incorrect. It's actually, how many reactions have happened within the cooldown window. 
            ")")
        cursor.execute("commit")

    @commands.Cog.listener()
    async def on_message(self, message):
        if not await self.bot.has_perm(message, dm=False): return

        await self.generic_react(message, r"^.*?yap", 60 * 10, 0.6, "<yap:1462729662496247922>", 1462729662496247922)
        await self.generic_react(message, r"(?:.*?\W|^)(?:gay|homo)(?:\W|$)", 60 * 10, 0.3, "🏳️‍🌈", hash("🏳️‍🌈"))

        # Animal reacts.
        animal_react_delay = 60 * 10
        animal_react_chance = 0.5
        await self.generic_react(message, r"(?:.*?\W|^)(?:rat|squeak)(?:\W|$)", animal_react_delay, animal_react_chance, "🐀", hash("🐀"))
        await self.generic_react(message, r"(?:.*?\W|^)(?:dog|woof)(?:\W|$)", animal_react_delay, animal_react_chance, "🐕‍🦺", hash("🐕‍🦺"))
        await self.generic_react(message, r"(?:.*?\W|^)(?:cat|meow)(?:\W|$)", animal_react_delay, animal_react_chance, "🐱", hash("🐱"))
        await self.generic_react(message, r"(?:.*?\W|^)(?:deer)(?:\W|$)", animal_react_delay, animal_react_chance, "🦌", hash("🦌"))
        await self.generic_react(message, r"(?:.*?\W|^)(?:horse)(?:\W|$)", animal_react_delay, animal_react_chance, "🐎", hash("🐎"))
        await self.generic_react(message, r"(?:.*?\W|^)(?:goat)(?:\W|$)", animal_react_delay, animal_react_chance, "🐐", hash("🐐"))
        await self.generic_react(message, r"(?:.*?\W|^)(?:duck|quack)(?:\W|$)", animal_react_delay, animal_react_chance, "🦆", hash("🦆"))
        await self.generic_react(message, r"(?:.*?\W|^)(?:shark)(?:\W|$)", animal_react_delay, animal_react_chance, "🦈", hash("🦈"))
        await self.generic_react(message, r"(?:.*?\W|^)(?:dragon|rawr)(?:\W|$)", animal_react_delay, animal_react_chance, "🐉", hash("🐉"))
        await self.generic_react(message, r"(?:.*?\W|^)(?:snake|snek|snep|hiss)(?:\W|$)", animal_react_delay, animal_react_chance, "🐍", hash("🐍"))
        await self.generic_react(message, r"(?:.*?\W|^)(?:car)(?:\W|$)", animal_react_delay, animal_react_chance, "<carbold:1462921633177141318>", 1462921633177141318)

        # Username reacts
        username_react_delay = 60 * 10
        username_react_chance = 0.3
        await self.generic_react(message, r"(?:.*?\W|^)(?:mooni|sleepy|eepy)(?:\W|$)", username_react_delay, username_react_chance, "☕", hash("☕"))
        await self.generic_react(message, r"(?:.*?\W|^)(?:dani|tiny|bird)(?:\W|$)", username_react_delay, username_react_chance, random.choice(["<dani:1462920859596619880>", "<dani_giggle:1462931410921984103>", "<dani_love:1462931657953644595>", "<dani_threaten:1462931810311733380>"]), 1462920859596619880)
        await self.generic_react(message, r"(?:.*?\W|^)(?:kobold|lizard|lizzer|will|balaur)(?:\W|$)", username_react_delay, 1, random.choice(["<carbold:1462921633177141318>", "<tinybold:1462923072007835753>", "<lizzer:1462923230011588639>", "<polite:1462923370717905026>"]), 1462923370717905026, max_reactions_before_cooldown=6)
        await self.generic_react(message, r"(?:.*?\W|^)(?:kyro|derg)(?:\W|$)", username_react_delay, username_react_chance, "🍜", hash("🍜"))
        await self.generic_react(message, r"(?:.*?\W|^)(?:kev|otter)(?:\W|$)", username_react_delay, username_react_chance, random.choice(["<kev_laugh:1462926223561986088>", "🦦"]), 1462926223561986088)
        await self.generic_react(message, r"(?:.*?\W|^)(?:zillu|bunny|rabbit)(?:\W|$)", username_react_delay, username_react_chance, random.choice(["<zillu_clap:1462925490837917777>", "<zillu_close:1462925547339387087>", "<zillu_bean:1462925555966935245>", "🐇"]), 1462925547339387087)
        await self.generic_react(message, r"(?:.*?\W|^)(?:adam|panda|wolf)(?:\W|$)", username_react_delay, username_react_chance, random.choice(["🐺", "🦝"]), hash("🐺"))

    async def generic_react(self, message: discord.Message,
                            regex: str, timer: int, chance: float,
                            reaction: str, reaction_id: int,
                            remove_reaction_chance: float = 0.3, remove_reaction_delay: float = 1,
                            max_reactions_before_cooldown: int = 3, max_reactions_cooldown: int = 60 * 60 * 12) -> bool:
        self.bot.cursor.execute(f"SELECT rowid, * FROM react_timer WHERE reaction_id={reaction_id} AND guild={message.guild.id}")
        db_entry = self.bot.cursor.fetchone()
        current_time = int(time.time())
        if db_entry:
            time_since_last_reaction = current_time - db_entry["last_react"]
            if time_since_last_reaction <= timer:
                return False
            if db_entry["reactions_today"] >= max_reactions_before_cooldown and time_since_last_reaction <= max_reactions_cooldown:
                return False
        if not re.match(regex, message.content.lower()):
            return False
        if random.random() > chance:
            return False

        await message.add_reaction(reaction)
        react_chain = 1
        if db_entry:
            time_since_last_reaction = current_time - db_entry["last_react"]
            if time_since_last_reaction <= max_reactions_before_cooldown:
                react_chain = db_entry["reactions_today"] + 1
            self.bot.cursor.execute(f"UPDATE react_timer SET last_react={current_time}, reactions_today={react_chain} WHERE rowid={db_entry['rowid']}")
        else:
            self.bot.cursor.execute(f"INSERT INTO react_timer VALUES(?,?,?,?)", (message.guild.id, reaction_id, current_time, react_chain))
        self.bot.cursor.execute("commit")

        if random.random() > remove_reaction_chance:
            return True
        await asyncio.sleep(remove_reaction_delay)
        await message.remove_reaction(reaction, self.bot.user)
        return True

    async def rename_on_im(self, server, message):
        im_response = re.match(r"i[']?(?:m| am) ?(.{1,32})(?:$|[ ,.!])", message.content, flags=re.IGNORECASE)
        if server and im_response:
            name = im_response.group(1).strip()
            try:
                await message.author.edit(reason="They said \"I'm\" and that must be punished.", nick=name)
            except discord.errors.Forbidden:
                pass


async def setup(bot):
    #bot.core_help_text["modules"] += ["react"]
    await bot.add_cog(Reaction(bot))
