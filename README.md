# Meeting-Discord-Bot

## About The Project
This is a Discord bot that can be used to help people meet online.

## Features
- Schedule meeting time

Scheduling meeting time allows participants to know exactly when the meeting will start.

- Pre-meeting reminders

When using /create_meeting, you can set pre-meeting reminders to notify participants.

- Use slash commands

Using slash commands makes it easier for users to execute commands.

- Dedicated category and forum channel for meetings

After using /set_server_settings, the bot will create dedicated categories and channels for meetings, without affecting the order of the original channels.

- Dedicated threads for meetings

After using /create_meeting, the bot will create dedicated threads for each meeting, where messages and meeting controls will be placed.

- Status tags

The bot will label threads with status tags (Pending, In Progress, Finished), allowing forum channels to quickly find meetings based on the desired tags.

- Roll call feature

Threads will have a roll call button. When pressed, it will scan the participant roles set in /create_meeting to determine who attended and who didn't, and send an embed message to the thread.

- Join/leave log

When a user enters the meeting's voice channel, a log will be left in the thread.


## Getting Started
To get a local copy up and running follow these simple steps.

### Prerequisites

- Python 3.10.6 or higher

- pip 22.2.2 or higher

### Installation

1. Clone the repo
   ```sh
   git clone https://github.com/GreenSlime1024/Meeting-Discord-Bot.git
    ```

2. Install pip packages
   ```sh
    pip install -r requirements.txt
    ```
    
## Run The Bot

1. Fill in the `token.json` with your discord bot token and mongodb connection string

2. Rename the `token.json` to `not_token.json` ~~(so that hackers can't easily find your token 🤓)~~

3. Run the bot
   ```sh
   python bot.py
   ```