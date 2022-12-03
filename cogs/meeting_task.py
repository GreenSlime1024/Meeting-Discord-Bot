import discord
from discord.ext import commands
from core.classes import Cog_Extension
import datetime
import json
import asyncio
from discord.utils import get


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
                    now_time = datetime.datetime.now().replace(second=0,microsecond=0)
                    
                    
                    year = jdata[i]["time"][0]
                    month = jdata[i]["time"][1]
                    day = jdata[i]["time"][2]
                    hour = jdata[i]["time"][3]
                    minute = jdata[i]["time"][4]


                    time = datetime.datetime(year, month, day, hour, minute)
                    print(time)
                    
                    if time == now_time:
                        title = jdata[i]["title"]
                        voice_channel_ID = jdata[i]["voice_channel_ID"]
                        voice_channel = self.bot.get_channel(voice_channel_ID)
                        role_ID = jdata[i]["role_ID"]
                        guild_ID = str(jdata[i]["guild_ID"])
                        guild = self.bot.get_guild(guild_ID)
                        
                        if role_ID == None:
                            role = None
                        else:
                            role = get(guild.roles, id=role_ID)
                        
                        embed=discord.Embed(title=title, description=voice_channel.mention)
                        if role == None:
                            embed.add_field(name="role", value="@everyone", inline=True)
                        else:
                            embed.add_field(name="role", value=role.mention, inline=True)

                        guild = str(jdata[i]["guild_ID"])
                        print(guild)
                        with open("meeting_notify_channel.json", mode="r", encoding="utf8") as jfile:
                            jdata = json.load(jfile)
                        notify_channel_ID = jdata[guild]
                        notify_channel = self.bot.get_channel(notify_channel_ID)
                        await notify_channel.send(embed=embed)
                        with open("meeting_info.json", mode="r", encoding="utf8") as jfile:
                            jdata = json.load(jfile)
                        del jdata[i]
                        with open("meeting_info.json", mode="w", encoding="utf8") as jfile:
                            json.dump(jdata, jfile, indent=4)
                    
                await asyncio.sleep(5)
                        

        self.bg_task = self.bot.loop.create_task(MeetingTask())


async def setup(bot):
    await bot.add_cog(MeetingTask(bot))
