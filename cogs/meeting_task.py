import discord
from core.classes import Cog_Extension
import datetime
import json


class MeetingTask(Cog_Extension):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        """ self.counter = 0

        async def MeetingTask():
            await self.bot.wait_until_ready()
            while not self.bot.is_closed():
                for i in jdata.keys:
                    with open('meet_time.json', mode='r', encoding='utf8') as jfile:
                        jdata = json.load(jfile)
                    now_time = datetime.datetime.now()
                    now_time_format = now_time.strftime("%Y/%m/%d %H:%M:%S")

                    if jdata[i]["time"] == now_time_format & jdata[i]["expired"] == False:
                        guild = jdata[i][guild]
                        with open('meet_notify_channel.json', mode='r', encoding='utf8') as jfile:
                            jdata = json.load(jfile)
                        channel_id = jdata[guild]
                        channel = self.bot.get_channel(channel_id)
                        await channel.send()
                        

        self.bg_task = self.bot.loop.create_task(MeetingTask()) """


async def setup(bot):
    await bot.add_cog(MeetingTask(bot))
