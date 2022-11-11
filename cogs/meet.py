import discord
from discord.ext import commands
from core.classes import Cog_Extension
from discord import app_commands
import asyncio

class Meet(Cog_Extension):
    @commands.Cog.listener()
    async def on_ready(self):
        print('meet cog loaded.')

    @app_commands.command(name='set-meeting', description="set meeting")
    async def meeting(self, interaction:discord.Interaction, channel:discord.VoiceChannel, time:int):
        await interaction.response.send_message('set meeting successfully.')
        membersID = []
        for member in channel.members:
            membersID.append(member.id)
        await asyncio.sleep(time)
        await interaction.channel.send(membersID)
        
        

async def setup(bot):
    await bot.add_cog(Meet(bot))