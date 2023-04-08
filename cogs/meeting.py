import discord
from discord.ext import commands
from discord.ext import tasks
from core.classes import Cog_Extension
from discord import app_commands
import json
import datetime
import pytz
import os
from core.error import error
import uuid
import asyncio
from discord.ui import Button, Select, View

class Meeting(Cog_Extension):
    @commands.Cog.listener()
    async def on_ready(self):
        print("meeting cog loaded.")

    # discord set meeting command
    @app_commands.command(name="set_meeting", description="set necessary info about the server")
    @app_commands.describe(title="title of the meeting", hour="hour that meeting will starts at (24-hour)", minute="minute that meeting will starts at", day="day that meeting will starts at", month="month that meeting will starts at", year="year that meeting will starts at", role="members of the role that are asked to join the meeting")
    async def set_meeting(self, interaction: discord.Interaction, title: str, hour: int, minute: int, role: discord.Role = None, day: int = None, month: int = None, year: int = None):
        # check if the channel type is correct
        if interaction.channel.type != discord.ChannelType.text:
            await error.error_message(interaction, error="wrong channel type", description="Please use this command in a text channel.")
            return
        
        # check if the user has set server settings
        with open("guilds_info.json", mode="r", encoding="utf8") as jfile:
            jdata = json.load(jfile)
        guild_ID = interaction.guild.id
        try:
            timezone = jdata[str(guild_ID)]["timezone"]
        except KeyError:
            await error.error_message(interaction, error="guild setting not found", description="You haven't set server settings.\nPlease use </set_server_settings:1072440724118847554> to set.")
            return
        
        # auto fill the time
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
        
        # check if the time user typed is correct
        try:
            meeting_time = pytz.timezone(timezone).localize(datetime.datetime(year, month, day, hour, minute))
        except ValueError as e:
            await error.error_message(interaction, error=e, description="Please check if the time you typed is correct.")
        meeting_time_UTC = meeting_time.astimezone(pytz.utc)
        
        if meeting_time_UTC <= now_time_UTC:
            await error.error_message(interaction, error="time had expired")
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

        # create embed
        embed_set = discord.Embed(title=title, color=discord.Color.yellow())
        embed_set.add_field(name="start time", value=f"<t:{timestamp}:F> <t:{timestamp}:R>", inline=False)
        embed_set.set_footer(text=meeting_ID)
        if role_ID == None:
            embed_set.add_field(name="role", value="@everyone", inline=False)
        else:
            embed_set.add_field(name="role", value=role.mention, inline=False)

        # create buttons
        button1 = Button(label="cancle", style=discord.ButtonStyle.red)
        button2 = Button(label="close", style=discord.ButtonStyle.red, disabled=True)
        button3 = Button(label="roll call", style=discord.ButtonStyle.blurple, disabled=True)
        view = View(timeout=604800)
        view.add_item(button1)
        view.add_item(button2)
        view.add_item(button3)
        await interaction.response.send_message(embed=embed_set, view=view)

        async def cancle_meeing(interaction):
            # disable the buttons
            view.children[0].disabled = True
            await interaction.message.edit(view=view)
            # delete the meeting data
            with open("meeting.json", mode="r", encoding="utf8") as jfile:
                jdata = json.load(jfile)
            del jdata[str(timestamp_UTC)]
            with open("meeting.json", mode="w", encoding="utf8") as jfile:
                json.dump(jdata, jfile, indent=4)
            await interaction.message.delete()

        async def close_meeting(interaction):
            # disable the buttons
            view.children[0].disabled = True
            view.children[1].disabled = True
            view.children[2].disabled = True
            await interaction.message.edit(view=view)
            # close the meeting
            MeetingTask_instance = MeetingTask(self.bot, False)
            await MeetingTask_instance.close_meeting(interaction, meeting_ID, timestamp_UTC)
        
        async def roll_call(interaction):
            absent_members = []
            attend_members = []
            with open("meeting.json", mode="r", encoding="utf8") as jfile:
                jdata = json.load(jfile)
            try:
                jdata[str(timestamp_UTC)]
            except KeyError:
                await error.error_message(interaction, error="meeting is not in progress.")
                return
            
            # find the meeting data
            for data in jdata[str(timestamp_UTC)]:
                if data["meeting_ID"] != meeting_ID:
                    return
                
            guild_ID = data["guild_ID"]
            text_channel_ID = data["text_channel_ID"]
            thread_ID = data["thread_ID"]
            voice_channel_ID = data["voice_channel_ID"]
                           
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

            filename = f"{meeting_ID}.json"
            with open(filename, "w") as jfile:
                json.dump(data, jfile, indent=4)
            message = await thread.send(embed=embed_button)
            await message.add_files(discord.File(filename, filename=filename))
            os.remove(filename)
            await interaction.response.send_message(f"Please check <#{thread_ID}>.", ephemeral=True)

        button1.callback = cancle_meeing
        button2.callback = close_meeting
        button3.callback = roll_call

        # save the meeting data
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
        with open("guilds_info.json", mode="r", encoding="utf8") as jfile:
            jdata = json.load(jfile)
        jdata[str(interaction.guild.id)] = data
        with open("guilds_info.json", mode="w", encoding="utf8") as jfile:
            json.dump(jdata, jfile, indent=4)
        await interaction.response.send_message(f"guild info set.", ephemeral=False)


