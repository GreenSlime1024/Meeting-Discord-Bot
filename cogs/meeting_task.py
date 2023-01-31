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
        self.counter = 0

        async def MeetingTask():
            await self.bot.wait_until_ready()
            while not self.bot.is_closed():

                with open("meeting_info.json", mode="r", encoding="utf8") as jfile:
                    jdata = json.load(jfile)

                for i in jdata.keys():
                    with open("meeting_info.json", mode="r", encoding="utf8") as jfile:
                        jdata = json.load(jfile)

                    guild_ID = jdata[i]["guild_ID"]

                    with open("guilds_info.json", mode="r", encoding="utf8") as jfile:
                        jdata = json.load(jfile)
                    timezone = jdata[str(guild_ID)]["timezone"]

                    with open("meeting_info.json", mode="r", encoding="utf8") as jfile:
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

                    print(f"now time: {now_time_UTC}")
                    print(f"meeting_time: {meeting_time}")

                    if meeting_time_UTC == now_time_UTC:
                        title = jdata[i]["title"]
                        voice_channel_ID = jdata[i]["voice_channel_ID"]
                        voice_channel = self.bot.get_channel(voice_channel_ID)
                        role_ID = jdata[i]["role_ID"]
                        guild = self.bot.get_guild(guild_ID)

                        if role_ID == None:
                            role = None
                        else:
                            role = guild.get_role(role_ID)

                        embed = discord.Embed(
                            title=title, description=voice_channel.mention, color=0x474eff)
                        embed.set_footer(text=i)
                        absent_members = ""
                        if role == None:
                            embed.add_field(
                                name="role", value="@everyone", inline=False)
                            for member in guild.members:
                                if member not in voice_channel.members:
                                    absent_members += member.mention+" "
                                    print(member.mention)

                        else:
                            embed.add_field(
                                name="role", value=role.mention, inline=False)
                            for member in role.members:
                                if member not in voice_channel.members:
                                    absent_members += member.mention+" "
                                    print(member.mention)

                        with open("guilds_info.json", mode="r", encoding="utf8") as jfile:
                            jdata = json.load(jfile)
                        meeting_notify_channel_ID = jdata[str(
                            guild_ID)]["meeting_notify_channel_id"]
                        meeting_notify_channel = self.bot.get_channel(
                            meeting_notify_channel_ID)

                        print(len(absent_members))
                        if len(absent_members) < 200:
                            embed.add_field(name="absent members",
                                            value=absent_members, inline=False)
                            await meeting_notify_channel.send(embed=embed)
                        else:
                            embed.add_field(
                                name="absent members", value="(text is too long. Please chack the file below.)", inline=False)
                            await meeting_notify_channel.send(embed=embed)
                        data = {
                            "guild_ID": guild_ID,
                            "title": title,
                            "voice_channel_ID": voice_channel_ID,
                            "role_ID": role_ID,
                            "time": [year, month, day, hour, minute],
                            "absent_members": absent_members
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

                        with open("meeting_info.json", mode="r", encoding="utf8") as jfile:
                            jdata = json.load(jfile)
                        del jdata[i]
                        with open("meeting_info.json", "w") as jfile:
                            json.dump(jdata, jfile, indent=4)

                await asyncio.sleep(1)

        self.bg_task = self.bot.loop.create_task(MeetingTask())


async def setup(bot):
    await bot.add_cog(MeetingTask(bot))
