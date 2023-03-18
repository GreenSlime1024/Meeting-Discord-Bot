import discord
from discord.ext import commands
from core.classes import Cog_Extension
from discord import app_commands
import json
import datetime
import pytz
import os
from core.error import error
import uuid
from discord.ui import Button, View

class Meeting(Cog_Extension):
    @commands.Cog.listener()
    async def on_ready(self):
        print("meeting cog loaded.")

    @app_commands.command(name="set_meeting", description="set necessary info about the server")
    @app_commands.describe(title="title of the meeting", hour="hour that meeting will starts at (24-hour)", minute="minute that meeting will starts at", day="day that meeting will starts at", month="month that meeting will starts at", year="year that meeting will starts at", role="members of the role that are asked to join the meeting")
    async def set_meeting(self, interaction: discord.Interaction, title: str, hour: int, minute: int, role: discord.Role = None, day: int = None, month: int = None, year: int = None):
        with open("guilds_info.json", mode="r", encoding="utf8") as jfile:
            jdata = json.load(jfile)
        guild_ID = interaction.guild.id
        try:
            timezone = jdata[str(guild_ID)]["timezone"]
        except KeyError:
            await error.error_message(interaction=interaction, error="guild setting not found", description="You haven't set server settings.\nPlease use </set_server_settings:1072440724118847554> to set.")
            return

        with open("meeting.json", mode="r", encoding="utf8") as jfile:
            jdata = json.load(jfile)
        now_time_UTC = datetime.datetime.now(datetime.timezone.utc).replace(second=0, microsecond=0)
        guild_time = now_time_UTC.astimezone(pytz.timezone(timezone))

        if day == None:
            day = guild_time.day
        if month == None:
            month = guild_time.month
        if year == None:
            year = guild_time.year
        
        try:
            meeting_time = pytz.timezone(timezone).localize(datetime.datetime(year, month, day, hour, minute))
        except ValueError as e:
            await error.error_message(interaction=interaction, error=e, description="Please check if the time you typed is correct.")
        meeting_time_UTC = meeting_time.astimezone(pytz.utc)
        
        if meeting_time_UTC < now_time_UTC:
            await error.error_message(interaction=interaction, error="time had expired")
            return
 
        meeting_ID = str(uuid.uuid4())

        if role == None:
            role_ID = None
        else:
            role_ID = role.id

        with open("guilds_info.json", mode="r", encoding="utf8") as jfile:
            jdata = json.load(jfile)

        timestamp = int(meeting_time.timestamp())
        timestamp_UTC = int(meeting_time_UTC.timestamp())

        embed_set = discord.Embed(title=title, color=0x66ff47)
        embed_set.add_field(name="start time", value=f"<t:{timestamp}:F> <t:{timestamp}:R>", inline=False)
        embed_set.set_footer(text=meeting_ID)
        if role_ID == None:
            embed_set.add_field(name="role", value="@everyone", inline=False)
        else:
            embed_set.add_field(name="role", value=role.mention, inline=False)

        button1 = Button(label="cancel/close", style=discord.ButtonStyle.red)
        button2 = Button(label="roll call", style=discord.ButtonStyle.blurple)
        view = View(timeout=604800)
        view.add_item(button1)
        view.add_item(button2)
        await interaction.response.send_message(embed=embed_set, view=view)

        async def remove_meeting(interaction):
            with open("meeting.json", mode="r", encoding="utf8") as jfile:
                jdata = json.load(jfile)
            try:
                for data in jdata[str(timestamp_UTC)]:
                    if data["meeting_ID"] == meeting_ID:
                        lenth = len(jdata[str(timestamp_UTC)])
                        index = jdata[str(timestamp_UTC)].index(data)
                        status = data["status"]
                        if lenth == 1:
                            del jdata[str(timestamp_UTC)]
                        else:
                            del jdata[str(timestamp_UTC)][index]
                        with open("meeting.json", mode="w", encoding="utf8") as jfile:
                            json.dump(jdata, jfile, indent=4)
                        if status:
                            await interaction.response.send_message("canceled.")
                        else:
                            await interaction.response.send_message("closed.")
            except KeyError:
                await interaction.response.send_message("meeting is not exist.")
                return

        async def roll_call(interaction):
            absent_members = []
            attend_members = []
            with open("meeting.json", mode="r", encoding="utf8") as jfile:
                jdata = json.load(jfile)
            try:
                for data in jdata[str(timestamp_UTC)]:
                    if data["meeting_ID"] == meeting_ID:
                        guild_ID = data["guild_ID"]
                        text_channel_ID = data["text_channel_ID"]
                        thread_ID = data["thread_ID"]
                        voice_channel_ID = data["voice_channel_ID"]
            except KeyError:
                await error.error_message(interaction=interaction, error="meeting is not in progress.")
                return
                           
            guild = self.bot.get_guild(guild_ID)
            text_channel = self.bot.get_channel(text_channel_ID)
            thread = text_channel.get_thread(thread_ID)
            voice_channel = self.bot.get_channel(voice_channel_ID)
            
            if role_ID == None:
                role = None
            else:
                role = guild.get_role(role_ID)

            embed_button = discord.Embed(title=title, color=0x5865f2)
            embed_button.set_footer(text=meeting_ID)

            if role == None:
                for member in guild.members:
                    if member not in voice_channel.members:
                        absent_members.append(member.mention)
            else:
                for member in role.members:
                    if member not in voice_channel.members:
                        absent_members.append(member.mention)

            for member in voice_channel.members:
                attend_members.append(member.mention)

            if len(absent_members) > 800:
                embed_button.add_field(name="absent members", value="(text is too long. Please chack the file below.)", inline=False)
            else:
                if len(absent_members) == 0:
                    embed_button.add_field(name="absent members", value="None", inline=False)
                else:
                    embed_button.add_field(name="absent members", value=" ".join(absent_members), inline=False)

            if len(attend_members) > 800:
                embed_button.add_field(name="attend members", value="(text is too long. Please chack the file below.)", inline=False)
            else:
                if len(attend_members) == 0:
                    embed_button.add_field(name="attend members", value="None", inline=False)
                else:
                    embed_button.add_field(name="attend members", value=" ".join(attend_members), inline=False)
            
            data = {
                "absent_members": absent_members,
                "attend_membets": attend_members
            }

            filename = f"meeting_record_{meeting_ID}.json"
            with open(filename, "w") as jfile:
                json.dump(data, jfile, indent=4)
            message = await thread.send(embed=embed_button)
            await message.add_files(discord.File(filename, filename=filename))
            os.remove(filename)
            await interaction.response.send_message(f"Please check <#{thread_ID}>.", ephemeral=True)

        button1.callback = remove_meeting
        button2.callback = roll_call

        message = await interaction.original_response()
        message_id = message.id
        text_channel_ID = message.channel.id
        thread = await message.create_thread(name="meeting info")
        thread_ID = thread.id

        with open("meeting.json", mode="r", encoding="utf8") as jfile:
            jdata = json.load(jfile)

        if str(timestamp_UTC) not in jdata:
            data = jdata[str(timestamp_UTC)] = []
        data = jdata[str(timestamp_UTC)]
        meeting_data = {
            "meeting_ID": meeting_ID,
            "guild_ID": guild_ID,
            "title": title,
            "text_channel_ID": text_channel_ID,
            "message_ID": message_id,
            "thread_ID": thread_ID,
            "role_ID": role_ID,
            "start_time": (year, month, day, hour, minute),
            "status": True
        }

        data.append(meeting_data)
        jdata[str(timestamp_UTC)] = data
        with open("meeting.json", mode="w", encoding="utf8") as jfile:
            json.dump(jdata, jfile, indent=4)

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
        data = {
            "timezone": timezone.value,
            "category_ID": category.id
        }

        if timezone.value in pytz.all_timezones:
            with open("guilds_info.json", mode="r", encoding="utf8") as jfile:
                jdata = json.load(jfile)
            jdata[str(interaction.guild.id)] = data
            with open("guilds_info.json", mode="w", encoding="utf8") as jfile:
                json.dump(jdata, jfile, indent=4)
            await interaction.response.send_message(f"guild info set.", ephemeral=False)
        else:
            await error.error_message(interaction=interaction, error="timezone is not correct", description="Time zone you typed is not correct\nPlease use </timezone-names:1072440724118847556> to check.")
            return

async def setup(bot):
    await bot.add_cog(Meeting(bot))
