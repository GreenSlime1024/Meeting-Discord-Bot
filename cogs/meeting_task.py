import discord
from discord.ext import commands
from core.classes import Cog_Extension
import datetime
import json
import asyncio
import pytz
import os


class MeetingTask(Cog_Extension):
    @commands.Cog.listener()
    async def on_ready(self):
        print("meeting_task cog loaded.")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        async def StartCheck():
            await self.bot.wait_until_ready()
            while not self.bot.is_closed():

                with open("before_meeting.json", mode="r", encoding="utf8") as jfile:
                    jdata = json.load(jfile)

                for i in jdata.keys():
                    with open("before_meeting.json", mode="r", encoding="utf8") as jfile:
                        jdata = json.load(jfile)

                    guild_ID = jdata[i]["guild_ID"]

                    with open("guilds_info.json", mode="r", encoding="utf8") as jfile:
                        jdata = json.load(jfile)
                    timezone = jdata[str(guild_ID)]["timezone"]

                    with open("before_meeting.json", mode="r", encoding="utf8") as jfile:
                        jdata = json.load(jfile)

                    year = jdata[i]["time"][0]
                    month = jdata[i]["time"][1]
                    day = jdata[i]["time"][2]
                    hour = jdata[i]["time"][3]
                    minute = jdata[i]["time"][4]

                    now_time = datetime.datetime.now().replace(second=0, microsecond=0)
                    now_time_UTC = pytz.timezone('UTC').localize(now_time)
                    meeting_time = pytz.timezone(timezone).localize(
                        datetime.datetime(year, month, day, hour, minute))
                    meeting_time_UTC = meeting_time.astimezone(pytz.utc)

                    if meeting_time_UTC == now_time_UTC:
                        title = jdata[i]["title"]
                        voice_channel_ID = jdata[i]["voice_channel_ID"]
                        voice_channel = self.bot.get_channel(voice_channel_ID)
                        role_ID = jdata[i]["role_ID"]
                        guild = self.bot.get_guild(guild_ID)
                        timestamp = int(meeting_time_UTC.timestamp())

                        if role_ID == None:
                            role = None
                        else:
                            role = guild.get_role(role_ID)

                        embed = discord.Embed(title=title, color=0x474eff)
                        embed.add_field(name="voice channel", value=f"{voice_channel.mention}", inline=False)
                        embed.add_field(name="meeting time", value=f"<t:{timestamp}:F> <t:{timestamp}:R>", inline=False)
                        
                        absent_members = []
                        attend_members = []

                        if role == None:
                            embed.add_field(
                                name="role", value="@everyone", inline=False)
                            for member in guild.members:
                                if member not in voice_channel.members:
                                    absent_members.append(member.mention)

                        else:
                            embed.add_field(
                                name="role", value=role.mention, inline=False)
                            for member in role.members:
                                if member not in voice_channel.members:
                                    absent_members.append(member.mention)

                        for member in voice_channel.members:
                            attend_members.append(member.mention)

                        with open("guilds_info.json", mode="r", encoding="utf8") as jfile:
                            jdata = json.load(jfile)
                        meeting_notify_channel_ID = jdata[str(
                            guild_ID)]["meeting_notify_channel_id"]
                        meeting_notify_channel = self.bot.get_channel(
                            meeting_notify_channel_ID)

                        if len(absent_members) > 800:
                            embed.add_field(name="absent members", value="(text is too long. Please chack the file below.)", inline=False)
                        else:
                            if len(absent_members) == 0:
                                embed.add_field(name="absent members", value="None", inline=False)
                            else:
                                embed.add_field(name="absent members", value=" ".join(absent_members), inline=False)

                        if len(attend_members) > 800:
                            embed.add_field(name="attend members", value="(text is too long. Please chack the file below.)", inline=False)
                        else:
                            if len(attend_members) == 0:
                                embed.add_field(name="attend members", value="None", inline=False)
                            else:
                                embed.add_field(name="attend members", value=" ".join(attend_members), inline=False)
                        embed.set_footer(text=i)

                        await meeting_notify_channel.send(embed=embed)

                        data = {
                            "guild_ID": guild_ID,
                            "title": title,
                            "voice_channel_ID": voice_channel_ID,
                            "role_ID": role_ID,
                            "time": [year, month, day, hour, minute],
                            "absent_members": absent_members,
                            "attend_membets": attend_members
                        }

                        filename = f"meeting_record_{i}.json"
                        with open(filename, "w") as jfile:
                            json.dump(data, jfile, indent=4)
                        await meeting_notify_channel.send(file=discord.File(filename))
                        os.remove(filename)

                        with open("meeting_save.json", mode="r", encoding="utf8") as jfile:
                            jdata = json.load(jfile)
                        jdata[i] = data
                        with open("meeting_save.json", "w") as jfile:
                            json.dump(jdata, jfile, indent=4)

                        with open("before_meeting.json", mode="r", encoding="utf8") as jfile:
                            jdata = json.load(jfile)
                        del jdata[i]
                        with open("before_meeting.json", "w") as jfile:
                            json.dump(jdata, jfile, indent=4)

                await asyncio.sleep(1)

        self.bg_task = self.bot.loop.create_task(StartCheck())


async def setup(bot):
    await bot.add_cog(MeetingTask(bot))
