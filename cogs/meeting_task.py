import discord
from discord.ext import commands, tasks
from utils.meeting import Meeting
from bot import MyBot
from bson.objectid import ObjectId
import asyncio
import datetime


class MeetingTask(commands.Cog):
    def __init__(self, bot: MyBot):
        self.bot = bot
        self.server_setting_coll = self.bot.mongo_client["meeting"]["server_setting"]
        self.meeting_coll = self.bot.mongo_client["meeting"]["meeting"]
        
    @commands.Cog.listener()
    async def on_ready(self):
        print("MeetingTask cog loaded.")

        meetings_to_start = []
        async for meeting_doc in self.meeting_coll.find({"status": "pending"}):
            meeting = Meeting(bot=self.bot, _id=ObjectId(meeting_doc["_id"]))
            start_timestamp:int = meeting_doc["start_timestamp"]
            now_timestamp = int(datetime.datetime.now().replace(second=0, microsecond=0).timestamp())
            if start_timestamp <= now_timestamp:
                meetings_to_start.append(meeting.start_meeting())
        await asyncio.gather(*meetings_to_start)

        self.auto_tasks.start()
    
    @tasks.loop(seconds=1)
    async def auto_tasks(self):
        now_time_UTC = datetime.datetime.now().replace(microsecond=0)
        if now_time_UTC.second == 0:
            await asyncio.gather(self.auto_start(), self.auto_end(), self.auto_remind())

    async def auto_start(self):
        now_timestamp = int(datetime.datetime.now().replace(microsecond=0).timestamp())
        meetings_to_start = []
        async for meeting_doc in self.meeting_coll.find({"start_timestamp": now_timestamp, "status": "pending"}):
            meeting = Meeting(bot=self.bot, _id=ObjectId(meeting_doc["_id"]))
            meetings_to_start.append(meeting.start_meeting())
        await asyncio.gather(*meetings_to_start)

    async def auto_end(self):
        meetings_to_end = []
        async for meeting_doc in self.meeting_coll.find({"status": "in_progress"}):
            voice_channel:discord.VoiceChannel = self.bot.get_channel(meeting_doc["voice_channel_id"])
            idle:int = meeting_doc["idle"]

            if len(voice_channel.members) == 0:
                idle += 1
                self.meeting_coll.update_one({"_id": meeting_doc["_id"]}, {"$set": {"idle": idle}})
            
            if idle >= 10:
                self.meeting_coll.update_one({"_id": meeting_doc["_id"]}, {"$set": {"status": "finished"}})
                meeting = Meeting(bot=self.bot, _id=ObjectId(meeting_doc["_id"]))
                meetings_to_end.append(meeting.end_meeting())
        await asyncio.gather(*meetings_to_end)

    async def auto_remind(self):
        meeting_wait_remind = []
        now_timestamp = int(datetime.datetime.now().replace(microsecond=0).timestamp())
        async for meeting_doc in self.meeting_coll.find({"remind_timestamp": now_timestamp, "status": "pending"}):
            meeting = Meeting(bot=self.bot, _id=ObjectId(meeting_doc["_id"]))
            meeting_wait_remind.append(meeting.remind_meeting())
        await asyncio.gather(*meeting_wait_remind)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if before.channel == after.channel:
            return

        if after.channel:
            meeting_doc = await self.meeting_coll.find_one({"voice_channel_id": after.channel.id})
            if meeting_doc:
                meeting = Meeting(bot=self.bot, _id=ObjectId(meeting_doc["_id"]))
                await meeting.join_leave_log(member, "join")
    
        if before.channel:
            meeting_doc = await self.meeting_coll.find_one({"voice_channel_id": before.channel.id})
            if meeting_doc:
                meeting = Meeting(bot=self.bot, _id=ObjectId(meeting_doc["_id"]))
                await meeting.join_leave_log(member, "leave")


async def setup(bot: MyBot):
    await bot.add_cog(MeetingTask(bot))
