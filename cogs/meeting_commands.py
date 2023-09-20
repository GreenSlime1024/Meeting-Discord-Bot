import discord
from discord.ext import commands
from discord import app_commands
import datetime
import pytz
from utils.error import error
import asyncio
from discord.ui import Button, Select, View
from utils.meeting import Meeting
from bot import MyBot
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
    async def create_meeting(self, interaction: discord.Interaction, title: str, hour_local: int, minute_local: int, participate_role: discord.Role = None, remind_time_ago: discord.app_commands.Choice[int] = None ,day_local: int = None, month_local: int = None, year_local: int = None):
        await interaction.response.defer()
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
        if remind_time_ago == None:
            remind_timestamp_UTC = 0
        else:
            remind_time_UTC = meeting_time_UTC - datetime.timedelta(minutes=remind_time_ago.value)
            remind_timestamp_UTC = remind_time_UTC.timestamp()
        _id = ObjectId()
        meeting = Meeting(bot=self.bot, _id=_id, guild=interaction.guild, title=title, start_timestamp_UTC=start_timestamp_UTC, remind_timestamp_UTC=remind_timestamp_UTC, participate_role=participate_role, timezone=timezone)
        # create meeting
        embed = await meeting.create_meeting()
        embed.color = discord.Color.blue()
        # send embed
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
        await interaction.response.defer()
        server_setting_coll = self.mongo_client.meeting.server_setting
        server_setting_doc = server_setting_coll.find_one({"guild_id": interaction.guild.id})
        async def create_server_setting(edit:bool):
            # check if the user is admin of the server
            if not interaction.user.guild_permissions.administrator:
                await error.error_message(interaction, error="permission error", description="You need to be the admin of this server to use this command.")
                return "error"
            # create a category for meetings voice_channel and forum
            meeting_category = await interaction.guild.create_category("meeting")
            try:
                forum_channel = await meeting_category.create_forum("meeting")
            except Exception:
                await error.error_message(interaction, error="create forum error", description="Please make sure that you have enabled the community feature.")
                return "error"
            # set permission for the forum
            await forum_channel.set_permissions(interaction.guild.default_role, send_messages=False)
            await forum_channel.set_permissions(interaction.guild.me, send_messages=True)
            # create a thread to explain how to use the forum
            file = discord.File("images/meeting_lifecycle.png", description="lifecycle of a meeting")
            thread, thread_message = await forum_channel.create_thread(name="About a Meeting Thread", file=file,content="# About a Meeting Thread\nBot will create one for the meeting after user use </create_meeting:1101520045449957467>\n\n> ## Buttons\n> ### roll call\n> Do a roll call for the members in voice channel. (will be enable after meeting start)\n> ### end\n> End meeting.\n> ## Meeting Info Embed\n> ### title\n> The meeting title.\n> ### start time\n> when the meeting will start.\n> ### participate role\n> The role that you want those member to participate this meeting.\n> ### meeting thread\n> The meeting thread that has buttons and data will be sent.\n> ### footer\n> The meeting _id.\n> ### colors\n> - Yellow\n> :hourglass_flowing_sand: pending\n> - Green\n> :arrows_counterclockwise: in progress\n> - Red\n> :white_check_mark: finished\n\n# The image below shows lifecycle of a meeting")
            await thread.edit(pinned=True)
            await thread_message.pin()
            # create tags for meeting forum
            tag_infos = [["pending", "⏳"], ["in_progress", "🔄"], ["finished", "✅"]]
            tag_ids = {}
            for tag_info in tag_infos:
                tag = await forum_channel.create_tag(name=tag_info[0], emoji=tag_info[1])
                tag_ids[tag_info[0]] = tag.id
                await asyncio.sleep(0.01)
        
            server_setting_doc = {
                    "guild_id": interaction.guild.id,
                    "timezone": timezone.value,
                    "category_id": meeting_category.id,
                    "forum_channel_id": forum_channel.id,
                    "forum_tags_id": tag_ids,
                    "admin_role_id": meeting_admin_role.id
                }
            
            # send message
            embed = discord.Embed(title="Server Settings", color=discord.Color.blue())
            embed.add_field(name="timezone", value=timezone.value, inline=False)
            embed.add_field(name="meeting category", value=meeting_category.mention, inline=False)
            embed.add_field(name="meeting forum channel", value=forum_channel.mention, inline=False)
            embed.add_field(name="meeting admin role", value=meeting_admin_role.mention, inline=False)

            # save server settings to database
            if edit:
                server_setting_coll.update_one({"guild_id": interaction.guild.id}, {"$set": server_setting_doc})
                await interaction.edit_original_response(content=None, embed=embed, view=None)
            else:
                server_setting_coll.insert_one(server_setting_doc)
                await interaction.edit_original_response(content=None, embed=embed)
            
        if server_setting_doc == None:
            await interaction.followup.send("processing...", ephemeral=True)
            if await create_server_setting(edit=False) == "error":
                return
            await interaction.followup.send("Server settings has been set.", ephemeral=True)

        else:
            async def confirm(interaction_button: discord.Interaction):
                await interaction_button.response.defer()
                if interaction_button.user != interaction.user:
                    await interaction_button.followup.send("You are not the one who sent the command.", ephemeral=True)
                    return
                meeting_coll = self.mongo_client.meeting.meeting
                meeting_coll.delete_many({"guild_id": interaction_button.guild.id})
                await interaction_button.followup.send("processing...", ephemeral=True)
                if await create_server_setting(edit=True) == "error":
                    return
                await interaction_button.followup.send("Server settings has been set.", ephemeral=True)

            embed = discord.Embed(title="Are you sure?", description="If you set server settings again, meetings that you created will be deleted.", color=discord.Color.blue())
            view = View()
            button1 = Button(style=discord.ButtonStyle.green, label="confirm")
            button1.callback = confirm
            view.add_item(button1)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(MeetingCommand(bot))
