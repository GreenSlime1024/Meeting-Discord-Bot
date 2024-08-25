import discord
from discord import app_commands
from discord.ext import commands
from bot import MyBot

class SettingsCog(commands.GroupCog, name="settings"):
    def __init__(self, bot: MyBot):
        self.bot = bot
        self.server_setting_coll = self.bot.mongo_client["meeting"]["server_setting"]

    timezone=[
        app_commands.Choice(name="UTC", value="UTC"),
        app_commands.Choice(name="GMT+1", value="Etc/GMT-1"),
        app_commands.Choice(name="GMT+2", value="Etc/GMT-2"),
        app_commands.Choice(name="GMT+3", value="Etc/GMT-3"),
        app_commands.Choice(name="GMT+4", value="Etc/GMT-4"),
        app_commands.Choice(name="GMT+5", value="Etc/GMT-5"),
        app_commands.Choice(name="GMT+6", value="Etc/GMT-6"),
        app_commands.Choice(name="GMT+7", value="Etc/GMT-7"),
        app_commands.Choice(name="GMT+8", value="Etc/GMT-8"),
        app_commands.Choice(name="GMT+9", value="Etc/GMT-9"),
        app_commands.Choice(name="GMT+10", value="Etc/GMT-10"),
        app_commands.Choice(name="GMT+11", value="Etc/GMT-11"),
        app_commands.Choice(name="GMT+12", value="Etc/GMT-12"),
        app_commands.Choice(name="GMT-1", value="Etc/GMT+1"),
        app_commands.Choice(name="GMT-2", value="Etc/GMT+2"),
        app_commands.Choice(name="GMT-3", value="Etc/GMT+3"),
        app_commands.Choice(name="GMT-4", value="Etc/GMT+4"),
        app_commands.Choice(name="GMT-5", value="Etc/GMT+5"),
        app_commands.Choice(name="GMT-6", value="Etc/GMT+6"),
        app_commands.Choice(name="GMT-7", value="Etc/GMT+7"),
        app_commands.Choice(name="GMT-8", value="Etc/GMT+8"),
        app_commands.Choice(name="GMT-9", value="Etc/GMT+9"),
        app_commands.Choice(name="GMT-10", value="Etc/GMT+10"),
        app_commands.Choice(name="GMT-11", value="Etc/GMT+11"),
        app_commands.Choice(name="GMT-12", value="Etc/GMT+12"),
    ]

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} loaded.")

    async def _init(self, interaction: discord.Interaction, timezone: discord.app_commands.Choice[str], meeting_admin_role: discord.Role):
        meeting_category = await interaction.guild.create_category("Meeting")
        available_tags = [
            discord.ForumTag(name="Pending", emoji="⏳"),
            discord.ForumTag(name="In Progress", emoji="🔄"),
            discord.ForumTag(name="Finished", emoji="✅"),
        ]
        try:
            forum_channel = await meeting_category.create_forum(name="meeting", available_tags=available_tags)
        except Exception:
            await meeting_category.delete()
            raise Exception("Please enable the community feature in the server settings.")
        await forum_channel.edit(sync_permissions=True)
        
        content="""
# About a Meeting Thread
Bot will create one for the meeting after user use </create_meeting:1101520045449957467>

## Buttons (will be enabled after the meeting starts)
- Roll Call
Do a roll call for the members in voice channel
- End Meeting
End the meeting

## Meeting Info Embed Fields
- Title
The meeting title
- Start Time
The meeting start time
- Participate Role
The role that you want those member to participate this meeting
- Thread
The thread that has buttons and data will be sent
- Footer
The meeting _id

## Meeting Info Embed Color
- Yellow
Pending :hourglass_flowing_sand:
- Green
In Progress :arrows_counterclockwise:
- Red
Finished :white_check_mark:
"""
        thread, thread_message = await forum_channel.create_thread(name="About a Meeting Thread" ,content=content)
        await thread.edit(pinned=True)
        tags_id = {}
        for tag in forum_channel.available_tags:
            tags_id[tag.name.lower().replace(" ", "_")] = tag.id

        server_setting_doc = {
            "guild_id": interaction.guild.id,
            "timezone": timezone.value,
            "category_id": meeting_category.id,
            "forum_id": forum_channel.id,
            "tags_id": tags_id,
            "admin_role_id": meeting_admin_role.id
        }
        await self.server_setting_coll.insert_one(server_setting_doc)

        embed = discord.Embed(title="Server Settings", color=discord.Color.blue())
        embed.add_field(name="Timezone", value=timezone.name, inline=False)
        embed.add_field(name="Meeting Category", value=meeting_category.mention, inline=False)
        embed.add_field(name="Meeting Forum Channel", value=forum_channel.mention, inline=False)
        if meeting_admin_role.id == interaction.guild.id:
            embed.add_field(name="meeting admin role", value="@everyone", inline=False)
        else:
            embed.add_field(name="meeting admin role", value=meeting_admin_role.mention, inline=False)

        await interaction.followup.send(embed=embed)


    @app_commands.command(name="init", description="initialize the server settings")
    @app_commands.describe(timezone="timezone of the server", meeting_admin_role="role that can control meetings")
    @app_commands.choices(timezone=timezone)
    async def init(self, interaction: discord.Interaction, timezone: discord.app_commands.Choice[str], meeting_admin_role: discord.Role):
        server_setting_doc:dict | None = await self.server_setting_coll.find_one({"guild_id": interaction.guild.id})
        if not interaction.user.guild_permissions.administrator:
            raise Exception("You need to have the administrator permission to set server settings.")
        if server_setting_doc is not None:
            raise Exception("Server settings has initialized. If you want to reinitialize, use /settings-reinit command. If you just want to change the timezone or meeting admin role, use /settings-update command.")
        
        await interaction.response.defer()
        await self._init(interaction, timezone, meeting_admin_role)

    @app_commands.command(name="reinit", description="reinitialize the server settings")
    @app_commands.describe(timezone="timezone of the server", meeting_admin_role="role that can control meetings")
    @app_commands.choices(timezone=timezone)
    async def reinit(self, interaction: discord.Interaction, timezone: discord.app_commands.Choice[str], meeting_admin_role: discord.Role):
        server_setting_doc:dict | None = await self.server_setting_coll.find_one({"guild_id": interaction.guild.id})
        if not interaction.user.guild_permissions.administrator:
            raise Exception("You need to have the administrator permission to set server settings.")
        if server_setting_doc is None:
            raise Exception("Server settings has not initialized. If you want to initialize, use /settings-init command.")
        else:
            await self.server_setting_coll.delete_one({"guild_id": interaction.guild.id})
        
        await interaction.response.defer()
        await self._init(interaction, timezone, meeting_admin_role)

    @app_commands.command(name="update", description="update the server settings")
    @app_commands.describe(timezone="timezone of the server", meeting_admin_role="role that can control meetings")
    @app_commands.choices(timezone=timezone)
    async def update(self, interaction: discord.Interaction, timezone: discord.app_commands.Choice[str], meeting_admin_role: discord.Role):
        server_setting_doc:dict | None = await self.server_setting_coll.find_one({"guild_id": interaction.guild.id})
        if not interaction.user.guild_permissions.administrator:
            raise Exception("You need to have the administrator permission to set server settings.")
        if server_setting_doc is None:
            raise Exception("Server settings has not initialized. If you want to initialize, use /settings-init command.")
        
        await interaction.response.defer()
        await self.server_setting_coll.update_one({"guild_id": interaction.guild.id}, {"$set": {"timezone": timezone.value, "admin_role_id": meeting_admin_role.id}})
        embed = discord.Embed(title="Server Settings", color=discord.Color.blue())
        embed.add_field(name="Timezone", value=timezone.name, inline=False)
        if meeting_admin_role.id == interaction.guild.id:
            embed.add_field(name="meeting admin role", value="@everyone", inline=False)
        else:
            embed.add_field(name="meeting admin role", value=meeting_admin_role.mention, inline=False)

        await interaction.followup.send(embed=embed)
        

async def setup(bot: MyBot):
    await bot.add_cog(SettingsCog(bot))