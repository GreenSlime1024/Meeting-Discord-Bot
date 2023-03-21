import discord
from discord.ext import commands
from discord.ext import tasks
from core.classes import Cog_Extension
import datetime
import json
import asyncio
import pytz
import os


class MeetingTask(Cog_Extension):
    @commands.Cog.listener()
    async def on_ready(self):
        print("meeting_task cog loaded.")

    def __init__(self, bot):
        super().__init__(bot)
        self.StartCheck.start()

    @tasks.loop(seconds=1)
    async def StartCheck(self):
        now_time_UTC = datetime.datetime.now(datetime.timezone.utc).replace(second=0, microsecond=0)
        timestamp_UTC = int(now_time_UTC.timestamp())
        with open("meeting.json", mode="r", encoding="utf8") as jfile:
            jdata = json.load(jfile)

        if str(timestamp_UTC) not in jdata:
            return
        
        # open meeting
        for data in jdata[str(timestamp_UTC)]:
            if data["status"] == True:
                index = jdata[str(timestamp_UTC)].index(data)
                # meeting_ID = data["meeting_ID"]
                guild_ID = data["guild_ID"]
                title = data["title"]
                # text_channel_ID = data["text_channel_ID"]
                # message_ID = data["message_ID"]
                # thread_ID = data["thread_ID"]
                # role_ID = data["role_ID"]
                # start_time = data["start_time"]
                guild = self.bot.get_guild(guild_ID)
                
                with open("guilds_info.json", mode="r", encoding="utf8") as jfile:
                    guilds_info_data = json.load(jfile)
                category_ID = guilds_info_data[str(guild_ID)]["category_ID"]
                category = self.bot.get_channel(category_ID)
                voice_channel = await guild.create_voice_channel(name=title, category=category)
                voice_channel_ID = voice_channel.id
                message_ID = data["message_ID"]
                text_channel_ID = data["text_channel_ID"]
                text_channel = self.bot.get_channel(text_channel_ID)
                message = await text_channel.fetch_message(message_ID)
                message.embeds[0].add_field(name="Voice Channel", value=f"<#{voice_channel_ID}>")
                message.embeds[0].color = discord.Color.green()
                await message.edit(embed=message.embeds[0])
                data["status"] = False
                data["voice_channel_ID"] = voice_channel_ID
                
                jdata[str(timestamp_UTC)][index] = data
                with open("meeting.json", mode="w", encoding="utf8") as jfile:
                    json.dump(jdata, jfile, indent=4)

async def setup(bot):
    await bot.add_cog(MeetingTask(bot))
    