import discord
import random
import time
import re
from discord.ext import commands
import asyncio
from dataclasses import dataclass, field
from typing import List
from pathlib import Path
import helpers
from json import loads


class Reaction(commands.Cog, name="message_reactions"):
    """Reacts to various chat messages with emotes or messages."""
    prefix = "react"
    
    def __init__(self, bot):
        self.bot = bot
        self.init_db(self.bot.cursor)
        self.generic_reactions = self.get_generic_reactions()

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

    def get_generic_reactions(self) -> List['GenericReaction']:
        generic_reactions = []
        reaction_data = {}
        with open(Path("data", "reactions.json"), "r", encoding="utf-8") as f:
            json_text = helpers.remove_python_comments(f.read())
            reaction_data = loads(json_text)  # API tokens/bot settings

        defaults = reaction_data["default"]
        for reaction in reaction_data["reactions"]:
            generic_reactions.append(GenericReaction.create_from_data(reaction, defaults, self.bot))

        return generic_reactions

    @commands.Cog.listener()
    async def on_message(self, message):
        if not await self.bot.has_perm(message, dm=False): return
        for generic_reaction in self.generic_reactions:
            await generic_reaction.try_react(message, self.bot.cursor)

    async def rename_on_im(self, server, message):
        im_response = re.match(r"i[']?(?:m| am) ?(.{1,32})(?:$|[ ,.!])", message.content, flags=re.IGNORECASE)
        if server and im_response:
            name = im_response.group(1).strip()
            try:
                await message.author.edit(reason="They said \"I'm\" and that must be punished.", nick=name)
            except discord.errors.Forbidden:
                pass


@dataclass
class GenericReaction:
    bot: commands.Bot = None
    regex: str = ""
    reaction_chance: float = 0
    repeat_delay: int = 0
    reactions: List[str] = None
    reaction_id: int = 0
    remove_reaction_chance: float = 0.3
    remove_reaction_delay: float = 1
    max_reactions_before_cooldown: int = 3
    max_reactions_cooldown: int = 60 * 60 * 12

    async def try_react(self, message: discord.Message, cursor):
        cursor.execute(
            f"SELECT rowid, * FROM react_timer WHERE reaction_id={self.reaction_id} AND guild={message.guild.id}")
        db_entry = cursor.fetchone()
        current_time = int(time.time())
        if db_entry:
            time_since_last_reaction = current_time - db_entry["last_react"]
            if time_since_last_reaction <= self.repeat_delay:
                return False
            if db_entry["reactions_today"] >= self.max_reactions_before_cooldown and time_since_last_reaction <= self.max_reactions_cooldown:
                return False
        if not re.match(self.regex, message.content.lower()):
            return False
        if random.random() > self.reaction_chance:
            return False

        reaction = random.choice(self.reactions)
        await message.add_reaction(reaction)
        react_chain = 1
        if db_entry:
            time_since_last_reaction = current_time - db_entry["last_react"]
            if time_since_last_reaction <= self.max_reactions_before_cooldown:
                react_chain = db_entry["reactions_today"] + 1
            cursor.execute(f"UPDATE react_timer"
                           f"SET last_react={current_time}, reactions_today={react_chain}"
                           f"WHERE rowid={db_entry['rowid']}")
        else:
            cursor.execute(f"INSERT INTO react_timer VALUES(?,?,?,?)",
                                    (message.guild.id, self.reaction_id, current_time, react_chain))
        cursor.execute("commit")

        if random.random() > self.remove_reaction_chance:
            return True
        await asyncio.sleep(self.remove_reaction_delay)
        await message.remove_reaction(reaction, self.bot.user)
        return True

    @staticmethod
    def create_from_data(data: dict, default: dict, bot) -> 'GenericReaction':
        gr = GenericReaction()
        gr.bot = bot
        gr.regex = data.get("regex", default["regex"])
        gr.reaction_chance = data.get("reaction_chance", default["reaction_chance"])
        gr.repeat_delay = data.get("repeat_delay", default["repeat_delay"])
        gr.reaction_chance = float(data.get("reaction_chance", default["reaction_chance"]))
        gr.reactions = data.get("reactions", default["reactions"])
        gr.reaction_id = data["reaction_id"] if "reaction_id" in data else hash(data["reaction_hash"])
        gr.remove_reaction_chance = float(data.get("remove_reaction_chance", default["remove_reaction_chance"]))
        gr.remove_reaction_delay = data.get("remove_reaction_delay", default["remove_reaction_delay"])
        gr.max_reactions_before_cooldown = data.get("max_reactions_before_cooldown", default["max_reactions_before_cooldown"])
        gr.max_reactions_cooldown = data.get("max_reactions_cooldown", default["max_reactions_cooldown"])
        return gr



async def setup(bot):
    #bot.core_help_text["modules"] += ["react"]
    await bot.add_cog(Reaction(bot))
