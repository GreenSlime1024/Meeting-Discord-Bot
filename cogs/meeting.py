import discord
from discord.ext import commands
from discord.ext import tasks
from discord import app_commands
import json
import datetime
import pytz
import os
from utils.error import error
import uuid
import asyncio
from discord.ui import Button, Select, View
from utils.meeting import Meeting


class MeetingCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # discord create meeting command
    @app_commands.command(name="create_meeting", description="create a meeting")
    @app_commands.describe(title="title of the meeting", hour="hour that meeting will starts at (24-hour)", minute="minute that meeting will starts at", day="day that meeting will starts at", month="month that meeting will starts at", year="year that meeting will starts at", role="members of the role that are asked to join the meeting")
    async def create_meeting(self, interaction: discord.Interaction, title: str, hour: int, minute: int, role: discord.Role = None, day: int = None, month: int = None, year: int = None):

    # check if the user has set guild settings
        with open("guilds_info.json", mode="r", encoding="utf8") as jfile:
            jdata = json.load(jfile)
        guild_ID = interaction.guild.id
        try:
            timezone: str = jdata[str(guild_ID)]["timezone"]
        except KeyError:
            await error.error_message(interaction, error="guild setting not found", description="You haven't set server settings.\nPlease use </set_server_settings:1072440724118847554> to set.")
            return 
        
        # auto fill the time if user didn't type
        now_time_UTC = datetime.datetime.now(datetime.timezone.utc).replace(second=0, microsecond=0)
        guild_time = now_time_UTC.astimezone(pytz.timezone(timezone))
        if day == None:
            day = guild_time.day
        if month == None:
            month = guild_time.month
        if year == None:
            year = guild_time.year
        
        # check if the time user typed is correct
        try:
            meeting_time = pytz.timezone(timezone).localize(datetime.datetime(year, month, day, hour, minute))
        except ValueError as e:
            await error.error_message(interaction, error=e, description="Please check if the time you typed is correct.")
        meeting_time_UTC = meeting_time.astimezone(pytz.utc)
        
        now_time_UTC = datetime.datetime.now(datetime.timezone.utc).replace(second=0, microsecond=0)
        if meeting_time_UTC <= now_time_UTC:
            await error.error_message(interaction, error="time had expired")
            return 
        
        # check if the channel type is correct
        if interaction.channel.type != discord.ChannelType.text:
            await error.error_message(interaction, error="channel type error", description="Please use this command in a text channel.")
            return 
        # check if the user has the permission to create meeting
        # pass

        # instantiate meeting class
        meeting = Meeting(self.bot, interaction, title, hour, minute, timezone, role, day, month, year)
        # create meeting
        await meeting.create_meeting()

async def setup(bot):
    await bot.add_cog(MeetingCommand(bot))
