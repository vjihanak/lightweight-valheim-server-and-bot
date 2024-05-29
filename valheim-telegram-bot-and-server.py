import os
import requests
import random
import shutil
import subprocess
import threading
from datetime import datetime
from time import sleep

TARGET_DIR = "/home/valheim/valheim-server"
STEAMCMD_PATH = "/usr/games/steamcmd"
SERVER_EXECUTABLE = "valheim_server.x86_64"

SERVER_NAME = os.environ.get('SERVER_NAME', '')
SERVER_PORT = os.environ.get('SERVER_PORT', '')
SERVER_PASSWORD = os.environ.get('SERVER_PASSWORD', '')
WORLD_NAME = os.environ.get('WORLD_NAME', '')
TG_API_TOKEN = os.environ.get('TG_API_TOKEN', '')
TG_CHAT_ID = os.environ.get('TG_CHAT_ID', '')
SERVER_OUTPUT_FILE = os.path.join("/home/valheim/valheim-server/server-output.txt")
SCRIPT_LOG_FILE_PATH = None # Optional file where all the connections and other info gets saved with a timestamp (File must be created beforehand if used) (Keep as None if not in use).
INITIALIZE_LOG = True # Defines if the script log will be initialized on first run. (Required on first start)
DEATH_MESSAGES = ["Ouch.", "Better luck next time.", "That must've hurt.", ] # List of messages that will be randomly selected to the message when a player dies

def InitializeServer():
    print("Initializing server...")
    server_executable_path = os.path.join(TARGET_DIR, SERVER_EXECUTABLE)
    if not os.path.exists(server_executable_path):
        print("Starting server first time setup...")
        subprocess.run([STEAMCMD_PATH, "+@sSteamCmdForcePlatformType", "linux",
                        "+force_install_dir", TARGET_DIR,
                        "+login", "anonymous",
                        "+app_update", "896660", "-beta", "none", "validate",
                        "+quit"])
    else:
        print("Server already initialized.")

# Copies the provided world to the correct directory
def CopyWorld():
    src_dir = "/home/valheim/provided_world"
    dest_dir = "/home/valheim/.config/unity3d/IronGate/Valheim/worlds_local"
    if os.path.exists(src_dir):
        os.makedirs(dest_dir)
        files = [f for f in os.listdir(src_dir) if os.path.isfile(os.path.join(src_dir, f))]
        if not files:
            print("No files to copy.")
            return
        print("Copying provided files...")
        for file_name in files:
            src_file = os.path.join(src_dir, file_name)
            dest_file = os.path.join(dest_dir, file_name)
            shutil.copy2(src_file, dest_file)
            print(f"Copied {file_name} to {dest_dir}")

def RunServer():
    print("Starting server...")
    original_ld_path = os.environ.get('LD_LIBRARY_PATH', '')
    os.environ['LD_LIBRARY_PATH'] = f"./linux64:{original_ld_path}"
    os.environ['SteamAppID'] = "892970"
    print(f"Options: {SERVER_NAME} {SERVER_PORT} {SERVER_PASSWORD} {WORLD_NAME} {TG_API_TOKEN} {TG_CHAT_ID}")
    process = subprocess.Popen(["./" + SERVER_EXECUTABLE, "-name", SERVER_NAME, "-port", SERVER_PORT,
                                "-nographics", "-batchmode", "-world", WORLD_NAME, "-password", SERVER_PASSWORD,
                                "-crossplay"],
                               cwd=TARGET_DIR,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               text=True)
    sleep(60)
    threading.Thread(target=ReadLog, args=(process.stdout,)).start()
    threading.Thread(target=ReadLog, args=(process.stderr,)).start()
    process.wait()

# Message levels: 0 = info, 1 = warning, 3 = error
def SendMessage(msgLevel, message):
    message_text = ""
    match msgLevel:
        case 1:
            message_text = "Info: "
        case 2:
            message_text = "Warning: "
        case 3:
            message_text = "Error: "
    message_text += message
    url = f"https://api.telegram.org/bot{TG_API_TOKEN}/sendMessage"
    params = {"chat_id": TG_CHAT_ID, "text": message_text}
    response = requests.post(url, params=params)
    print(response.text)

