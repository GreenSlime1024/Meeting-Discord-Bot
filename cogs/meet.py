import discord
from discord.ext import commands
from core.classes import Cog_Extension
from discord import app_commands
import asyncio
import json

with open('meet.json', mode='r', encoding='utf8') as jfile:
    jdata = json.load(jfile)

class Meet(Cog_Extension):
    @commands.Cog.listener()
    async def on_ready(self):
        print('meet cog loaded.')

    @app_commands.command(name='set_meeting', description="set the meeting voice channel and when to begin")
    async def set_meeting(self, interaction:discord.Interaction, channel:discord.VoiceChannel, time:int):
        await interaction.response.send_message('set meeting successfully.')
        membersID = []
        for member in channel.members:
            membersID.append(member.id)
        await asyncio.sleep(time)
        notify_channel = jdata[str(interaction.guild.id)]
        notify_channel = self.bot.get_channel(notify_channel)
        await notify_channel.send(membersID)

    @app_commands.command(name="set_meeting_notify_channel", description="set meeting notify channe")
    async def set_meeting_notify_channel(self, interaction: discord.Interaction, channel : discord.TextChannel):
        jdata[interaction.guild.id] = channel.id
        with open('meet.json', mode='w', encoding='utf8') as jfile:
            json.dump(jdata, jfile, indent=4)
        channel = self.bot.get_channel(channel.id)
        await interaction.response.send_message(f'meeting notify channel set to {channel.mention}.', ephemeral=False)
        
        

async def setup(bot):
    await bot.add_cog(Meet(bot))