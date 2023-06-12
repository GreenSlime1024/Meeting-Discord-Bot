import discord
from discord.ext import commands
from utils.error import error
from discord.ui import Button, View
import json
import asyncio
import datetime
import pytz
import os
import uuid
from bot import MyBot

class Meeting():
    def __init__(self, bot: MyBot, interaction: discord.Interaction, title: str, day: int, month: int, year: int, hour: int, minute: int, timezone:str, participate_role: discord.Role = None):
        self.bot = bot
        self.mongo_client = bot.mongo_client
        self.meeting_id = str(uuid.uuid4())
        self.interaction = interaction
        self.guild_id = interaction.guild.id
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

        # create buttons
        self.button1 = Button(label="cancle", style=discord.ButtonStyle.red)
        self.button2 = Button(label="close", style=discord.ButtonStyle.red, disabled=True)
        self.button3 = Button(label="roll call", style=discord.ButtonStyle.blurple, disabled=True)
        self.view = View(timeout=604800)
        self.view.add_item(self.button1)
        self.view.add_item(self.button2)
        self.view.add_item(self.button3)

    

    async def create_meeting(self):
        # create embed
        self.embed = discord.Embed(title=self.title, color=discord.Color.yellow())
        self.embed.add_field(name="start time", value=f"<t:{self.timestamp_local}:F> <t:{self.timestamp_local}:R>", inline=False)
        if self.participate_role_id == None:
            self.embed.add_field(name="participate_role", value="@everyone", inline=False)
        else:
            self.embed.add_field(name="participate_role", value=self.participate_role.mention, inline=False)
        self.embed.set_footer(text=self.meeting_id)
        
        # get server settings
        settings_db = self.mongo_client.settings
        server_settings_coll = settings_db.server_settings
        server_settings_doc = server_settings_coll.find_one({"guild_id": self.guild_id})
        self.meeting_forum_channel_id = server_settings_doc["meeting_forum_channel_id"]
        self.meeting_forum_channel = self.bot.get_channel(self.meeting_forum_channel_id)
        self.meeting_forum_tags_id = server_settings_doc["meeting_forum_tags_id"]
        self.pending_tag_id = self.meeting_forum_tags_id["pending"]
        self.pending_tag = self.meeting_forum_channel.get_tag(self.pending_tag_id)
        self.forum_return = await self.meeting_forum_channel.create_thread(name=self.title, view=self.view, embed=self.embed, auto_archive_duration=1440, applied_tags=[self.pending_tag])
        self.meeting_thread = self.forum_return[0]
        self.meeting_thread_id = self.meeting_thread.id
        self.embed.add_field(name="meeting thread", value=self.meeting_thread.mention, inline=False)
        
        # send meeting message
        await self.interaction.response.send_message(embed=self.embed)

        # save the meeting data
        meeting_doc = {
            "meeting_id": self.meeting_id,
            "guild_id": self.guild_id,
            "title": self.title,
            "meeting_thread_id": self.meeting_thread_id,
            "participate_role_id": self.participate_role_id,
            "start_time": {
                "year": self.year,
                "month": self.month,
                "day": self.day,
                "hour": self.hour,
                "minute": self.minute,
            }
        }
        self.meeting_db = self.mongo_client.meeting
        self.meeting_coll = self.meeting_db.meeting
        self.meeting_coll.insert_one(meeting_doc)

    async def start_meeting(self):
        pass
