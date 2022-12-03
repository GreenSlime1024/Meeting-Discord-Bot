import discord
from discord.ext import commands
from core.classes import Cog_Extension
from discord import app_commands
import asyncio
import json
import datetime


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
        timestamp = int(time.timestamp())

        embed=discord.Embed(title=title, description=voice_channel.mention, color=0x66ff47)
        embed.add_field(name="meeting time", value=f"<t:{timestamp}:F>", inline=False)
        if role_ID == None:
            embed.add_field(name="role", value="@everyone", inline=False)
        else:
            embed.add_field(name="role", value=role.mention, inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="set_meeting_notify_channel", description="set meeting notify channe")
    async def set_meeting_notify_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        with open("meeting_notify_channel.json", mode="r", encoding="utf8") as jfile:
            jdata = json.load(jfile)
        jdata[interaction.guild.id] = channel.id
        with open("meeting_notify_channel.json", mode="w", encoding="utf8") as jfile:
            json.dump(jdata, jfile, indent=4)
        channel = self.bot.get_channel(channel.id)
        await interaction.response.send_message(f"set meeting notify channel to {channel.mention} successfully.", ephemeral=False)


async def setup(bot):
    await bot.add_cog(Meet(bot))
