import discord
import math
import random
import re
from discord.ext import commands
import traceback


class Reaction(commands.Cog, name="message_reactions"):
    """Reacts to various chat messages with emotes or messages."""
    prefix = "react"
    
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if not await self.bot.has_perm(message, dm=False): return
        await self.yap_react(message)

    async def rename_on_im(self, server, message):
        im_response = re.match(r"i[']?(?:m| am) ?(.{1,32})(?:$|[ ,.!])", message.content, flags=re.IGNORECASE)
        if server and im_response:
            name = im_response.group(1).strip()
            try:
                await message.author.edit(reason="They said \"I'm\" and that must be punished.", nick=name)
            except discord.errors.Forbidden:
                pass

    async def yap_react(self, message):
        if "yap" not in message.content.lower():
            return
        await message.add_reaction("<yap:1462729662496247922>")


async def setup(bot):
    #bot.core_help_text["modules"] += ["react"]
    await bot.add_cog(Reaction(bot))
