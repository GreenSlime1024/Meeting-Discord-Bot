import discord
from discord.ext import commands
from core.classes import Cog_Extension
import datetime
import json
import asyncio


class MeetingTask(Cog_Extension):
    @commands.Cog.listener()
    async def on_ready(self):
        print('meeting_task cog loaded.')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.counter = 0

        async def MeetingTask():
            await self.bot.wait_until_ready()
            while not self.bot.is_closed():
            
                with open('meeting_info.json', mode='r', encoding='utf8') as jfile:
                    jdata = json.load(jfile)

                for i in jdata.keys():
                    with open('meeting_info.json', mode='r', encoding='utf8') as jfile:
                        jdata = json.load(jfile)
                    now_time = datetime.datetime.now()
                    
                    if jdata[i]["expired"] == True:
                        return
                    if jdata[i]["time"][0] != now_time.year:
                        return
                    if jdata[i]["time"][1] != now_time.month:
                        return
                    if jdata[i]["time"][2] != now_time.day:
                        return
                    if jdata[i]["time"][3] != now_time.hour:
                        return
                    if jdata[i]["time"][4] != now_time.minute:
                        return
                    
                    title = jdata[i]["title"]
                    voice_channel_ID = jdata[i]["voice_channel_ID"]
                    voice_channel = self.bot.get_channel(voice_channel_ID)
                    
                    

                    embed=discord.Embed(title=title, description=voice_channel.mention)
                    embed.add_field(name="key", value="value", inline=False)

                    guild = jdata[i]["guild_ID"]
                    with open('meeting_notify.json', mode='r', encoding='utf8') as jfile:
                        jdata = json.load(jfile)
                    notify_channel_ID = jdata[guild]
                    notify_channel = self.bot.get_channel(notify_channel_ID)

                    await notify_channel.send(embed=embed)
            await asyncio.sleep(1)
                        

        self.bg_task = self.bot.loop.create_task(MeetingTask())


async def setup(bot):
    await bot.add_cog(MeetingTask(bot))