# Message levels: 0 = info, 1 = warning, 3 = error
def SendMessageDebug(msgLevel: int, message):
    message_text = ""
    match msgLevel:
        case 1:
            message_text = "Info: "
        case 2:
            message_text = "Warning: "
        case 3:
            message_text = "Error: "
    message_text += message
    print(message_text)

def Log(timestamp: int, output: str):
    if SCRIPT_LOG_FILE_PATH:
        with open(SCRIPT_LOG_FILE_PATH, 'a') as file:
            file.write(f"{timestamp}:{output}\n")

# Returns the timestamp from a line
def GetTimestamp(line: str) -> int:
    output_timestamp = line.split()
    output_time = " ".join(output_timestamp[:2])
    output_timestamp = datetime.strptime(output_time[:-1], "%m/%d/%Y %H:%M:%S")
    output_timestamp = output_timestamp.replace(year=datetime.now().year)
    return int(output_timestamp.timestamp())

def ReadLog(pipe):
    print("Starting to read log...")
    if SCRIPT_LOG_FILE_PATH != None and not os.path.isfile(SCRIPT_LOG_FILE_PATH):
        print("Error: Could not find script log file. Make sure the path is provided correctly and that the file exists.")

    player_count = ""
    while True:
        line = pipe.readline()
        if not line:
            sleep(0.5)
            continue
        else:
            if "Player joined server" in line:
                substring = line.split()
                player_count = substring[-2]
                continue
            elif "I HAVE ARRIVED!" in line:
                substring = line.split("<color=orange>")[1]
                username = (substring.split("</color>")[0]).strip()
                print("Found new player connection")
                SendMessage(1, f"{username} has joined! Players present: {player_count}")
                Log(GetTimestamp(line), f"Player connected: {username}")
                continue
            elif "Player connection lost" in line:
                print("Player has disconnected.")
                pfound = False
                substring = line.split()
                player_count = substring[-2]
                if not pfound:
                    SendMessage(1, f"Player has left the server. Players present: {player_count}")
                    Log(GetTimestamp(line), f"Player disconnected: {username}")
                continue
            elif "Random event set:" in line:
                event_name = ((line.split("Random event set:"))[1]).strip()
                print("Found new random event")
                match event_name:
                    case "army_theelder":
                        SendMessage(2, "Greydwarf raid has started!")
                    case "army_eikthyr":
                        SendMessage(2, "Boars and Necks raid has started!")
                    case "army_bonemass":
                        SendMessage(2, "Skeleton and draugr raid has started!")
                    case "army_moder":
                        SendMessage(2, "Drakes raid has started!")
                    case "army_goblin":
                        SendMessage(2, "Fuling raid has started!")
                    case "foresttrolls":
                        SendMessage(2, "Troll raid has started!")
                    case "blobs":
                        SendMessage(2, "Blob and Oozer raid has started!")
                    case "skeletons":
                        SendMessage(2, "Skeleton raid has started!")
                    case "surtlings":
                        SendMessage(2, "Surtling raid has started!")
                    case "wolves":
                        SendMessage(2, "Wolf raid has started!")
                    case _:
                        SendMessage(2, "Unknown raid has started")
                Log(GetTimestamp(line), f"Raid started: {event_name}")
                continue
            
            elif "Got character ZDOID" in line and ": 0:0" in line:
                substring = line.split("Got character ZDOID from")[1]
                username = (substring.split(": 0:0")[0]).strip()
                print("Found new player death")
                SendMessage(1, f"{username} has died! {random.choice(DEATH_MESSAGES)}")
                Log(GetTimestamp(line), f"Player died: {username}")
                continue

if __name__=="__main__": 
    print("Running server install...")
    InitializeServer()
    CopyWorld()
    RunServer()
