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

    @commands.Cog.listener()
    async def on_ready(self):
        print("MeetingCommand cog loaded.")
        
    # discord create meeting command
    @app_commands.command(name="create_meeting", description="create a meeting")
    @app_commands.describe(title="title of the meeting", hour="hour that meeting will starts at (24-hour)", minute="minute that meeting will starts at", day="day that meeting will starts at", month="month that meeting will starts at", year="year that meeting will starts at", participate_role="members of the role that are asked to join the meeting")
    async def create_meeting(self, interaction: discord.Interaction, title: str, hour: int, minute: int, participate_role: discord.Role = None, day: int = None, month: int = None, year: int = None):

        # check if the user has set guild settings
        self.settings_db = self.mongo_client.settings
        self.server_settings_coll = self.settings_db.server_settings
        server_settings = self.server_settings_coll.find_one({"guild_id": interaction.guild.id})
        if server_settings == None:
            await error.error_message(interaction, error="guild settings not set", description="Please set guild settings first.")
            return
        timezone = server_settings["timezone"]
        # check if the user has the permission to create meeting
        meeting_admin_role_id = server_settings["meeting_admin_role_id"]
        meeting_admin_role = interaction.guild.get_role(meeting_admin_role_id)
        if interaction.user not in meeting_admin_role.members:
            await error.error_message(interaction, error="no permission", description="You don't have the permission to create meeting.")
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

        # instantiate meeting class
        meeting = Meeting(self.bot, interaction, title, day, month, year, hour, minute, timezone, participate_role)
        # create meeting
        await meeting.create_meeting()
    
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="set_server_settings", description="set server settings")
    @app_commands.describe(timezone="choose your timezone", meeting_category="choose the category that meeting voice channels will be created in", meeting_forum_channel="choose the forum that meeting control pannel will be created in", meeting_admin_role="choose the role that can control meeting")
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
    
    async def set_server_settings(self, interaction: discord.Interaction, timezone: discord.app_commands.Choice[str], meeting_admin_role: discord.Role, meeting_category:discord.CategoryChannel=None, meeting_forum_channel:discord.ForumChannel=None):
        if meeting_category == None:
            # create a category for meetings voice_channel and forum
            meeting_category = await interaction.guild.create_category("meeting")

        if meeting_admin_role == None:
            # create a role for meeting admin
            meeting_admin_role = await interaction.guild.create_role(name="meeting admin")

        if meeting_forum_channel == None:
            # create a forum channel for meetings
            print(meeting_forum_channel)
            meeting_forum_channel = await interaction.guild.create_forum("meeting", category=meeting_category)
        
        # create tags for meeting forum
        tag_infos = [["pending", "⏳"], ["in progress", "🔄"], ["finished", "✅"]]
        tag_ids = {}
        for tag_info in tag_infos:
            try:
                tag = await meeting_forum_channel.create_tag(name=tag_info[0], emoji=tag_info[1])
                tag_ids[tag_info[0]] = tag.id
            except discord.errors.HTTPException:
                pass

        server_settings_doc = {
                "guild_id": interaction.guild.id,
                "timezone": timezone.value,
                "meeting_category_id": meeting_category.id,
                "meeting_forum_channel_id": meeting_forum_channel.id,
                "meeting_forum_tags_id": tag_ids,
                "meeting_admin_role_id": meeting_admin_role.id
            }

        # save server settings to database
        self.settings_db = self.mongo_client.settings
        self.server_settings_coll = self.settings_db.server_settings
        if self.server_settings_coll.find_one({"guild_id": interaction.guild.id}) == None:
            self.server_settings_coll.insert_one(server_settings_doc)
        else:
            self.server_settings_coll.update_one({"guild_id": interaction.guild.id}, {"$set": server_settings_doc})

        # send message
        embed = discord.Embed(title="Server Settings")
        embed.add_field(name="timezone", value=timezone.value, inline=False)
        embed.add_field(name="meeting category", value=meeting_category.mention, inline=False)
        embed.add_field(name="meeting forum channel", value=meeting_forum_channel.mention, inline=False)
        embed.add_field(name="meeting admin role", value=meeting_admin_role.mention, inline=False)
        await interaction.response.send_message(f"server_settings set.", embed=embed, ephemeral=False)

async def setup(bot):
    await bot.add_cog(MeetingCommand(bot))
