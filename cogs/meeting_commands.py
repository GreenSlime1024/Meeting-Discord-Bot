import discord
from discord.ext import commands
from discord.ext import tasks
from discord import app_commands
import json
import datetime
import pytz
import os
from utils.error import error
import asyncio
from discord.ui import Button, Select, View
from utils.meeting import Meeting
from bot import MyBot
import pymongo
from bson import ObjectId


class MeetingCommand(commands.Cog):
    def __init__(self, bot: MyBot):
        self.bot = bot
        self.mongo_client = bot.mongo_client

    @commands.Cog.listener()
    async def on_ready(self):
        print("MeetingCommand cog loaded.")
        
    # discord create meeting command
    @app_commands.command(name="create_meeting", description="create a meeting")
    @app_commands.describe(title="title of the meeting", hour_local="hour that meeting will starts at (24-hour)", minute_local="minute that meeting will starts at", day_local="day that meeting will starts at", month_local="month that meeting will starts at", year_local="year that meeting will starts at", participate_role="members of the role that are asked to join the meeting")
    async def create_meeting(self, interaction: discord.Interaction, title: str, hour_local: int, minute_local: int, participate_role: discord.Role = None, day_local: int = None, month_local: int = None, year_local: int = None):

        # check if the user has set guild settings
        meeting_db = self.mongo_client.meeting
        server_setting_coll = meeting_db.server_setting
        server_setting_doc = server_setting_coll.find_one({"guild_id": interaction.guild.id})
        if server_setting_doc == None:
            await error.error_message(interaction, error="server settings not set", description="Please set server settings first.")
            return
        timezone = server_setting_doc["timezone"]

        # check if the user has the permission to create meeting
        admin_role_id = server_setting_doc["admin_role_id"]
        meeting_admin_role = interaction.guild.get_role(admin_role_id)
        if interaction.user not in meeting_admin_role.members:
            await error.error_message(interaction, error="no permission", description="You don't have the permission to create meeting.")
            return
        
        # auto fill the time if user didn't type
        now_time_UTC = datetime.datetime.now(datetime.timezone.utc).replace(second=0, microsecond=0)
        now_time_local = now_time_UTC.astimezone(pytz.timezone(timezone))
        day_local = day_local or now_time_local.day
        month_local = month_local or now_time_local.month
        year_local = year_local or now_time_local.year
        
        # check if the time user typed is correct
        try:
            meeting_time_local = pytz.timezone(timezone).localize(datetime.datetime(year_local, month_local, day_local, hour_local, minute_local))
        except ValueError as e:
            await error.error_message(interaction, error=e, description="Please check if the time you typed is correct.")
            return
        
        meeting_time_UTC = meeting_time_local.astimezone(pytz.utc)
        now_time_UTC = datetime.datetime.now(datetime.timezone.utc).replace(second=0, microsecond=0)
        if meeting_time_UTC <= now_time_UTC:
            await error.error_message(interaction, error="time had expired")
            return 
        
        # check if the channel type is correct
        if interaction.channel.type != discord.ChannelType.text:
            await error.error_message(interaction, error="channel type error", description="Please use this command in a text channel.")
            return 
        
        # instantiate meeting class
        start_timestamp_UTC = meeting_time_UTC.timestamp()
        _id = ObjectId()
        meeting = Meeting(self.bot, _id, interaction.guild, title, start_timestamp_UTC, timezone, participate_role)
        # create meeting
        embed = await meeting.create_meeting()
        embed.color = discord.Color.blue()
        # send embed
        await interaction.response.send_message(embed=embed)
    
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="set_server_settings", description="set server settings")
    @app_commands.describe(timezone="choose your timezone", meeting_admin_role="choose the role that can control meeting")
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
    
    async def set_server_settings(self, interaction: discord.Interaction, timezone: discord.app_commands.Choice[str], meeting_admin_role: discord.Role):
        server_setting_coll = self.mongo_client.meeting.server_setting
        server_setting_doc = server_setting_coll.find_one({"guild_id": interaction.guild.id})
        async def create_server_setting(edit:bool):
            # create a category for meetings voice_channel and forum
            meeting_category = await interaction.guild.create_category("meeting")
            forum_channel = await meeting_category.create_forum("meeting")
            # create tags for meeting forum
            tag_infos = [["pending", "⏳"], ["in_progress", "🔄"], ["finished", "✅"]]
            tag_ids = {}
            for tag_info in tag_infos:
                tag = await forum_channel.create_tag(name=tag_info[0], emoji=tag_info[1])
                tag_ids[tag_info[0]] = tag.id
                await asyncio.sleep(0.1)
        
            server_setting_doc = {
                    "guild_id": interaction.guild.id,
                    "timezone": timezone.value,                        
                    "category_id": meeting_category.id,
                    "forum_channel_id": forum_channel.id,
                    "forum_tags_id": tag_ids,
                    "admin_role_id": meeting_admin_role.id
                }

            # save server settings to database
            if edit:
                server_setting_coll.update_one({"guild_id": interaction.guild.id}, {"$set": server_setting_doc})
            else:
                server_setting_coll.insert_one(server_setting_doc)
        
            # send message
            embed = discord.Embed(title="Server Settings", color=discord.Color.blue())
            embed.add_field(name="timezone", value=timezone.value, inline=False)
            embed.add_field(name="meeting category", value=meeting_category.mention, inline=False)
            embed.add_field(name="meeting forum channel", value=forum_channel.mention, inline=False)
            embed.add_field(name="meeting admin role", value=meeting_admin_role.mention, inline=False)
            if edit:
                await interaction.edit_original_response(embed=embed, view=None)
            else:
                await interaction.response.send_message(embed=embed)
            
        if server_setting_doc == None:
            await create_server_setting(edit=False)
        else:
            async def confirm(interaction: discord.Interaction):
                meeting_coll = self.mongo_client.meeting.meeting
                meeting_coll.delete_many({"guild_id": interaction.guild.id})
                await create_server_setting(edit=True)

            embed = discord.Embed(title="Are you sure?", description="If you set server settings again, meetings that you created will be deleted.", color=discord.Color.blue())
            view = View()
            button1 = Button(style=discord.ButtonStyle.green, label="confirm")
            button1.callback = confirm
            view.add_item(button1)
            await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(MeetingCommand(bot))
