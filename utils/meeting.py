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
    def __init__(self, bot: MyBot, guild:discord.Guild, title: str, meeting_timestamp_UTC, timezone:str, participate_role: discord.Role = None):
        self.bot = bot
        self.mongo_client:MongoClient  = bot.mongo_client
        self.guild = guild
        self.title = title
        self.participate_role = participate_role
        self.timezone = timezone
        self.meeting_timestamp_UTC = meeting_timestamp_UTC
        self.meeting_time_UTC = datetime.datetime.fromtimestamp(meeting_timestamp_UTC, datetime.timezone.utc)
        self.meeting_time_local = self.meeting_time_UTC.astimezone(pytz.timezone(timezone))
        self.meeting_timestamp_local = self.meeting_time_local.timestamp()
        
        if self.participate_role == None:
            self.participate_role_id = None
        else:   
            self.participate_role_id = self.participate_role.id

        async def roll_call(interaction: discord.Interaction):
            absent_members = []
            attend_members = []
            meeting_coll = self.mongo_client.meeting.meeting

        # create buttons
        self.button1 = Button(label="roll call", style=discord.ButtonStyle.blurple, disabled=True, emoji="📝")
        self.button2 = Button(label="archive", style=discord.ButtonStyle.grey, disabled=True, emoji="📩")

        # button callback
        self.button1.callback = roll_call
        
        self.view = View(timeout=604800)
        self.view.add_item(self.button1)
        self.view.add_item(self.button2)

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
        self.embed.add_field(name="start time", value=f"<t:{int(self.meeting_timestamp_local)}:F> <t:{int(self.meeting_timestamp_local)}:R>", inline=False)
        if self.participate_role_id == None:
            self.embed.add_field(name="participate role", value="@everyone", inline=False)
        else:
            self.embed.add_field(name="participate role", value=self.participate_role.mention, inline=False)
        
        # get server settings
        server_setting_coll = self.mongo_client.meeting.server_setting
        server_setting_doc = server_setting_coll.find_one({"guild_id": self.guild.id})
        self.forum_channel_id = server_setting_doc["forum_channel_id"]
        self.meeting_forum_channel = self.bot.get_channel(self.forum_channel_id)
        self.forum_tags_id = server_setting_doc["forum_tags_id"]
        self.pending_tag_id = self.forum_tags_id["pending"]
        self.pending_tag = self.meeting_forum_channel.get_tag(self.pending_tag_id)
        result = await self.meeting_forum_channel.create_thread(name=self.title, view=self.view, embed=self.embed, content="Meeting log will be sent here.", auto_archive_duration=1440, applied_tags=[self.pending_tag])
        self.thread_message = result[1]
        await self.thread_message.pin()
        self.thread:discord.Thread = result[0]
        self.embed.add_field(name="meeting thread", value=self.thread.mention, inline=False)
        

        # save the meeting data
        meeting_doc = {
            "status": "pending",
            "guild_id": self.guild.id,
            "title": self.title,
            "thread_message_id": self.thread_message.id,
            "thread_id": self.thread.id,
            "participate_role_id": self.participate_role_id,
            "meeting_timestamp_UTC": self.meeting_time_UTC.timestamp(),
            }
        self.meeting_coll = self.mongo_client.meeting.meeting
        result = self.meeting_coll.insert_one(meeting_doc)
        _id = result.inserted_id
        self.embed.set_footer(text=f"meeting id: {_id}")
        await self.thread_message.edit(embed=self.embed)
        return self.embed

    async def start_meeting(self, _id: ObjectId):
        meeting_coll = self.mongo_client.meeting.meeting
        meeting_doc = meeting_coll.find_one({"_id": _id})
        self.thread_message_id = meeting_doc["thread_message_id"]
        self.thread_id = meeting_doc["thread_id"]
        self.thread = await self.bot.fetch_channel(self.thread_id)
        self.thread_message = await self.thread.fetch_message(self.thread_message_id)
        self.view = View
        self.view = self.view.from_message(self.thread_message, timeout=604800)
        self.view.children[0].disabled = False
        self.view.children[1].disabled = False
        await self.thread_message.edit(view=self.view)
        await self.thread.send("Meeting started.")
        print(f"meeting {_id} started")
        meeting_coll.update_one({"_id": _id}, {"$set": {"status": "started"}})
