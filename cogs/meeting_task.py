import discord
from discord.ext import commands, tasks
from utils.meeting import Meeting
from pymongo import MongoClient
from bot import MyBot
from bson.objectid import ObjectId
import asyncio
import datetime
import pytz

class Meeting_task(commands.Cog):
    def __init__(self, bot: MyBot):
        self.bot = bot
        self.mongo_client:MongoClient  = bot.mongo_client
    
    async def get_meeting_info(self, meeting_doc, server_setting_doc):
        _id = ObjectId(meeting_doc["_id"])
        guild_id = meeting_doc["guild_id"]
        guild = self.bot.get_guild(guild_id)
        participate_role_id = meeting_doc["participate_role_id"]
        title = meeting_doc["title"]
        timezone = server_setting_doc["timezone"]
        start_timestamp_UTC = meeting_doc["start_timestamp_UTC"]         
        meeting = Meeting(self.bot, _id, guild, title, start_timestamp_UTC, timezone, participate_role_id)
        return meeting
        
    @commands.Cog.listener()
    async def on_ready(self):
        print("MeetingTask cog loaded.")
        # load or start meeting from database
        meeting_coll  = self.mongo_client.meeting.meeting
        server_setting_coll = self.mongo_client.meeting.server_setting
        meeting_wait_load_or_start = []

        for meeting_doc in meeting_coll.find():
            server_setting_doc = server_setting_coll.find_one({"guild_id": meeting_doc["guild_id"]})
            meeting = await self.get_meeting_info(meeting_doc, server_setting_doc)
            meeting_wait_load_or_start.append(meeting.load_meeting())

            start_timestamp_UTC = meeting_doc["start_timestamp_UTC"]
            now_timestamp_UTC = int(datetime.datetime.now(datetime.timezone.utc).replace(second=0, microsecond=0).timestamp())
            if start_timestamp_UTC <= now_timestamp_UTC and meeting_doc["status"] == "pending":
                meeting_wait_load_or_start.append(meeting.start_meeting())
        await asyncio.gather(*meeting_wait_load_or_start)

        # call start check loop
        self.Start_End_loop.start()

    # start check loop
    @tasks.loop(seconds=1)
    async def Start_End_loop(self):
        now_time_UTC = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
        if now_time_UTC.second == 0:
            auto_start_end_wait = []
            auto_start_end_wait.append(self.AutoStart())
            auto_start_end_wait.append(self.AutoEnd())
            await asyncio.gather(*auto_start_end_wait)

    
    # start check loop
    async def AutoStart(self):
        now_time_UTC = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
        now_timestamp_UTC = now_time_UTC.timestamp()
        meeting_coll = self.mongo_client.meeting.meeting
        server_setting_coll = self.mongo_client.meeting.server_setting
        meeting_wait_start = []
        
        for meeting_doc in meeting_coll.find({"start_timestamp_UTC": int(now_timestamp_UTC), "status": "pending"}):
            server_setting_doc = server_setting_coll.find_one({"guild_id": meeting_doc["guild_id"]})
            meeting = await self.get_meeting_info(meeting_doc, server_setting_doc)
            meeting_wait_start.append(meeting.start_meeting())
        await asyncio.gather(*meeting_wait_start)

    # auto end loop
    async def AutoEnd(self):
        meeting_coll  = self.mongo_client.meeting.meeting
        server_setting_coll = self.mongo_client.meeting.server_setting
        meeting_wait_end = []

        for meeting_doc in meeting_coll.find({"status": "in_progress"}):
            voice_channel = self.bot.get_channel(meeting_doc["voice_channel_id"])
            idle_time = meeting_doc["idle_time"]

            if len(voice_channel.members) == 0:
                idle_time += 1
                meeting_coll.update_one({"_id": meeting_doc["_id"]}, {"$set": {"idle_time": idle_time}})
            else:
                return
            
            if idle_time >= 10:
                meeting_coll.update_one({"_id": meeting_doc["_id"]}, {"$set": {"status": "finished"}})
                server_setting_doc = server_setting_coll.find_one({"guild_id": meeting_doc["guild_id"]})
                meeting = await self.get_meeting_info(meeting_doc, server_setting_doc)
                meeting_wait_end.append(meeting.button2.callback())
        await asyncio.gather(*meeting_wait_end)


async def setup(bot):
    await bot.add_cog(Meeting_task(bot))