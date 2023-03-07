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
        with open("before_meeting.json", mode="r", encoding="utf8") as jfile:
            jdata = json.load(jfile)

        for i in jdata.keys():
            with open("before_meeting.json", mode="r", encoding="utf8") as jfile:
                jdata = json.load(jfile)
        
            guild_ID = jdata[i]["guild_ID"]
            with open("guilds_info.json", mode="r", encoding="utf8") as jfile:
                jdata = json.load(jfile)
            timezone = jdata[str(guild_ID)]["timezone"]

            with open("before_meeting.json", mode="r", encoding="utf8") as jfile:
                jdata = json.load(jfile)

            year, month, day, hour, minute = jdata[i]["start_time"]

            now_time_UTC = datetime.datetime.now(datetime.timezone.utc).replace(second=0, microsecond=0)
            meeting_time = pytz.timezone(timezone).localize(datetime.datetime(year, month, day, hour, minute))
            meeting_time_UTC = meeting_time.astimezone(pytz.utc)

            if meeting_time_UTC == now_time_UTC:
                meeting_data = jdata[i]

                with open("durning_meeting.json", mode="r", encoding="utf8") as jfile:
                    jdata = json.load(jfile)
                jdata[i] = meeting_data
                with open("durning_meeting.json", mode="w", encoding="utf8") as jfile:
                    json.dump(jdata, jfile, indent=4)

                with open("before_meeting.json", mode="r", encoding="utf8") as jfile:
                    jdata = json.load(jfile)
                del jdata[i]
                with open("before_meeting.json", mode="w", encoding="utf8") as jfile:
                    json.dump(jdata, jfile, indent=4)

async def setup(bot):
    await bot.add_cog(MeetingTask(bot))
