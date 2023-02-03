import discord
from discord.ext import commands
from core.classes import Cog_Extension
from discord import app_commands
import asyncio
import json
import datetime
import pytz
import os
from core.error import error


class Meet(Cog_Extension):
    @commands.Cog.listener()
    async def on_ready(self):
        print("meeting cog loaded.")

    @app_commands.command(name="set_meeting", description="set the meeting voice channel and when to begin")
    async def set_meeting(self, interaction: discord.Interaction, title: str, voice_channel: discord.VoiceChannel,  hour: int, minute: int, role: discord.Role = None, day: int = None, month: int = None, year: int = None):
        if day == None:
            day = datetime.datetime.today().day
        if month == None:
            month = datetime.datetime.today().month
        if year == None:
            year = datetime.datetime.today().year
        guild_ID = interaction.guild.id

        with open("guilds_info.json", mode="r", encoding="utf8") as jfile:
            jdata = json.load(jfile)
        timezone = jdata[str(guild_ID)]["timezone"]

        with open("meeting_info.json", mode="r", encoding="utf8") as jfile:
            jdata = json.load(jfile)
        now_time = datetime.datetime.now().replace(second=0, microsecond=0)
        now_time_UTC = pytz.timezone('UTC').localize(now_time)
        meeting_time = pytz.timezone(timezone).localize(datetime.datetime(year, month, day, hour, minute))
        meeting_time_UTC = meeting_time.astimezone(pytz.utc)
        if meeting_time_UTC < now_time_UTC:
            await error.error_message(interaction=interaction, error="time is expired")
            return

        
        voice_channel_ID = voice_channel.id

        if role == None:
            role_ID = None
        else:
            role_ID = role.id

        data = {
            "guild_ID": guild_ID,
            "title": title,
            "voice_channel_ID": voice_channel_ID,
            "role_ID": role_ID,
            "time": [year, month, day, hour, minute]
        }
        try:
            time = datetime.datetime(year, month, day, hour, minute)
        except ValueError as e:
            await error.error_message(interaction=interaction, error=e)
            return

        with open("meeting_info_count.json", mode="r", encoding="utf8") as jfile:
            jdata = json.load(jfile)
        count = jdata["count"]

        with open("meeting_info.json", mode="r", encoding="utf8") as jfile:
            jdata = json.load(jfile)
        jdata[count] = data

        with open("meeting_info.json", mode="w", encoding="utf8") as jfile:
            json.dump(jdata, jfile, indent=4)

        with open("meeting_info_count.json", mode="r", encoding="utf8") as jfile:
            jdata = json.load(jfile)
        jdata["count"] = count+1

        with open("meeting_info_count.json", mode="w", encoding="utf8") as jfile:
            json.dump(jdata, jfile, indent=4)
    
        with open("guilds_info.json", mode="r", encoding="utf8") as jfile:
            jdata = json.load(jfile)
        
        time_UTC = pytz.timezone(timezone).localize(time)
        timestamp = int(time_UTC.timestamp())

        embed = discord.Embed(title=title, color=0x66ff47)
        embed.add_field(name="voice channel",
                        value=f"{voice_channel.mention}", inline=False)
        embed.add_field(
            name="meeting time", value=f"<t:{timestamp}:F> <t:{timestamp}:R>", inline=False)
        embed.set_footer(text=count)
        if role_ID == None:
            embed.add_field(name="role", value="@everyone", inline=False)
        else:
            embed.add_field(name="role", value=role.mention, inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="set_server_settings", description="set server settings")
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
            await interaction.response.send_message(f"set successfully.", ephemeral=False)
        else:
            await error.error_message(interaction=interaction, error="timezone is not correct")

    @app_commands.command(name="get_meeting_record_json", description="get meeting record json")
    async def get_meeting_record_json(self, interaction: discord.Interaction, meeting_id: int):
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
