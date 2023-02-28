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
 
        voice_channel_ID = voice_channel.id
        meeting_ID = str(uuid.uuid4())

        if role == None:
            role_ID = None
        else:
            role_ID = role.id

        with open("guilds_info.json", mode="r", encoding="utf8") as jfile:
            jdata = json.load(jfile)

        timestamp = int(meeting_time.timestamp())

        embed_set = discord.Embed(title=title, color=0x66ff47)
        embed_set.add_field(name="voice channel", value=f"{voice_channel.mention}", inline=False)
        embed_set.add_field(name="start time", value=f"<t:{timestamp}:F> <t:{timestamp}:R>", inline=False)
        embed_set.set_footer(text=meeting_ID)
        if role_ID == None:
            embed_set.add_field(name="role", value="@everyone", inline=False)
        else:
            embed_set.add_field(name="role", value=role.mention, inline=False)

        button1 = Button(label="cancel", style=discord.ButtonStyle.red)
        button2 = Button(label="close", style=discord.ButtonStyle.red)
        button3 = Button(label="roll call", style=discord.ButtonStyle.blurple)
        view = View(timeout=604800)
        view.add_item(button1)
        view.add_item(button2)
        view.add_item(button3)
        await interaction.response.send_message(embed=embed_set, view=view)


        async def cancel(interaction):
            with open("before_meeting.json", mode="r", encoding="utf8") as jfile:
                jdata = json.load(jfile)
            try:
                data = jdata[meeting_ID]
                del jdata[meeting_ID]    
            except KeyError:
                await error.error_message(interaction=interaction, error="The meeting is not pending.")
                return
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
                data = jdata[meeting_ID]
                del jdata[meeting_ID]
            except KeyError:
                await error.error_message(interaction=interaction, error="The meeting is not in progress.")
                return
            with open("durning_meeting.json", mode="w", encoding="utf8") as jfile:
                json.dump(jdata, jfile, indent=4)
            
            with open("after_meeting.json", mode="r", encoding="utf8") as jfile:
                jdata = json.load(jfile)
            jdata[meeting_ID] = data
            with open("after_meeting.json", mode="w", encoding="utf8") as jfile:
                json.dump(jdata, jfile, indent=4)
            await interaction.response.send_message("closed.")

        async def roll_call(interaction):
            absent_members = []
            attend_members = []
            with open("durning_meeting.json", mode="r", encoding="utf8") as jfile:
                jdata = json.load(jfile)
            try:
                guild_ID = jdata[meeting_ID]["guild_ID"]
            
                title = jdata[meeting_ID]["title"]
                voice_channel_ID = jdata[meeting_ID]["voice_channel_ID"]          
                role_ID = jdata[meeting_ID]["role_ID"]            
                text_channel_ID = jdata[meeting_ID]["text_channel_ID"]
                thread_ID = jdata[meeting_ID]["thread_ID"]
            except KeyError:
                await error.error_message(interaction=interaction, error="The meeting is not in progress.")
                return
            guild = self.bot.get_guild(guild_ID)
            voice_channel = self.bot.get_channel(voice_channel_ID)
            timestamp = int(meeting_time_UTC.timestamp())
            text_channel = self.bot.get_channel(text_channel_ID)
            thread = text_channel.get_thread(thread_ID)
            

            if role_ID == None:
                role = None
            else:
                role = guild.get_role(role_ID)

            embed_button = discord.Embed(title=title, color=0x5865f2)
            embed_button.add_field(name="voice channel", value=f"{voice_channel.mention}", inline=False)
            embed_button.add_field(name="start time", value=f"<t:{timestamp}:F> <t:{timestamp}:R>", inline=False)

            if role == None:
                embed_button.add_field(name="role", value="@everyone", inline=False)
                for member in guild.members:
                    if member not in voice_channel.members:
                        absent_members.append(member.mention)

            else:
                embed_button.add_field(name="role", value=role.mention, inline=False)
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
            embed_button.set_footer()
            await thread.send(embed=embed_button)


            """data = {
                "guild_ID": guild_ID,
                "title": title,
                "voice_channel_ID": voice_channel_ID,
                "role_ID": role_ID,
                "start_time": [year, month, day, hour, minute],
                "absent_members": absent_members,
                "attend_membets": attend_members
            }

            filename = f"meeting_record_{meeting_ID}.json"
            with open(filename, "w") as jfile:
                json.dump(data, jfile, indent=4)
            #await meeting_notify_channel.send(file=discord.File(filename))
            os.remove(filename)"""
            

        button1.callback = cancel
        button2.callback = close
        button3.callback = roll_call

        message = await interaction.original_response()
        message_id = message.id
        text_channel_ID = message.channel.id
        thread = await message.create_thread(name="meeting info")
        thread_ID = thread.id
        data = {
            "guild_ID": guild_ID,
            "title": title,
            "voice_channel_ID": voice_channel_ID,
            "text_channel_ID": text_channel_ID,
            "message_ID": message_id,
            "thread_ID": thread_ID,
            "role_ID": role_ID,
            "start_time": [year, month, day, hour, minute]
        }
        
        

        with open("before_meeting.json", mode="r", encoding="utf8") as jfile:
            jdata = json.load(jfile)
        jdata[meeting_ID] = data
        with open("before_meeting.json", mode="w", encoding="utf8") as jfile:
            json.dump(jdata, jfile, indent=4)



    @app_commands.command(name="set_server_settings", description="set server settings")
    @app_commands.describe(timezone="your timezone")
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
    @app_commands.describe(meeting_ID="You can find this at the embed footer")
    async def get_meeting_record_json(self, interaction: discord.Interaction, meeting_ID: str):
        with open("meeting_save.json", mode="r", encoding="utf8") as jfile:
            jdata = json.load(jfile)
        try:
            data = jdata[str(meeting_ID)]
            filename = f"meeting_record_{meeting_ID}.json"
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
