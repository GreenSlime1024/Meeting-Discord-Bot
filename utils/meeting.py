import discord
from discord.ext import commands
from pymongo import MongoClient
from utils.error import error
from discord.ui import Button, View
import json
import asyncio
import datetime
import pytz
import os
import uuid
from bot import MyBot
from bson.objectid import ObjectId

class Meeting():
    def __init__(self, bot: MyBot, _id:ObjectId, guild:discord.Guild, title: str, start_timestamp_UTC, timezone:str, participate_role: discord.Role, remind_timestamp_UTC):
        self.bot = bot
        self._id = _id
        self.mongo_client:MongoClient  = bot.mongo_client
        self.guild = guild
        self.title = title
        self.participate_role = participate_role
        self.timezone = timezone
        self.start_timestamp_UTC = start_timestamp_UTC
        self.start_time = datetime.datetime.fromtimestamp(start_timestamp_UTC, pytz.timezone(timezone))
        self.start_timestamp_local = self.start_time.timestamp()
        self.remind_timestamp_UTC = remind_timestamp_UTC
        
        if self.participate_role == None:
            self.participate_role_id = None
        else:   
            self.participate_role_id = self.participate_role.id

        # create embed
        self.embed = discord.Embed(title="Meeting Info", color=discord.Color.yellow())
        self.embed.add_field(name="title", value=self.title, inline=False)
        self.embed.add_field(name="start time", value=f"<t:{int(self.start_timestamp_local)}:F> <t:{int(self.start_timestamp_local)}:R>", inline=False)
        if self.remind_timestamp_UTC != 0:
            self.embed.add_field(name="remind time", value=f"<t:{int(self.remind_timestamp_UTC)}:F> <t:{int(self.remind_timestamp_UTC)}:R>", inline=False)
        if self.participate_role_id == None:
            self.embed.add_field(name="participate role", value="@everyone", inline=False)
        else:
            self.embed.add_field(name="participate role", value=self.participate_role.mention, inline=False)

        async def roll_call(interaction: discord.Interaction):
            await interaction.response.defer()
            # create absent and attend members list
            absent_members = []
            attend_members = []
            # get meeting info from database
            meeting_coll = self.mongo_client.meeting.meeting
            meeting_doc = meeting_coll.find_one({"_id": self._id})
            # get voice channel
            voice_channel_id = meeting_doc["voice_channel_id"]
            voice_channel = self.guild.get_channel(voice_channel_id)
            
            # a function to check if a member is in the meeting voice channel
            def absent_or_attend(member: discord.Member):
                if member not in voice_channel.members:
                    absent_members.append(member)
                else:
                    attend_members.append(member)

            if self.participate_role == None: # all members are asked to join the meeting voice channel
                for member in self.guild.members:   
                    absent_or_attend(member)
            else: # only members with participate role are asked to join the meeting voice channel
                for member in self.participate_role.members:
                    absent_or_attend(member)

            # create embed 
            embed = discord.Embed(title="roll call", color=discord.Color.blue())
            # add absent and attend members to embed
            embed.add_field(name="absent members", value="\n".join([member.mention for member in absent_members]), inline=True)
            embed.add_field(name="attend members", value="\n".join([member.mention for member in attend_members]), inline=True)
            # send embed to thread
            await interaction.followup.send(embed=embed, ephemeral=False)

        async def end_meeting(interaction: discord.Interaction=None):
            if interaction != None:
                await interaction.response.defer()
            # get meeting info from database
            meeting_coll = self.mongo_client.meeting.meeting
            meeting_doc = meeting_coll.find_one({"_id": self._id})
            server_setting_coll = self.mongo_client.meeting.server_setting
            server_setting_doc = server_setting_coll.find_one({"guild_id": self.guild.id})
            # get thread and thread message
            thread_message_id = meeting_doc["thread_message_id"]
            thread_id = meeting_doc["thread_id"]
            thread = await self.bot.fetch_channel(thread_id)
            thread_message = await thread.fetch_message(thread_message_id)
            # get voice channel
            voice_channel_id = meeting_doc["voice_channel_id"]
            voice_channel = self.bot.get_channel(voice_channel_id)
            # delete voice channel
            await voice_channel.delete()
            # disable buttons
            view = View
            view = view.from_message(thread_message, timeout=604800)
            view.children[0].disabled = True
            view.children[1].disabled = True
            # change embed color from yellow to red
            embed = thread_message.embeds[0]
            embed.color = discord.Color.red()
            # get forum tags
            forum_tags_id = server_setting_doc["forum_tags_id"]
            finished_tag_id = forum_tags_id["finished"]
            forum_channel_id: discord.ForumChannel = server_setting_doc["forum_channel_id"]
            forum_channel = self.bot.get_channel(forum_channel_id)
            finished_tag = forum_channel.get_tag(finished_tag_id)
            # change thread tag from in_progress to finished
            await thread.edit(applied_tags =[finished_tag])
            # edit thread message
            await thread_message.edit(view=view, embed=embed)
            print(f"meeting {self._id} ended")
            if interaction != None:
                await interaction.followup.send("meeting ended", ephemeral=False)
            # delete meeting doc
            meeting_coll.delete_one({"_id": self._id})
        
        # create buttons
        self.button1 = Button(label="roll call", style=discord.ButtonStyle.blurple, disabled=True, emoji="📝")
        self.button2 = Button(label="end", style=discord.ButtonStyle.grey, disabled=True, emoji="📩")

        # buttons callback
        self.button1.callback = roll_call
        self.button2.callback = end_meeting

        # create view
        self.view = View(timeout=604800)
        # add buttons into view
        self.view.add_item(self.button1)
        self.view.add_item(self.button2)

    async  def load_meeting(self):
        # get meeting info from database
        meeting_coll = self.mongo_client.meeting.meeting
        meeting_doc = meeting_coll.find_one({"_id": self._id})
        # get thread and thread message
        thread_message_id = meeting_doc["thread_message_id"]
        thread_id = meeting_doc["thread_id"]
        try: # if thread or thread message is deleted, delete meeting doc and return
            thread = await self.bot.fetch_channel(thread_id)
            thread_message = await thread.fetch_message(thread_message_id)
        except discord.NotFound:
            meeting_coll.delete_one({"_id": self._id})
            return
        # get view from thread message
        view = View
        view = view.from_message(thread_message, timeout=604800)
        # add callback to buttons
        view.children[0].callback = self.button1.callback
        view.children[1].callback = self.button2.callback
        # edit view
        await thread_message.edit(view=view)
        print(f"meeting {self._id} loaded")
        
    async def create_meeting(self):
        # get server settings
        server_setting_coll = self.mongo_client.meeting.server_setting
        server_setting_doc = server_setting_coll.find_one({"guild_id": self.guild.id})
        # get forum channel
        forum_channel_id = server_setting_doc["forum_channel_id"]
        forum_channel = self.bot.get_channel(forum_channel_id)
        # get forum tags'id list
        forum_tags_id = server_setting_doc["forum_tags_id"]
        # get pending tag
        pending_tag_id = forum_tags_id["pending"]
        pending_tag = forum_channel.get_tag(pending_tag_id)
        # create thread at forum channel
        thread, thread_message = await forum_channel.create_thread(name=f"{self.title} _id={self._id}", view=self.view, embed=self.embed, content="Meeting log will be sent here.", auto_archive_duration=1440, applied_tags=[pending_tag])
        # pin thread message that contains buttons and embed
        await thread_message.pin()
        # add thread and meeting _id to embed
        embed = self.embed
        embed.add_field(name="meeting thread", value=thread.mention, inline=False)
        embed.set_footer(text=f"meeting id: {self._id}")
        # edit thread message
        await thread_message.edit(embed=embed)

        # save the meeting data
        meeting_doc = {
            "_id": self._id,
            "status": "pending",
            "guild_id": self.guild.id,
            "title": self.title,
            "thread_message_id": thread_message.id,
            "thread_id": thread.id,
            "participate_role_id": self.participate_role_id,
            "start_timestamp_UTC": int(self.start_timestamp_UTC),
            "remind_timestamp_UTC": int(self.remind_timestamp_UTC),
            "idle_time": 0,
            }
        self.meeting_coll = self.mongo_client.meeting.meeting
        self.meeting_coll.insert_one(meeting_doc)
        return embed

    async def start_meeting(self):
        # get meeting data
        meeting_coll = self.mongo_client.meeting.meeting
        meeting_doc = meeting_coll.find_one({"_id": self._id})
        server_setting_coll = self.mongo_client.meeting.server_setting
        server_setting_doc = server_setting_coll.find_one({"guild_id": self.guild.id})
        # get thread and thread message
        thread_message_id = meeting_doc["thread_message_id"]
        thread_id = meeting_doc["thread_id"]
        thread = await self.bot.fetch_channel(thread_id)
        thread_message = await thread.fetch_message(thread_message_id)
        # get category
        category_id = server_setting_doc["category_id"]
        category = self.bot.get_channel(category_id)
        # create voice channel
        voice_channel = await self.guild.create_voice_channel(name=f"{self.title} _id={self._id}", category=category)
        # enable buttons
        view = View
        view = view.from_message(thread_message, timeout=604800)
        view.children[0].disabled = False
        view.children[1].disabled = False
        # buttons callback
        view.children[0].callback = self.button1.callback
        view.children[1].callback = self.button2.callback
        # change embed color from yellow to green
        embed = thread_message.embeds[0]
        embed.color = discord.Color.green()
        # add voice channel field to embed
        embed.add_field(name="voice channel", value=voice_channel.mention, inline=False)
        # get forum tags
        forum_tags_id = server_setting_doc["forum_tags_id"]
        in_progress_tag_id = forum_tags_id["in_progress"]
        forum_channel_id: discord.ForumChannel = server_setting_doc["forum_channel_id"]
        forum_channel = self.bot.get_channel(forum_channel_id)
        in_progress_tag = forum_channel.get_tag(in_progress_tag_id)
        # change thread tag from pending to in_progress
        await thread.edit(applied_tags =[in_progress_tag])
        # edit thread message
        await thread_message.edit(view=view, embed=embed)
        print(f"meeting {self._id} started")
        # change meeting status to in_progress
        meeting_coll.update_one({"_id": self._id}, {"$set": {"status": "in_progress", "voice_channel_id": voice_channel.id}})

    async def join_leave_log(self, member:discord.Member, action:str):
        meeting_coll = self.mongo_client.meeting.meeting
        meeting_doc = meeting_coll.find_one({"_id": self._id})
        thread_id = meeting_doc["thread_id"]
        thread = await self.bot.fetch_channel(thread_id)
        embed = discord.Embed(title="join leave log")
        if action == "join":
            embed.description = f"{member.mention} joined the meeting."
            embed.color = discord.Color.green()
        elif action == "leave":
            embed.description = f"{member.mention} left the meeting."
            embed.color = discord.Color.red()
        await thread.send(embed=embed)

    async def auto_remind(self):
        meeting_coll = self.mongo_client.meeting.meeting
        meeting_doc = meeting_coll.find_one({"_id": self._id})
        thread_id = meeting_doc["thread_id"]
        thread = await self.bot.fetch_channel(thread_id)
        embed = discord.Embed(title="Meeting Reminder", description=f"Meeting will start <t:{int(self.start_timestamp_local)}:R>.")
        embed.color = discord.Color.blue()
        await thread.send(embed=embed, content=f"{self.participate_role.mention}")
        
