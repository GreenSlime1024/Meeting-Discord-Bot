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


class Meet(Cog_Extension):
    @commands.Cog.listener()
    async def on_ready(self):
        print("meeting cog loaded.")

    @app_commands.command(name="set_meeting", description="set the meeting voice channel and when to begin")
    @app_commands.describe(title="title of the meeting", voice_channel="Voice channel where meeting start", hour="hour that meeting will starts at (24-hour)", minute="minute that meeting will starts at", day="day that meeting will starts at", month="month that meeting will starts at", year="year that meeting will starts at", role="members of the role that are asked to join the meeting")
    async def set_meeting(self, interaction: discord.Interaction, title: str, voice_channel: discord.VoiceChannel,  hour: int, minute: int, role: discord.Role = None, day: int = None, month: int = None, year: int = None):
        with open("guilds_info.json", mode="r", encoding="utf8") as jfile:
            jdata = json.load(jfile)
        guild_ID = interaction.guild.id
        try:
            timezone = jdata[str(guild_ID)]["timezone"]
        except KeyError:
            await error.error_message(interaction=interaction, error="guild setting not found", description="You haven't set server settings.\nPlease use </set_server_settings:1072440724118847554> to set.")
            return

        with open("before_meeting.json", mode="r", encoding="utf8") as jfile:
            jdata = json.load(jfile)
        now_time = datetime.datetime.utcnow().replace(second=0, microsecond=0)
        now_time_UTC = pytz.timezone('UTC').localize(now_time)
        guild_time = now_time.astimezone(pytz.timezone(timezone))

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
 
        voice_channel_ID = voice_channel.id
        meeting_id = str(uuid.uuid4())
        print(meeting_id)

        if role == None:
            role_ID = None
        else:
            role_ID = role.id

        with open("guilds_info.json", mode="r", encoding="utf8") as jfile:
            jdata = json.load(jfile)

        timestamp = int(meeting_time.timestamp())

        embed = discord.Embed(title=title, color=0x66ff47)
        embed.add_field(name="voice channel", value=f"{voice_channel.mention}", inline=False)
        embed.add_field(name="meeting time", value=f"<t:{timestamp}:F> <t:{timestamp}:R>", inline=False)
        embed.set_footer(text=meeting_id)
        if role_ID == None:
            embed.add_field(name="role", value="@everyone", inline=False)
        else:
            embed.add_field(name="role", value=role.mention, inline=False)

        button1 = Button(label="cancel", style=discord.ButtonStyle.red)
        button2 = Button(label="close", style=discord.ButtonStyle.red)
        view = View()
        view.add_item(button1)
        view.add_item(button2)
        await interaction.response.send_message(embed=embed, view=view)


        async def cancel(interaction):
            with open("before_meeting.json", mode="r", encoding="utf8") as jfile:
                jdata = json.load(jfile)            
            try:
                data = jdata[meeting_id]
                
            except KeyError as e:
                await error.error_message(interaction=interaction, error="The meeting is not pending.")
                return
            del jdata[meeting_id]
            with open("before_meeting.json", mode="w", encoding="utf8") as jfile:
                json.dump(jdata, jfile, indent=4)
            await interaction.response.send_message("canceled.")

            text_channel_ID = data["text_channel_ID"]
            message_ID = data["message_ID"]
            text_channel = self.bot.get_channel(text_channel_ID)
            message = await text_channel.fetch_message(message_ID)
            await message.delete()


        async def close(interaction):
            with open("durning_meeting.json", mode="r", encoding="utf8") as jfile:
                jdata = json.load(jfile)
            try:
                data = jdata[meeting_id]
            except KeyError:
                await error.error_message(interaction=interaction, error="The meeting is not in progress.")
                return
            del jdata[meeting_id]
            with open("durning_meeting.json", mode="w", encoding="utf8") as jfile:
                json.dump(jdata, jfile, indent=4)
            
            with open("after_meeting.json", mode="r", encoding="utf8") as jfile:
                jdata = json.load(jfile)
            jdata[meeting_id] = data
            with open("after_meeting.json", mode="w", encoding="utf8") as jfile:
                json.dump(jdata, jfile, indent=4)
            await interaction.response.send_message("closed.")
            

        button1.callback = cancel
        button2.callback = close

        message = await interaction.original_response()
        message_id = message.id
        text_channel_ID = message.channel.id
        data = {
            "guild_ID": guild_ID,
            "title": title,
            "voice_channel_ID": voice_channel_ID,
            "text_channel_ID": text_channel_ID,
            "message_ID": message_id,
            "role_ID": role_ID,
            "time": [year, month, day, hour, minute]
        }

        with open("before_meeting.json", mode="r", encoding="utf8") as jfile:
            jdata = json.load(jfile)
        jdata[meeting_id] = data
        with open("before_meeting.json", mode="w", encoding="utf8") as jfile:
            json.dump(jdata, jfile, indent=4)



    @app_commands.command(name="set_server_settings", description="set server settings")
    @app_commands.describe(meeting_notify_channel="Text channel where the meeting notification will be sent", timezone="your timezone")
    async def set_server_settings(self, interaction: discord.Interaction, meeting_notify_channel: discord.TextChannel, timezone: str):
        data = {
            "meeting_notify_channel_id": meeting_notify_channel.id,
            "timezone": timezone
        }
        if timezone in pytz.all_timezones:
            with open("guilds_info.json", mode="r", encoding="utf8") as jfile:
                jdata = json.load(jfile)
            jdata[str(interaction.guild.id)] = data
            with open("guilds_info.json", mode="w", encoding="utf8") as jfile:
                json.dump(jdata, jfile, indent=4)
            await interaction.response.send_message(f"guild info set.", ephemeral=False)
        else:
            await error.error_message(interaction=interaction, error="timezone is not correct", description="Time zone you typed is not correct\nPlease use </timezone-names:1072440724118847556> to check.")
            return

    @app_commands.command(name="get_meeting_record_json", description="get meeting record json")
    @app_commands.describe(meeting_id="You can find this at the embed footer")
    async def get_meeting_record_json(self, interaction: discord.Interaction, meeting_id: str):
        with open("meeting_save.json", mode="r", encoding="utf8") as jfile:
            jdata = json.load(jfile)
        try:
            data = jdata[str(meeting_id)]
            filename = f"meeting_record_{meeting_id}.json"
            with open(filename, "w") as jfile:
                json.dump(data, jfile, indent=4)
            await interaction.response.send_message(f"chack the file below.", ephemeral=False)
            message = await interaction.original_response()
            await message.add_files(discord.File(filename, filename=filename))
            os.remove(filename)
        except KeyError:
            await error.error_message(interaction=interaction, error="Meeting is not found")
        
    @app_commands.command(name="timezone-names", description="show all the timezone names")
    async def guild(self, interaction: discord.Interaction):
        await interaction.response.send_message("timezones")
        message = await interaction.original_response()
        await message.add_files(discord.File("timezone_names.txt", filename="timezone_names.txt"))


async def setup(bot):
    await bot.add_cog(Meet(bot))
