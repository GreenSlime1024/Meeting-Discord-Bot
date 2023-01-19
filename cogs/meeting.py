import discord
from discord.ext import commands
from core.classes import Cog_Extension
from discord import app_commands
import asyncio
import json
import datetime
import pytz


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

        time = datetime.datetime(year,month,day,hour,minute)
        with open("guilds_info.json", mode="r", encoding="utf8") as jfile:
            jdata = json.load(jfile)
        timezone = jdata[str(interaction.guild.id)]["timezone"]
        time_UTC = pytz.timezone(timezone).localize(time)
        timestamp = int(time_UTC.timestamp())

        embed=discord.Embed(title=title, color=0x66ff47)
        embed.add_field(name="voice channel", value=f"{voice_channel.mention}", inline=False)
        embed.add_field(name="meeting time", value=f"<t:{timestamp}:F> <t:{timestamp}:R>", inline=False)
        if role_ID == None:
            embed.add_field(name="role", value="@everyone", inline=False)
        else:
            embed.add_field(name="role", value=role.mention, inline=False)
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="server-settings", description="set server settings")
    async def server_settings(self, interaction: discord.Interaction, meeting_notify_channel: discord.TextChannel, timezone:str):
        data = {
            "meeting_notify_channel_id": meeting_notify_channel.id,
            "timezone": timezone
        }
        with open("guilds_info.json", mode="r", encoding="utf8") as jfile:
            jdata = json.load(jfile)
        jdata[str(interaction.guild.id)] = data
        with open("guilds_info.json", mode="w", encoding="utf8") as jfile:
            json.dump(jdata, jfile, indent=4)
        await interaction.response.send_message(f"set successfully.", ephemeral=False)

async def setup(bot):
    await bot.add_cog(Meet(bot))
