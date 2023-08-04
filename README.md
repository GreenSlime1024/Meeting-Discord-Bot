# Distance-Learning-Discord-Bot

## About The Project
This is a Discord bot that can be used to help teachers and students use Discord as a distance learning platform.

## Features
### 預定會議時間

預定會議時間可以讓參與者清楚了解會議哪時候會開始。

### 會議開始前提醒

在使用 /create_meeting 時，可以設定會議開始前提醒，提醒參與者。

### 使用 slash command

用斜線指令來讓使用者更容易使用指令。

### 會議們的專屬類別 (collection) 和論壇頻道 (forum channel)

在 /set_server_settings 後，bot 會建立專屬會議們的類別和頻道，不會影響到原本頻道的秩序。

### 會議的專屬討論串 (thread)

在 /create_meeting 後，bot 會建立專屬該會議的 thread ，關於該會議的訊息和操控會議的按鈕會放在該討論串中。

### 狀態標籤 (tag)

bot 會在討論串會標示狀態標籤 (pending, in_prograss, finished) ，論壇頻道可以勾選要找的標籤，快速地找到會議。

### 點名功能

討論串中有點名按鈕，按下後，會掃描 /create_meeting 設定的參與者身分組哪些有來，哪些沒來，並用 embed 傳到該討論串中。

### 進出會議記錄 (join leave log)

 在使用者進入該會議的語音頻道時，會在該會議的討論串留下紀錄。

## Getting Started
To get a local copy up and running follow these simple steps.

### Prerequisites

- Python 3.10.6 or higher

- pip 22.2.2 or higher

### Installation

1. Clone the repo
   ```sh
   git clone https://github.com/GreenSlime1024/Distance-Learning-Discord-Bot.git
    ```

2. Install pip packages
   ```sh
    pip install -r requirements.txt
    ```
    
## Usage

1. Run `bot.py`
    ```sh
    python bot.py
    ```

2. Enter your bot token and mongoDB connection string in the `not_token.json` file

3. Run `bot.py` again
    ```sh
    python bot.py
    ```