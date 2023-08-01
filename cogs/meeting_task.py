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
    
    # the function to get meeting info from database and return meeting object
    async def get_meeting_info(self, meeting_doc, server_setting_doc):
        _id = ObjectId(meeting_doc["_id"])
        guild_id = meeting_doc["guild_id"]
        guild = self.bot.get_guild(guild_id)
        participate_role_id = meeting_doc["participate_role_id"]
        participate_role = guild.get_role(participate_role_id)
        title = meeting_doc["title"]
        timezone = server_setting_doc["timezone"]
        start_timestamp_UTC = meeting_doc["start_timestamp_UTC"]         
        meeting = Meeting(self.bot, _id, guild, title, start_timestamp_UTC, timezone, participate_role)
        return meeting
        
    @commands.Cog.listener()
    async def on_ready(self):
        print("MeetingTask cog loaded.")
        # get meeting info from database
        meeting_coll  = self.mongo_client.meeting.meeting
        server_setting_coll = self.mongo_client.meeting.server_setting
        meeting_wait_load_or_start = []

        # find meeting that status is pending or in progress
        for meeting_doc in meeting_coll.find({"status": {"$in": ["pending", "in_progress"]}}):
            # get server setting
            server_setting_doc = server_setting_coll.find_one({"guild_id": meeting_doc["guild_id"]})
            # get meeting object
            meeting = await self.get_meeting_info(meeting_doc, server_setting_doc)
            # if status is in_progress, load meeting
            if meeting_doc["status"] == "in_progress":
                meeting_wait_load_or_start.append(meeting.load_meeting())

            # if status is pending and start time is now or past, start meeting
            start_timestamp_UTC = meeting_doc["start_timestamp_UTC"]
            now_timestamp_UTC = int(datetime.datetime.now(datetime.timezone.utc).replace(second=0, microsecond=0).timestamp())
            if start_timestamp_UTC <= now_timestamp_UTC and meeting_doc["status"] == "pending":
                meeting_wait_load_or_start.append(meeting.start_meeting())
        await asyncio.gather(*meeting_wait_load_or_start)

        # call start check loop
        self.auto_start_end.start()
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member:discord.member, before:discord.VoiceState, after:discord.VoiceState):
        meeting_coll = self.mongo_client.meeting.meeting
        server_setting_coll = self.mongo_client.meeting.server_setting

        if before.channel is None and after.channel is None:
            return
        if (before.channel != None and after.channel != None) and (before.channel.id == after.channel.id):
            return

        # Check if the member joined a voice channel
        if after.channel is not None:
            print(f"{member.display_name} joined {after.channel.name}.")
            # get meeting info from database
            meeting_doc = meeting_coll.find_one({"voice_channel_id": after.channel.id})
            action = "join"
            # get server setting
            server_setting_doc = server_setting_coll.find_one({"guild_id": meeting_doc["guild_id"]})
            # get meeting object
            meeting = await self.get_meeting_info(meeting_doc, server_setting_doc)
            await meeting.join_leave_log(member, action)
    
        # Check if the member left a voice channel
        if before.channel is not None:
            print(f"{member.display_name} left {before.channel.name}.")
            meeting_doc = meeting_coll.find_one({"voice_channel_id": before.channel.id})
            action = "leave"
            # get server setting
            server_setting_doc = server_setting_coll.find_one({"guild_id": meeting_doc["guild_id"]})
            # get meeting object
            meeting = await self.get_meeting_info(meeting_doc, server_setting_doc)
            await meeting.join_leave_log(member, action)

    # check the time every second
    @tasks.loop(seconds=1)
    async def auto_start_end(self):
        now_time_UTC = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
        if now_time_UTC.second == 0: # if the time's second is 0, call auto_start and auto_end function
            auto_start_end_wait = []
            auto_start_end_wait.append(self.auto_start())
            auto_start_end_wait.append(self.auto_end())
            await asyncio.gather(*auto_start_end_wait)

    async def auto_start(self):
        # get meeting info from database
        meeting_coll = self.mongo_client.meeting.meeting
        server_setting_coll = self.mongo_client.meeting.server_setting
        # get now timestamp UTC
        now_time_UTC = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
        now_timestamp_UTC = now_time_UTC.timestamp()
        meeting_wait_start = []
        
        # find meeting that status is pending and start time is now
        for meeting_doc in meeting_coll.find({"start_timestamp_UTC": int(now_timestamp_UTC), "status": "pending"}):
            # get server setting
            server_setting_doc = server_setting_coll.find_one({"guild_id": meeting_doc["guild_id"]})
            # get meeting object
            meeting = await self.get_meeting_info(meeting_doc, server_setting_doc)
            # start meeting
            meeting_wait_start.append(meeting.start_meeting())
        await asyncio.gather(*meeting_wait_start)

    async def auto_end(self):
        # get meeting info from database
        meeting_coll  = self.mongo_client.meeting.meeting
        server_setting_coll = self.mongo_client.meeting.server_setting
        meeting_wait_end = []

        # find meeting that status is in_progress
        for meeting_doc in meeting_coll.find({"status": "in_progress"}):
            voice_channel = self.bot.get_channel(meeting_doc["voice_channel_id"])
            idle_time = meeting_doc["idle_time"]

            # if voice channel is empty, idle time +=1
            if len(voice_channel.members) == 0:
                idle_time += 1
                # update idle time
                meeting_coll.update_one({"_id": meeting_doc["_id"]}, {"$set": {"idle_time": idle_time}})
            
            # if idle time is 10 or over, end meeting
            if idle_time >= 10:
                meeting_coll.update_one({"_id": meeting_doc["_id"]}, {"$set": {"status": "finished"}})
                server_setting_doc = server_setting_coll.find_one({"guild_id": meeting_doc["guild_id"]})
                meeting = await self.get_meeting_info(meeting_doc, server_setting_doc)
                meeting_wait_end.append(meeting.button2.callback())
        await asyncio.gather(*meeting_wait_end)


async def setup(bot):
    await bot.add_cog(Meeting_task(bot))