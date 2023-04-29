import discord
from discord.ext import commands
from utils.error import error
from discord.ui import Button, View
import json
import asyncio
import datetime
import pytz
import os
import uuid

class Meeting():
    def __init__(self, bot, interaction: discord.Interaction, title: str, hour: int, minute: int, timezone:str, role: discord.Role = None, day: int = None, month: int = None, year: int = None):
        self.bot = bot
        self.meeting_ID = str(uuid.uuid4())
        self.interaction = interaction
        self.guild_ID = interaction.guild.id
        self.title = title
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.role = role
        self.timezone = timezone
        self.now_time_UTC = datetime.datetime.now(datetime.timezone.utc).replace(second=0, microsecond=0)
        self.now_time_local = self.now_time_UTC.astimezone(pytz.timezone(self.timezone))
        
        self.meeting_time_local = pytz.timezone(self.timezone).localize(datetime.datetime(self.year, self.month, self.day, self.hour, self.minute))
        self.meeting_time_UTC = self.meeting_time_local.astimezone(pytz.utc)
        if self.role == None:
            self.role_ID = None
        else:
            self.role_ID = self.role.id
        self.timestamp_local = int(self.meeting_time_local.timestamp())
        self.timestamp_UTC = int(self.meeting_time_UTC.timestamp())

        # create buttons
        self.button1 = Button(label="cancle", style=discord.ButtonStyle.red)
        self.button2 = Button(label="close", style=discord.ButtonStyle.red, disabled=True)
        self.button3 = Button(label="roll call", style=discord.ButtonStyle.blurple, disabled=True)
        self.view = View(timeout=604800)
        self.view.add_item(self.button1)
        self.view.add_item(self.button2)
        self.view.add_item(self.button3)

    

    async def create_meeting(self):
        # create embed
        embed_meeting = discord.Embed(title=self.title, color=discord.Color.yellow())
        embed_meeting.add_field(name="start time", value=f"<t:{self.timestamp_local}:F> <t:{self.timestamp_local}:R>", inline=False)
        embed_meeting.set_footer(text=self.meeting_ID)
        if self.role_ID == None:
            embed_meeting.add_field(name="role", value="@everyone", inline=False)
        else:
            embed_meeting.add_field(name="role", value=self.role.mention, inline=False)
        # send meeting message
        await self.interaction.response.send_message(embed=embed_meeting, view=self.view)

        # save the meeting data
        self.message = await self.interaction.original_response()
        self.message_id = self.message.id
        self.text_channel_ID = self.message.channel.id
        self.thread = await self.message.create_thread(name="meeting info")
        self.thread_ID = self.thread.id

        with open("meeting.json", mode="r", encoding="utf8") as jfile:
            jdata = json.load(jfile)

        if str(self.timestamp_UTC) not in jdata:
            data_timestamp_chunk = jdata[str(self.timestamp_UTC)] = []
        data_timestamp_chunk = jdata[str(self.timestamp_UTC)]
        data_meeting = {
            "meeting_ID": self.meeting_ID,
            "guild_ID": self.guild_ID,
            "title": self.title,
            "text_channel_ID": self.text_channel_ID,
            "message_ID": self.message_id,
            "thread_ID": self.thread_ID,
            "role_ID": self.role_ID,
            "start_time": (self.year, self.month, self.day, self.hour, self.minute)
        }

        data_timestamp_chunk.append(data_meeting)
        jdata[str(self.timestamp_UTC)] = data_timestamp_chunk
        with open("meeting.json", mode="w", encoding="utf8") as jfile:
            json.dump(jdata, jfile, indent=4)
                    
async def setup(bot):
    await bot.add_cog(Meeting(bot))