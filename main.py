import asyncio
import os
from sys import executable
from subprocess import run, PIPE


# Path to runner
runner = executable

# Clear console
run("cls" if os.name == "nt" else "clear", shell=True)


def version_checks():
    # Runner details
    print("Using runner: " + runner)
    output = os.popen(runner + " -V").read()
    version = output.split(" ")[1]
    print("Python version: " + version.replace("\n", ""))

    # Check if version is 3.10+
    main_version = int(version.split(".")[0])
    sub_version = int(version.split(".")[1])
    if main_version < 3:
        print("Python version 3.10+ is required")
        print("Imagine using python 2 in the modern day")
        exit(1)
    elif main_version == 3 and sub_version < 10:
        print("Python version 3.10+ is required")
        exit(1)
    elif main_version > 3:
        # In case people use this script in the future.
        print("Python 3 is recommended for this bot." + 
              "Python 4+ versions weren't avaiable when this bot was made")
        print("Bot starting, but might cause errors.")


def path_finder(path: str):
    if os.name == "nt":
        return path.replace("/", "\\")
    else:
        return path.replace("\\", "/")


# Path to bot.py
botfile = os.path.dirname(os.path.abspath(
    __file__)) + "/bot.py"
botfile = path_finder(botfile)

# Time in seconds before restarting the bot in seconds.
restart_timer = 5


def starter():
    # Getting all the required files.
    print("Fetching requirements...")
    ndir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(ndir)
    os.system(runner + " -m pip install -q -r requirements.txt")
    print("Starting bot...")


async def start_script():
    try:
        # We run the script
        run(runner+" "+botfile, check=True, shell=True)
    except Exception as e:
        if "KeyboardInterrupt" in str(e):
            exit(0)
        # Script crash detected
        await handle_crash()


async def handle_crash():
    # Restarts the script after timer
    await asyncio.sleep(restart_timer)
    await start_script()

def execute():
    starter()
    asyncio.run(start_script())
        
    
if __name__ == "__main__":
    version_checks()
    execute()
    print("Bot Stopped. Returning control to system.")
