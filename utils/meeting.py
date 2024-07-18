import discord
from bot import MyBot
from bson.objectid import ObjectId
from typing import Union
import asyncio


class Meeting():
    def __init__(self, bot: MyBot, _id:ObjectId):
        self.bot = bot
        self._id = _id
        self.server_setting_coll = self.bot.mongo_client["meeting"]["server_setting"]
        self.meeting_coll = self.bot.mongo_client["meeting"]["meeting"]

    async def create_meeting(self, guild_id:int, title:str, start_timestamp:int, participate_role_id:int, remind_timestamp:Union[int, None]=None):
        server_setting_doc:dict = await self.server_setting_coll.find_one({"guild_id": guild_id})
        forum_id:int = server_setting_doc["forum_id"]
        forum_channel:discord.ForumChannel = self.bot.get_channel(forum_id)
        pending_tag_id:int = server_setting_doc["tags_id"]["pending"]
        pending_tag:discord.ForumTag = forum_channel.get_tag(pending_tag_id)
        guild = self.bot.get_guild(guild_id)

        embed = discord.Embed(title="Meeting Info", color=discord.Color.yellow())
        embed.add_field(name="Title", value=title, inline=False)
        embed.add_field(name="Start Time", value=f"<t:{start_timestamp}:F> <t:{start_timestamp}:R>", inline=False)
        if remind_timestamp is not None:
            embed.add_field(name="Remind Time", value=f"<t:{remind_timestamp}:F> <t:{remind_timestamp}:R>", inline=False)
        if participate_role_id != guild_id:
            role:discord.Role = guild.get_role(participate_role_id)
            embed.add_field(name="Participate Role", value=role.mention, inline=False)
        else:
            embed.add_field(name="Participate Role", value="@everyone", inline=False)
        embed.set_footer(text=self._id)
        
        view = Meeting_Buttons()
        thread, thread_message = await forum_channel.create_thread(name=title, view=view, applied_tags=[pending_tag], auto_archive_duration=1440)
        embed.add_field(name="Thread", value=thread.mention, inline=False)
        await asyncio.gather(
            thread_message.edit(embed=embed),
            thread_message.pin()
        )

        meeting = {
            "_id": self._id,
            "status": "pending",
            "guild_id": guild_id,
            "title": title,
            "thread_id": thread.id,
            "participate_role_id": participate_role_id,
            "start_timestamp": start_timestamp,
            "remind_timestamp": remind_timestamp,
            "idle": 0,
        }
        await self.meeting_coll.insert_one(meeting)
        print(f"Meeting {self._id} created")
        return embed
    
    async def start_meeting(self):
        meeting_doc:dict = await self.meeting_coll.find_one({"_id": self._id})
        guild_id:int = meeting_doc["guild_id"]
        server_setting_doc:dict = await self.server_setting_coll.find_one({"guild_id": guild_id})
        thread_id:int = meeting_doc["thread_id"]
        thread:discord.Thread | None = self.bot.get_channel(thread_id)
        if thread is None:
            self.meeting_coll.delete_one({"_id": self._id})
            print(f"Meeting {self._id} deleted")
            return
        thread_message:discord.Message | None = thread.starter_message
        if thread_message is None:
            thread_message = await thread.fetch_message(thread_id)

        view = Meeting_Buttons()
        view.from_message(thread_message, timeout=None)
        view.children[0].disabled = False
        view.children[1].disabled = False

        category_id:int = server_setting_doc["category_id"]
        category:discord.CategoryChannel = self.bot.get_channel(category_id)
        voice_channel = await category.create_voice_channel(name=meeting_doc["title"])

        embed = thread_message.embeds[0]
        embed.color = discord.Color.green()
        embed.add_field(name="Voice Channel", value=voice_channel.mention, inline=False)
        await thread_message.edit(embed=embed, view=view)

        tags_id:int = server_setting_doc["tags_id"]
        in_progress_tag_id:int = tags_id["in_progress"]
        forum_id:int = server_setting_doc["forum_id"]
        forum_channel:discord.ForumChannel = self.bot.get_channel(forum_id)
        in_progress_tag:discord.ForumTag = forum_channel.get_tag(in_progress_tag_id)
        await thread.edit(applied_tags=[in_progress_tag])
        await self.meeting_coll.update_one({"_id": self._id}, {"$set": {"status": "in_progress", "voice_channel_id": voice_channel.id}})

        print(f"Meeting {self._id} started")

    async def end_meeting(self):
        meeting_doc:dict = await self.meeting_coll.find_one({"_id": self._id})
        guild_id:int = meeting_doc["guild_id"]
        server_setting_doc:dict = await self.server_setting_coll.find_one({"guild_id": guild_id})
        thread_id:int = meeting_doc["thread_id"]
        thread:discord.Thread | None = self.bot.get_channel(thread_id)
        if thread is None:
            self.meeting_coll.delete_one({"_id": self._id})
            print(f"Meeting {self._id} deleted")
            return
        thread_message:discord.Message | None = thread.starter_message
        if thread_message is None:
            thread_message = await thread.fetch_message(thread_id)

        view = Meeting_Buttons()
        view.from_message(thread_message, timeout=None)
        view.children[0].disabled = True
        view.children[1].disabled = True
        view.stop()

        voice_channel_id:int = meeting_doc["voice_channel_id"]
        voice_channel:discord.VoiceChannel = self.bot.get_channel(voice_channel_id)
        await voice_channel.delete()    

        embed = thread_message.embeds[0]
        embed.color = discord.Color.red()

        tags_id = server_setting_doc["tags_id"]
        ended_tag_id = tags_id["finished"]
        forum_id = server_setting_doc["forum_id"]
        forum_channel:discord.ForumChannel = self.bot.get_channel(forum_id)
        finished_tag:discord.ForumTag = forum_channel.get_tag(ended_tag_id)
        await thread.edit(applied_tags=[finished_tag])
        await thread_message.edit(embed=embed, view=view)
        await self.meeting_coll.delete_one({"_id": self._id})

        print(f"Meeting {self._id} ended")

    async def remind_meeting(self):
        meeting_doc:dict = await self.meeting_coll.find_one({"_id": self._id})
        guild_id:int = meeting_doc["guild_id"]
        guild:discord.Guild = self.bot.get_guild(guild_id)
        thread_id:int = meeting_doc["thread_id"]
        thread:discord.Thread = self.bot.get_channel(thread_id)
        start_timestamp:int = meeting_doc["start_timestamp"]
        embed = discord.Embed(title="Meeting Reminder", description=f"Meeting will start <t:{start_timestamp}:R>.", color=discord.Color.blue())
        participate_role_id:int = meeting_doc["participate_role_id"]
        participate_role = guild.get_role(participate_role_id)

        if participate_role.id == guild_id:
            await thread.send(content="@everyone", embed=embed)
        else:
            await thread.send(content=participate_role.mention, embed=embed)
        print(f"Meeting {self._id} reminded")

    async def join_leave_log(self, member:discord.Member, action:str):
        meeting_doc:dict = await self.meeting_coll.find_one({"_id": self._id})
        thread_id:int = meeting_doc["thread_id"]
        thread:discord.Thread = self.bot.get_channel(thread_id)
        embed = discord.Embed(title="Join/Leave Log", color=discord.Color.blue())
        if action == "join":
            embed.description = f"{member.mention} joined the voice channel."
            embed.color = discord.Color.green()
        else:
            embed.description = f"{member.mention} left the voice channel."
            embed.color = discord.Color.red()
        await thread.send(embed=embed)
        
    async def roll_call(self, interaction:discord.Interaction, button:discord.ui.Button):
        meeting_doc:dict = await self.meeting_coll.find_one({"_id": self._id})
        guild_id:int = meeting_doc["guild_id"]
        guild:discord.Guild = self.bot.get_guild(guild_id)
        server_setting_doc:dict = await self.server_setting_coll.find_one({"guild_id": guild_id})
        admin_role_id:int = server_setting_doc["admin_role_id"]
        admin_role:discord.Role = guild.get_role(admin_role_id)

        if admin_role not in interaction.user.roles:
            interaction.response.send_message("You don't have permission to use this button.", ephemeral=True)
            return
        else:
            voice_channel_id = meeting_doc["voice_channel_id"]
            voice_channel:discord.VoiceChannel = guild.get_channel(voice_channel_id)
            absent_members = []
            attend_members = []

            def absent_or_attend(member: discord.Member):
                if member not in voice_channel.members:
                    absent_members.append(member)
                else:
                    attend_members.append(member)

            participate_role_id = meeting_doc["participate_role_id"]
            participate_role = guild.get_role(participate_role_id)
            for member in participate_role.members:
                absent_or_attend(member)

            embed = discord.Embed(title="Roll Call", color=discord.Color.blue())
            embed.add_field(name="Attend", value=" ".join([member.mention for member in attend_members]), inline=False)
            embed.add_field(name="Absent", value=" ".join([member.mention for member in absent_members]), inline=False)
            await interaction.response.send_message(embed=embed)


class Meeting_Buttons(discord.ui.View):
    def __init__(self, *, timeout: float | None = None):
        super().__init__(timeout=timeout)

    @discord.ui.button(label="Roll Call", style=discord.ButtonStyle.blurple, disabled=True, emoji="📝", custom_id="roll_call")
    async def roll_call(self, interaction: discord.Interaction, button: discord.ui.Button):
        bot = interaction.client
        meeting = Meeting(bot, ObjectId(interaction.message.embeds[0].footer.text))
        await meeting.roll_call(interaction, button)

    @discord.ui.button(label="End Meeting", style=discord.ButtonStyle.grey, disabled=True, emoji="📩", custom_id="end_meeting")
    async def end_meeting(self, interaction: discord.Interaction, button: discord.ui.Button):
        bot = interaction.client
        meeting = Meeting(bot, ObjectId(interaction.message.embeds[0].footer.text))
        await meeting.end_meeting()
