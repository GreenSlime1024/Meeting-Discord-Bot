import discord
from discord.ext import commands
from pymongo import MongoClient
from utils.error import error
from discord.ui import Button, View
import json
import asyncio
import datetime
import pytz
import os
import uuid
from bot import MyBot
from bson.objectid import ObjectId

class Meeting():
    def __init__(self, bot: MyBot, guild:discord.Guild, title: str, year: int, month: int, day: int, hour: int, minute: int, timezone:str, participate_role: discord.Role = None):
        self.bot = bot
        self.mongo_client:MongoClient  = bot.mongo_client
        self.guild = guild
        self.guild_id = guild.id
        self.title = title
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.participate_role = participate_role
        self.timezone = timezone
        self.now_time_UTC = datetime.datetime.now(datetime.timezone.utc).replace(second=0, microsecond=0)
        self.now_time_local = self.now_time_UTC.astimezone(pytz.timezone(self.timezone))
        
        self.meeting_time_local = pytz.timezone(self.timezone).localize(datetime.datetime(self.year, self.month, self.day, self.hour, self.minute))
        self.meeting_time_UTC = self.meeting_time_local.astimezone(pytz.utc)
        if self.participate_role == None:
            self.participate_role_id = None
        else:
            self.participate_role_id = self.participate_role.id
        self.timestamp_local = int(self.meeting_time_local.timestamp())
        self.timestamp_UTC = int(self.meeting_time_UTC.timestamp())

        async def test(interaction: discord.Interaction):
            await interaction.response.send_message("test")

        # create buttons
        self.button1 = Button(label="cancel", style=discord.ButtonStyle.red)
        self.button2 = Button(label="close", style=discord.ButtonStyle.red, disabled=True)
        self.button3 = Button(label="roll call", style=discord.ButtonStyle.blurple, disabled=True)

        # button callback
        self.button1.callback = test
        
        self.view = View(timeout=604800)
        self.view.add_item(self.button1)
        self.view.add_item(self.button2)
        self.view.add_item(self.button3)

    # this function is called when the bot reboot
    async  def load_meeting(self, _id: ObjectId):
        meeting_coll = self.mongo_client.meeting.meeting
        meeting_doc = meeting_coll.find_one({"_id": _id})
        thread_message_id = meeting_doc["thread_message_id"]
        thread_id = meeting_doc["thread_id"]
        thread = await self.bot.fetch_channel(thread_id)
        thread_message = await thread.fetch_message(thread_message_id)
        view = View
        view = view.from_message(thread_message, timeout=604800)
        view.children[0].callback = self.button1.callback
        await thread_message.edit(view=view)
        print(f"meeting {_id} loaded")
        
    async def create_meeting(self):
        # create embed
        self.embed = discord.Embed(title="Meeting Info", color=discord.Color.yellow())
        self.embed.add_field(name="title", value=self.title, inline=False)
        self.embed.add_field(name="start time", value=f"<t:{self.timestamp_local}:F> <t:{self.timestamp_local}:R>", inline=False)
        if self.participate_role_id == None:
            self.embed.add_field(name="participate role", value="@everyone", inline=False)
        else:
            self.embed.add_field(name="participate role", value=self.participate_role.mention, inline=False)
        
        # get server settings
        server_setting_coll = self.mongo_client.meeting.server_setting
        server_setting_doc = server_setting_coll.find_one({"guild_id": self.guild_id})
        self.forum_channel_id = server_setting_doc["forum_channel_id"]
        self.meeting_forum_channel = self.bot.get_channel(self.forum_channel_id)
        self.forum_tags_id = server_setting_doc["forum_tags_id"]
        self.pending_tag_id = self.forum_tags_id["pending"]
        self.pending_tag = self.meeting_forum_channel.get_tag(self.pending_tag_id)
        result = await self.meeting_forum_channel.create_thread(name=self.title, view=self.view, embed=self.embed, content="Meeting log will be sent here.", auto_archive_duration=1440, applied_tags=[self.pending_tag])
        self.thread_message = result[1]
        await self.thread_message.pin()
        self.thread:discord.Thread = result[0]
        self.thread_id = self.thread.id
        self.embed.add_field(name="meeting thread", value=self.thread.mention, inline=False)
        

        # save the meeting data
        meeting_doc = {
            "guild_id": self.guild_id,
            "title": self.title,
            "thread_message_id": self.thread_message.id,
            "thread_id": self.thread_id,
            "participate_role_id": self.participate_role_id,
            "start_time": {
                "year": self.year,
                "month": self.month,
                "day": self.day,
                "hour": self.hour,
                "minute": self.minute,
            }
        }
        self.meeting_coll = self.mongo_client.meeting.meeting
        result = self.meeting_coll.insert_one(meeting_doc)
        _id = result.inserted_id
        self.embed.set_footer(text=f"meeting id: {_id}")
        await self.thread_message.edit(embed=self.embed)
        return self.embed

    async def start_meeting(self):
        pass
