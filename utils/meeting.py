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
    def __init__(self, bot: MyBot, _id:ObjectId, guild:discord.Guild, title: str, meeting_timestamp_UTC, timezone:str, participate_role: discord.Role = None):
        self.bot = bot
        self._id = _id
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
            meeting_doc = meeting_coll.find_one({"_id": self._id})

        async def archive(interaction: discord.Interaction):
            pass

        # create buttons
        self.button1 = Button(label="roll call", style=discord.ButtonStyle.blurple, disabled=True, emoji="📝")
        self.button2 = Button(label="archive", style=discord.ButtonStyle.grey, disabled=True, emoji="📩")

        # button callback
        self.button1.callback = roll_call
        
        self.view = View(timeout=604800)
        self.view.add_item(self.button1)
        self.view.add_item(self.button2)

        # create embed
        self.embed = discord.Embed(title="Meeting Info", color=discord.Color.yellow())
        self.embed.add_field(name="title", value=self.title, inline=False)
        self.embed.add_field(name="start time", value=f"<t:{int(self.meeting_timestamp_local)}:F> <t:{int(self.meeting_timestamp_local)}:R>", inline=False)
        if self.participate_role_id == None:
            self.embed.add_field(name="participate role", value="@everyone", inline=False)
        else:
            self.embed.add_field(name="participate role", value=self.participate_role.mention, inline=False)

    # this function is called when the bot reboot
    async  def load_meeting(self):
        meeting_coll = self.mongo_client.meeting.meeting
        meeting_doc = meeting_coll.find_one({"_id": self._id})
        thread_message_id = meeting_doc["thread_message_id"]
        thread_id = meeting_doc["thread_id"]
        thread = await self.bot.fetch_channel(thread_id)
        thread_message = await thread.fetch_message(thread_message_id)
        view = View
        view = view.from_message(thread_message, timeout=604800)
        view.children[0].callback = self.button1.callback
        await thread_message.edit(view=view)
        print(f"meeting {self._id} loaded")
        
    async def create_meeting(self):
        # get server settings
        server_setting_coll = self.mongo_client.meeting.server_setting
        server_setting_doc = server_setting_coll.find_one({"guild_id": self.guild.id})
        forum_channel_id = server_setting_doc["forum_channel_id"]
        forum_channel = self.bot.get_channel(forum_channel_id)
        forum_tags_id = server_setting_doc["forum_tags_id"]
        pending_tag_id = forum_tags_id["pending"]
        pending_tag = forum_channel.get_tag(pending_tag_id)
        thread, thread_message = await forum_channel.create_thread(name=self.title, view=self.view, embed=self.embed, content="Meeting log will be sent here.", auto_archive_duration=1440, applied_tags=[pending_tag])
        await thread_message.pin()
        embed = self.embed
        embed.add_field(name="meeting thread", value=thread.mention, inline=False)

        # save the meeting data
        meeting_doc = {
            "_id": self._id,
            "status": "pending",
            "guild_id": self.guild.id,
            "title": self.title,
            "thread_message_id": thread_message.id,
            "thread_id": thread.id,
            "participate_role_id": self.participate_role_id,
            "meeting_timestamp_UTC": int(self.meeting_time_UTC.timestamp()),
            }
        self.meeting_coll = self.mongo_client.meeting.meeting
        self.meeting_coll.insert_one(meeting_doc)
        self.embed.set_footer(text=f"meeting id: {self._id}")
        await thread_message.edit(embed=self.embed)
        return embed

    async def start_meeting(self):
        meeting_coll = self.mongo_client.meeting.meeting
        meeting_doc = meeting_coll.find_one({"_id": self._id})
        server_setting_coll = self.mongo_client.meeting.server_setting
        server_setting_doc = server_setting_coll.find_one({"guild_id": self.guild.id})
        thread_message_id = meeting_doc["thread_message_id"]
        thread_id = meeting_doc["thread_id"]
        thread = await self.bot.fetch_channel(thread_id)
        thread_message = await thread.fetch_message(thread_message_id)
        category_id = server_setting_doc["category_id"]
        category = self.bot.get_channel(category_id)
        voice_channel = await self.guild.create_voice_channel(name=self.title, category=category)
        view = View
        view = view.from_message(thread_message, timeout=604800)
        view.children[0].disabled = False
        view.children[1].disabled = False
        embed = self.embed
        embed.color = discord.Color.green()
        embed.add_field(name="voice channel", value=voice_channel.mention, inline=False)
        server_setting_coll = self.mongo_client.meeting.server_setting
        forum_tags_id = server_setting_doc["forum_tags_id"]
        in_progress_tag_id = forum_tags_id["in_progress"]
        forum_channel_id: discord.ForumChannel = server_setting_doc["forum_channel_id"]
        forum_channel = self.bot.get_channel(forum_channel_id)
        in_progress_tag = forum_channel.get_tag(in_progress_tag_id)
        await thread.edit(applied_tags =[in_progress_tag])
        await thread_message.edit(view=view, embed=embed)
        print(f"meeting {self._id} started")
        meeting_coll.update_one({"_id": self._id}, {"$set": {"status": "in_progress", "voice_channel_id": voice_channel.id}})
