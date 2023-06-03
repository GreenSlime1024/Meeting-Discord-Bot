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
from bot import MyBot
import pymongo


class MeetingCommand(commands.Cog):
    def __init__(self, bot: MyBot):
        self.bot = bot
        self.mongo_client = bot.mongo_client
        self.settings_db = bot.settings_db
        self.server_settings_coll = bot.server_settings_coll
        
    # discord create meeting command
    @app_commands.command(name="create_meeting", description="create a meeting")
    @app_commands.describe(title="title of the meeting", hour="hour that meeting will starts at (24-hour)", minute="minute that meeting will starts at", day="day that meeting will starts at", month="month that meeting will starts at", year="year that meeting will starts at", role="members of the role that are asked to join the meeting")
    async def create_meeting(self, interaction: discord.Interaction, title: str, hour: int, minute: int, role: discord.Role = None, day: int = None, month: int = None, year: int = None):

        # check if the user has set guild settings
        server_settings = self.server_settings_coll.find_one({"guild_id": interaction.guild.id})
        if server_settings == None:
            await error.error_message(interaction, error="guild settings not set", description="Please set guild settings first.")
            return
        timezone = server_settings["timezone"]
        
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
    
    @app_commands.command(name="set_server_settings", description="set server settings")
    @app_commands.describe(timezone="choose your timezone")
    @app_commands.choices(timezone=[
        discord.app_commands.Choice(name="GMT+0", value="Etc/GMT-0"),
        discord.app_commands.Choice(name="GMT+1", value="Etc/GMT-1"),
        discord.app_commands.Choice(name="GMT+2", value="Etc/GMT-2"),
        discord.app_commands.Choice(name="GMT+3", value="Etc/GMT-3"),
        discord.app_commands.Choice(name="GMT+4", value="Etc/GMT-4"),
        discord.app_commands.Choice(name="GMT+5", value="Etc/GMT-5"),
        discord.app_commands.Choice(name="GMT+6", value="Etc/GMT-6"),
        discord.app_commands.Choice(name="GMT+7", value="Etc/GMT-7"),
        discord.app_commands.Choice(name="GMT+8", value="Etc/GMT-8"),
        discord.app_commands.Choice(name="GMT+9", value="Etc/GMT-9"),
        discord.app_commands.Choice(name="GMT+10", value="Etc/GMT-10"),
        discord.app_commands.Choice(name="GMT+11", value="Etc/GMT-11"),
        discord.app_commands.Choice(name="GMT+12", value="Etc/GMT-12"),
        discord.app_commands.Choice(name="GMT-11", value="Etc/GMT+11"),
        discord.app_commands.Choice(name="GMT-10", value="Etc/GMT+10"),
        discord.app_commands.Choice(name="GMT-9", value="Etc/GMT+9"),
        discord.app_commands.Choice(name="GMT-8", value="Etc/GMT+8"),
        discord.app_commands.Choice(name="GMT-7", value="Etc/GMT+7"),
        discord.app_commands.Choice(name="GMT-6", value="Etc/GMT+6"),
        discord.app_commands.Choice(name="GMT-5", value="Etc/GMT+5"),
        discord.app_commands.Choice(name="GMT-4", value="Etc/GMT+4"),
        discord.app_commands.Choice(name="GMT-3", value="Etc/GMT+3"),
        discord.app_commands.Choice(name="GMT-2", value="Etc/GMT+2"),
        discord.app_commands.Choice(name="GMT-1", value="Etc/GMT+1"),
    ])
    
    async def set_server_settings(self, interaction: discord.Interaction, timezone: discord.app_commands.Choice[str], category: discord.CategoryChannel):
        server_settings = {
                "guild_id": interaction.guild.id,
                "timezone": timezone.value,
                "category_ID": category.id
            }
        if self.server_settings_coll.find_one({"guild_id": interaction.guild.id}) == None:
            self.server_settings_coll.insert_one(server_settings)
        else:
            self.server_settings_coll.update_one({"guild_id": interaction.guild.id}, {"$set": server_settings})
        await interaction.response.send_message(f"guild info set.", ephemeral=False)


    @app_commands.command(name="test", description="test")
    @commands.is_owner()
    async def test(self, interaction: discord.Interaction):
        print(self.mongo_client.list_database_names())
        await interaction.response.send_message("test", ephemeral=True)

async def setup(bot):
    await bot.add_cog(MeetingCommand(bot))