class MeetingTask(Cog_Extension):
    @commands.Cog.listener()
    async def on_ready(self):
        print("meeting_task cog loaded.")

    def __init__(self, bot, task=True):
        super().__init__(bot)
        if task == True:
            self.StartCheck.start()

    def get_self(self):
        return self
    
    close_events = {}

    # 跑一個 meeting
    async def run_meeting(self, data, timestamp_UTC):
        #get data
        with open("meeting.json", mode="r", encoding="utf8") as jfile:
            jdata = json.load(jfile)
        index = jdata[str(timestamp_UTC)].index(data)
        meeting_ID = data["meeting_ID"]
        guild_ID = data["guild_ID"]
        title = data["title"]
        # thread_ID = data["thread_ID"]
        # role_ID = data["role_ID"]
        # start_time = data["start_time"]
        guild = self.bot.get_guild(guild_ID)
        with open("guilds_info.json", mode="r", encoding="utf8") as jfile:
            guilds_info_data = json.load(jfile)
        message_ID = data["message_ID"]
        text_channel_ID = data["text_channel_ID"]
        text_channel = self.bot.get_channel(text_channel_ID)
        message = await text_channel.fetch_message(message_ID)
        # disable cancle button
        # enable close, roll call button
        view = View().from_message(message)
        view.children[0].disabled = True
        view.children[1].disabled = False
        view.children[2].disabled = False
        # buttons callback
        
        await message.edit(view=view)
        # create voice channel
        category_ID = guilds_info_data[str(guild_ID)]["category_ID"]
        category = self.bot.get_channel(category_ID)
        voice_channel = await guild.create_voice_channel(name=title, category=category)
        voice_channel_ID = voice_channel.id
        message.embeds[0].add_field(name="Voice Channel", value=f"<#{voice_channel_ID}>")
        message.embeds[0].color = discord.Color.green()
        await message.edit(embed=message.embeds[0])
        data["voice_channel_ID"] = voice_channel_ID
        with open("meeting.json", mode="r", encoding="utf8") as jfile:
            jdata = json.load(jfile)
        jdata[str(timestamp_UTC)][index] = data
        with open("meeting.json", mode="w", encoding="utf8") as jfile:
            json.dump(jdata, jfile, indent=4)
        print(f"meeting {meeting_ID} started")
        self.close_events[meeting_ID] = asyncio.Event()
        await self.close_events[meeting_ID].wait()

        #close meeting
        with open("meeting.json", mode="r", encoding="utf8") as jfile:
            jdata = json.load(jfile)
        lenth = len(jdata[str(timestamp_UTC)])
        index = jdata[str(timestamp_UTC)].index(data)
        voice_channel_ID = data["voice_channel_ID"]
        voice_channel = self.bot.get_channel(voice_channel_ID)
        if lenth == 1:
            del jdata[str(timestamp_UTC)]
        else:
            del jdata[str(timestamp_UTC)][index]
        with open("meeting.json", mode="w", encoding="utf8") as jfile:
            json.dump(jdata, jfile, indent=4)
        message_ID = data["message_ID"]
        text_channel_ID = data["text_channel_ID"]
        text_channel = self.bot.get_channel(text_channel_ID)
        message = await text_channel.fetch_message(message_ID)
        message.embeds[0].color = discord.Color.red()
        
        await message.edit(embed=message.embeds[0])
        await voice_channel.delete()
        print(f"meeting {meeting_ID} closed")

    # 跑一個時間點的所有 meeting  
    async def run_all_meetings_in_list(self, timestamp_UTC):
        running_meetings = []
        with open("meeting.json", mode="r", encoding="utf8") as jfile:
            jdata = json.load(jfile)
        meeting_list = jdata[str(timestamp_UTC)]
        for data in meeting_list:
            running_meetings.append(self.run_meeting(data, timestamp_UTC)) # 先把所有的 meeting 開始跑，但不要在 for loop 裡面 await
        await asyncio.gather(*running_meetings) # 全部一起 await

    async def close_meeting(self, interaction, meeting_ID, timestamp_UTC):
        with open("meeting.json", mode="r", encoding="utf8") as jfile:
            jdata = json.load(jfile)
        for data in jdata[str(timestamp_UTC)]:
            if data["meeting_ID"] == meeting_ID:
                if int(timestamp_UTC)<=int(datetime.datetime.now(datetime.timezone.utc).replace(second=0, microsecond=0).timestamp()):
                    self.close_events[meeting_ID].set()
                    await interaction.response.send_message("closed.", ephemeral=True)

    # 每秒檢查一次，如果是整點，就跑一次 run_all_meetings_in_list
    @tasks.loop(seconds=1)
    async def StartCheck(self):
        now_time_UTC = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
        if now_time_UTC.second == 0:
            timestamp_UTC = int(now_time_UTC.replace(second=0).timestamp())
            with open("meeting.json", mode="r", encoding="utf8") as jfile:
                jdata = json.load(jfile)
            if str(timestamp_UTC) not in jdata:
                return
            asyncio.create_task(self.run_all_meetings_in_list(timestamp_UTC))

async def setup(bot):
    await bot.add_cog(Meeting(bot))
    await bot.add_cog(MeetingTask(bot))
