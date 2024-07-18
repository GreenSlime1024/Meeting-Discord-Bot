import discord
from discord.ext import commands
from discord import app_commands
import datetime
import pytz
from utils.meeting import Meeting
from bot import MyBot
from bson import ObjectId
from typing import Union


class MeetingCommands(commands.Cog):
    def __init__(self, bot: MyBot):
        self.bot = bot
        self.server_setting_coll = self.bot.mongo_client["meeting"]["server_setting"]
        self.meeting_coll = self.bot.mongo_client["meeting"]["meeting"]

    @commands.Cog.listener()
    async def on_ready(self):
        print("MeetingCommands cog loaded.")
        
    # discord create meeting command
    @app_commands.command(name="create_meeting", description="create a meeting")
    @app_commands.choices(
        remind_time_ago=[
            app_commands.Choice(name="1 minute ago", value=1),
            app_commands.Choice(name="5 minutes ago", value=5),
            app_commands.Choice(name="10 minutes ago", value=10),
            app_commands.Choice(name="15 minutes ago", value=15),
            app_commands.Choice(name="30 minutes ago", value=30),
            app_commands.Choice(name="1 hour ago", value=60),
        ]
    )
    @app_commands.describe(title="title of the meeting", hour_local="hour that meeting will starts at (24-hour)", minute_local="minute that meeting will starts at (24-hour)", day_local="day that meeting will starts at (24-hour)", month_local="month that meeting will starts at (24-hour)", year_local="year that meeting will starts at (24-hour)", participate_role="members of the role that are asked to join the meeting", remind_time_ago="time before the meeting that the bot will remind the members to join the meeting")
    async def create_meeting(self, interaction: discord.Interaction, title: str, hour_local: int, minute_local: int, participate_role: Union[discord.Role, None]=None, remind_time_ago: Union[discord.app_commands.Choice[int], None]=None ,day_local: Union[int, None]=None, month_local: Union[int, None]=None, year_local: Union[int, None]=None):
        await interaction.response.defer()

        server_setting_doc = await self.server_setting_coll.find_one({"guild_id": interaction.guild.id})
        if server_setting_doc is None:
            raise Exception("Please set server settings first.")
        timezone = server_setting_doc["timezone"]

        admin_role_id = server_setting_doc["admin_role_id"]
        meeting_admin_role = interaction.guild.get_role(admin_role_id)
        if interaction.user not in meeting_admin_role.members:
            raise Exception("You need to have the meeting admin role to create a meeting.")
        
        now_time_UTC = datetime.datetime.now(datetime.timezone.utc).replace(second=0, microsecond=0)
        now_time_local = now_time_UTC.astimezone(pytz.timezone(timezone))
        day_local = day_local or now_time_local.day
        month_local = month_local or now_time_local.month
        year_local = year_local or now_time_local.year
        
        try:
            meeting_time_local = pytz.timezone(timezone).localize(datetime.datetime(year_local, month_local, day_local, hour_local, minute_local))
        except ValueError:
            raise Exception("Please type the correct time.")
        
        meeting_time_UTC = meeting_time_local.astimezone(pytz.utc)
        now_time_UTC = datetime.datetime.now(datetime.timezone.utc).replace(second=0, microsecond=0)
        if meeting_time_UTC <= now_time_UTC:
            raise Exception("Please type the correct time.")
        
        if interaction.channel.type != discord.ChannelType.text:
            raise Exception("Please use this command in a text channel.")
        
        start_timestamp = int(meeting_time_UTC.timestamp())
        if remind_time_ago is not None:
            remind_time_UTC = meeting_time_UTC - datetime.timedelta(minutes=remind_time_ago.value)
            remind_timestamp = int(remind_time_UTC.timestamp())
        else:
            remind_timestamp = None

        _id = ObjectId()
        meeting = Meeting(bot=self.bot, _id=_id)
        embed = await meeting.create_meeting(guild_id=interaction.guild_id, title=title, start_timestamp=start_timestamp, remind_timestamp=remind_timestamp, participate_role_id=participate_role.id if participate_role != None else interaction.guild_id)
        embed.color = discord.Color.blue()

        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="set_server_settings", description="set server settings")
    @app_commands.describe(timezone="timezone of your region", meeting_admin_role="choose the role that can control meeting")
    @app_commands.choices(timezone=[
        app_commands.Choice(name="GMT+0", value="Etc/GMT-0"),
        app_commands.Choice(name="GMT+1", value="Etc/GMT-1"),
        app_commands.Choice(name="GMT+2", value="Etc/GMT-2"),
        app_commands.Choice(name="GMT+3", value="Etc/GMT-3"),
        app_commands.Choice(name="GMT+4", value="Etc/GMT-4"),
        app_commands.Choice(name="GMT+5", value="Etc/GMT-5"),
        app_commands.Choice(name="GMT+6", value="Etc/GMT-6"),
        app_commands.Choice(name="GMT+7", value="Etc/GMT-7"),
        app_commands.Choice(name="GMT+8", value="Etc/GMT-8"),
        app_commands.Choice(name="GMT+9", value="Etc/GMT-9"),
        app_commands.Choice(name="GMT+10", value="Etc/GMT-10"),
        app_commands.Choice(name="GMT+11", value="Etc/GMT-11"),
        app_commands.Choice(name="GMT+12", value="Etc/GMT-12"),
        app_commands.Choice(name="GMT-11", value="Etc/GMT+11"),
        app_commands.Choice(name="GMT-10", value="Etc/GMT+10"),
        app_commands.Choice(name="GMT-9", value="Etc/GMT+9"),
        app_commands.Choice(name="GMT-8", value="Etc/GMT+8"),
        app_commands.Choice(name="GMT-7", value="Etc/GMT+7"),
        app_commands.Choice(name="GMT-6", value="Etc/GMT+6"),
        app_commands.Choice(name="GMT-5", value="Etc/GMT+5"),
        app_commands.Choice(name="GMT-4", value="Etc/GMT+4"),
        app_commands.Choice(name="GMT-3", value="Etc/GMT+3"),
        app_commands.Choice(name="GMT-2", value="Etc/GMT+2"),
        app_commands.Choice(name="GMT-1", value="Etc/GMT+1"),
    ])
    
    async def set_server_settings(self, interaction: discord.Interaction, timezone: discord.app_commands.Choice[str], meeting_admin_role: discord.Role):
        server_setting_doc = await self.server_setting_coll.find_one({"guild_id": interaction.guild.id})
        if server_setting_doc is not None:
            raise Exception("Server settings already set.")
        if not interaction.user.guild_permissions.administrator:
            raise Exception("You need to have the administrator permission to set server settings.")
        
        await interaction.response.defer()
        
        meeting_category = await interaction.guild.create_category("Meeting")
        available_tags = [
            discord.ForumTag(name="Pending", emoji="⏳"),
            discord.ForumTag(name="In Progress", emoji="🔄"),
            discord.ForumTag(name="Finished", emoji="✅"),
        ]
        try:
            forum_channel = await meeting_category.create_forum(name="meeting", available_tags=available_tags)
        except Exception:
            await meeting_category.delete()
            raise Exception("Please enable the community feature in the server settings.")
        await forum_channel.edit(sync_permissions=True)
        
        content="""
# About a Meeting Thread
Bot will create one for the meeting after user use </create_meeting:1101520045449957467>

## Buttons (will be enabled after the meeting starts)
- Roll Call
Do a roll call for the members in voice channel
- End Meeting
End the meeting

## Meeting Info Embed Fields
- Title
The meeting title
- Start Time
The meeting start time
- Participate Role
The role that you want those member to participate this meeting
- Thread
The thread that has buttons and data will be sent
- Footer
The meeting _id

## Meeting Info Embed Color
- Yellow
Pending :hourglass_flowing_sand:
- Green
In Progress :arrows_counterclockwise:
- Red
Finished :white_check_mark:
"""
        thread, thread_message = await forum_channel.create_thread(name="About a Meeting Thread" ,content=content)
        await thread.edit(pinned=True)
        tags_id = {}
        for tag in forum_channel.available_tags:
            tags_id[tag.name.lower().replace(" ", "_")] = tag.id

        server_setting_doc = {
            "guild_id": interaction.guild.id,
            "timezone": timezone.value,
            "category_id": meeting_category.id,
            "forum_id": forum_channel.id,
            "tags_id": tags_id,
            "admin_role_id": meeting_admin_role.id
        }
        await self.server_setting_coll.insert_one(server_setting_doc)

        embed = discord.Embed(title="Server Settings", color=discord.Color.blue())
        embed.add_field(name="Timezone", value=timezone.name, inline=False)
        embed.add_field(name="Meeting Category", value=meeting_category.mention, inline=False)
        embed.add_field(name="Meeting Forum Channel", value=forum_channel.mention, inline=False)
        if meeting_admin_role.id == interaction.guild.id:
            embed.add_field(name="meeting admin role", value="@everyone", inline=False)
        else:
            embed.add_field(name="meeting admin role", value=meeting_admin_role.mention, inline=False)

        await interaction.followup.send(embed=embed)


async def setup(bot: MyBot):
    await bot.add_cog(MeetingCommands(bot))
