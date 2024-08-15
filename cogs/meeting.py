import discord
from discord.ext import commands
from discord import app_commands
import datetime
import pytz
from utils.meeting import Meeting
from bot import MyBot
from bson import ObjectId
from typing import Union


class _Meeting(commands.GroupCog, name="meeting"):
    def __init__(self, bot: MyBot):
        self.bot = bot
        self.server_setting_coll = self.bot.mongo_client["meeting"]["server_setting"]
        self.meeting_coll = self.bot.mongo_client["meeting"]["meeting"]

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} cog loaded.")
        
    # discord create meeting command
    @app_commands.command(name="create", description="create a meeting")
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
    @app_commands.describe(title="title of the meeting", hour="hour that meeting will starts at (use 24-hour clock)", minute="minute that meeting will starts at", day="day that meeting will starts at", month="month that meeting will starts at", year="year that meeting will starts at", participate_role="members who are asked to participate the meeting", remind_time_ago="when to remind the meeting")
    async def create(self, interaction: discord.Interaction, title: str, hour_local: int, minute_local: int, participate_role: Union[discord.Role, None]=None, remind_time_ago: Union[discord.app_commands.Choice[int], None]=None ,day_local: Union[int, None]=None, month_local: Union[int, None]=None, year_local: Union[int, None]=None):
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
        embed = await meeting.create(guild_id=interaction.guild_id, title=title, start_timestamp=start_timestamp, remind_timestamp=remind_timestamp, participate_role_id=participate_role.id if participate_role != None else interaction.guild_id)
        embed.color = discord.Color.blue()

        await interaction.followup.send(embed=embed)
    

async def setup(bot: MyBot):
    await bot.add_cog(_Meeting(bot))
