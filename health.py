import telebot,os,csv
import logging
from dotenv import load_dotenv
import subprocess
import signal
load_dotenv()
TEL_ID = int("814952835")
BOT_TOKEN=os.environ["BOT"]
DB_FILE = os.environ["DB"]
LOG_FILE = os.path.join("logs","main.log")
bot = telebot.TeleBot(BOT_TOKEN)

# Configure logging (optional but recommended)
logging.basicConfig(filename=os.path.join("logs","health.log"), level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Function to check the health of your program
def check_health():
    try:
        # Execute the command and get the output
        process = subprocess.Popen('ps aux | grep "main.py" | wc -l', shell=True, stdout=subprocess.PIPE)
        output, error = process.communicate()

        # Convert the output to an integer
        num_processes = int(output.decode('utf-8').strip())
        # Check if the number of processes is 2 (one for grep, one for the script)
        if num_processes >= 3:
            return True
        else:
            return False

    except Exception as e:
        logging.error(f"Health check failed: {e}")
        return False


def get_pid():
    process = subprocess.Popen('ps aux | grep "main.py" | head -1', shell=True, stdout=subprocess.PIPE)
    output, error = process.communicate()
    output_args = output.decode("utf-8").strip().split()
    if output_args[-2]=="python3" and output_args[-1]=="main.py":
        return int(output_args[1])
    else:
        return 0
    
    
    

def start_server():
  try:
    # Use subprocess.Popen to execute the command in a new process
    command = "nohup python3 main.py </dev/null >/dev/null 2>&1 &"
    process = subprocess.Popen(
        command, 
        shell=True,  # Interpret the command as a shell command
        stdin=subprocess.DEVNULL,  # Redirect stdin to /dev/null
        stdout=subprocess.DEVNULL,  # Redirect stdout to /dev/null
        stderr=subprocess.STDOUT,  # Redirect stderr to stdout (and thus to /dev/null)
        preexec_fn=os.setpgrp  # Create a new process group to avoid SIGHUP
    )
    print("Server started!")
    return True
  except Exception as e:
    print(f"Error while starting server: {e}")
    logging.critical(f"Encountered an error while trying to start the server main process : {e}")
    return False


    
# Handler for messages
@bot.message_handler(func=lambda message: message.chat.id == TEL_ID)
def handle_message(message):
    if message.text.lower() == 'health':
        health_status = check_health()
        if health_status:
            bot.reply_to(message, f"Well system seems to be online 🟢  ")
        else:
            bot.reply_to(message, f"System is offline!🔴 ")
        logging.info(f"Health check requested by {message.from_user.first_name}. Status: {health_status}")
    elif message.text.lower()=="info":
        if check_health():
            bot.reply_to(message, f"This is Hosue Hunting Notification System Developed by Ouassim 🤖\n📍 Location : Paris\n🏠 Supports : Arpej, Studefi, Crous & Fac-Habitat\n System : 🟢")
        else:
            bot.reply_to(message, f"This is Hosue Hunting Notification System Developed by Ouassim 🤖\n📍 Location : Paris\n🏠 Supports : Arpej, Studefi, Crous & Fac-Habitat\n🔧 System : 🔴")
        logging.info(f"Info invoked by {message.from_user.first_name}.")
    elif message.text.lower()=="kill":
        logging.critical(f"User {message.from_user.first_name} requested to kill the main process.")
        if check_health():
            pid = get_pid()
            if pid:
                try:
                    os.kill(pid,signal.SIGKILL)
                    bot.reply_to(message,f"✅ System killed!")
                    logging.info("Main process ahs been killed.")
                except ProcessLookupError:
                    print(f"No process found with PID {pid}")
                    bot.reply_to(message,f"🚨 Couldn't Find Process PID during killing! While we detected the system is ON! Open Terminal 🛠️")
                    logging.error(f"Couldn't Find Process PID during killing! While we detected the system is ON!")
                except Exception as e:
                    print(f"Error killing process: {e}")
                    bot.reply_to(message,f"🚨 FAILURE TO KILL PROCESS!\n⚠️ Error : {e}\n🛠️ Open Terminal!")
                    logging.error(f"FAILURE TO KILL PROCESS! Error : {e}")
            else:
                print("🚨 PID returned is 0, meaning we couldn't find script running on first row of PS!")
                logging.critical("PID returned is 0, meaning we couldn't find script running on first row of PS!")
                bot.reply_to(message,f"🚨 PID returned is 0, meaning we couldn't find script running on first row of PS!")
        else:
            print("🚨 System is not online!")
            logging.info("System is not online. thus cannot be killed.")
            bot.reply_to(message,"🚨 System is not online!")
    elif message.text.lower()=="start":
        logging.info(f"User {message.from_user.first_name} requested to start the main process.")
        if check_health():
            bot.reply_to(message,"🚨 System is already online!")
            logging.info(f"System is already online, skipping...")
        else:
            if start_server():
                bot.reply_to(message,"Server is starting..⌛")
                logging.info(f"Server process started!")
            else:
                bot.reply_to(message,"🚨 Failed to start server!")
    elif message.text.lower()=="db":
        logging.info(f"User {message.from_user.first_name} requested to access database.")
        with open(DB_FILE,"rb") as f:
            bot.send_document(TEL_ID,f, caption="Here's your Database file!")
    elif message.text.lower()=="log":
        logging.info(f"User {message.from_user.first_name} requested to access logs.")
        with open(LOG_FILE,"rb") as f:
            bot.send_document(TEL_ID,f, caption="Here's your Log file!")
    elif message.text.lower()=="help" or message.text.lower()=="cmds":
        logging.info(f"User {message.from_user.first_name} requested help with commands.")
        bot.reply_to(message, 
             "🤖 Health: Checks on the main program's execution state. 💓\n"
             "ℹ️ Info: Gives general info on the project alongside health status. 📊\n"
             "💀 Kill: Kills the main program. ☠️\n"
             "🚀 Start: Starts the main program. ✨\n"
             "💾 DB: Sends the database file. 📁\n"
             "⏰ Now: Shows currently available offers. 🏡"
            )

    elif message.text.lower()=="now":
        logging.info(f"User {message.from_user.first_name} requested to show availablities now, signaling to second process...")
        if check_health():
            try:
                os.kill(get_pid(),signal.SIGUSR1)
                bot.reply_to(message,"Getting you that list!...⌛")
            except Exception as e:
                logging.error(f"Error occurred whiel trying to signal main process : {e}")
                bot.reply_to(message,"🚨 Failed to signal to the main process! Try later!")
        else:
            logging.error("System is not online, thus cannot be signaled, informing user to start it first..")
            bot.reply_to(message,"🚨 System is not online! Please start it first!")
# Start listening for messages
logging.info("Telegram bot started.")
bot.polling()