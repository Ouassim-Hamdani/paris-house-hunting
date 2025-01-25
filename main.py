import requests,csv,os,telegram,asyncio
from bs4 import BeautifulSoup
from time import sleep
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging,signal,multiprocessing
from housing.checkers import check_all_res
from housing.utils import write_notifications_to_csv,read_notifications_from_csv,has_time_passed,load_users
#Init variabes & logging & signaling

logging.basicConfig(filename=os.path.join("logs",'main.log'), level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',encoding="utf-8")

load_dotenv()

TEL_ID = "814952835" 
CSV_FILE=os.environ["DB"]
USERS_DB = os.environ["USER_DB"]
bot = telegram.Bot(token=os.environ["BOT"])



#SIGNAL SETUP
def handler(signum, frame):
    print(f"Received signal {signum}! Performing task of showing what's available ...")
    logging.info("Received signal {signum} from health.py! Performing task of showing what's available now ...")
    process = multiprocessing.Process(target=check_all_no_time_process)
    process.start()

signal.signal(signal.SIGUSR1,handler)

def check_all_no_time_process(): # we had to do this so we run it in a sperate process without awaiting, since runnign i nsame process was impsoibble due to async nature
    asyncio.run(check_all_no_time()) 
    

async def check_all_no_time(): # for secondary task, direct show
    with open(os.environ["PIPE_FILE"],"r") as f:
        user = f.read()
    logging.info(f"Task 2 requested by {user} : Checking for available hosuing options...")
    print("Task 2 : Checking...")
    housing_info = check_all_res()
    if len(housing_info)>0:
        print("Found housings!")
        logging.info("Found housing offers. Verifying...")
        for housing in housing_info:
            print(f"{housing["source"]} : Found {housing["name"]} at {housing["address"]}")
            logging.info(f"{housing["source"]} : Found {housing["name"]} at {housing["address"]}")
            await notify_user(housing,user)
    else:
        print("No offers.")
        await bot.send_message(chat_id=user, text="No housing offer is available!")
        logging.info("No Housing offers were found.")
# END OF SIGNAL SETUP


async def notify_check(housing_info):
    """
    Checks the CSV for previous notifications and sends a new 
    notification if conditions are met.
    """
    notifications = read_notifications_from_csv(CSV_FILE)
    updated_notifications = notifications.copy()

    for housing in housing_info:
        name = housing['name']
        address = housing['address']
        found = False
        print(f"{housing["source"]} : Found {name} at {address}")
        logging.info(f"{housing["source"]} : Found {name} at {address}")
        for i, notification in enumerate(notifications): # search in csv notifciations
            if notification['RESIDENCE'] == name:
                found = True
                last_notification_time = notification['NOTIFICATION']
                if has_time_passed(last_notification_time):
                    await notify(housing)
                    updated_notifications[i]['NOTIFICATION'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                break

        if not found:
            await notify(housing)
            updated_notifications.append({
                'RESIDENCE': name, 
                'ADDRESS': address, 
                'SOURCE':housing["source"],
                'NOTIFICATION': datetime.now().strftime("%Y-%m-%d %H:%M")
            })

    write_notifications_to_csv(updated_notifications,CSV_FILE)    


def create_message(housing_item):
    """Create Message dependin on source to send to user"""
    if housing_item["source"]=="Crous":
        message = f"🏢 Source : {housing_item["source"]}\n\n🏠 Residence : {housing_item["name"]}\n\n📍 Address : {housing_item["address"]}\n\n💰 Price : {housing_item["price"]}\n\n🧱 Size : {housing_item["size"]}\n\n🌐 Reserve it at {housing_item["URL"]}"
    elif housing_item["source"]=="Studefi":
        message = f"🏢 Source : {housing_item["source"]}\n\n🏠 Residence : {housing_item["name"]}\n\n🌐 Reserve it at https://www.studefi.fr/main.php#listRes"
    elif housing_item["source"]=="Arpej":
        message = f"🏢 Source : {housing_item["source"]}\n\n🏠 Residence : {housing_item["name"]}\n\n📍 Address : {housing_item["address"]}\n\n💰 Price : {housing_item["price"]}€\n\n🌐 Reserve it at {housing_item["URL"]}"
    elif housing_item["source"]=="Fac-Habitat":
        message = f"🏢 Source : {housing_item["source"]}\n\n🏠 Residence : {housing_item["name"]}\n\n📍 Address : {housing_item["address"]}\n\n🔓 Availability : {housing_item["state"]}\n\n🌐 Reserve it at {housing_item["URL"]}"
        
    return message
async def notify(housing_item): # dont be confused this als onotifies all users, just for housing offers
    
    message=create_message(housing_item)
    users = load_users(USERS_DB)
    if "image" in housing_item.keys():
        for user in users.keys():
            if users[user]["notify"]:
                await bot.send_photo(chat_id=user, photo=housing_item["image"],caption=message)
    else:
        for user in users.keys():
            if users[user]["notify"]:
                await bot.send_message(chat_id=user, text=message)
    print("Notification Sent!")
    logging.info("Notifying all users of previous offer.")
async def check_all():
    logging.info("Checking for available hosuing options...")
    print("Checking...")
    housing_info = check_all_res()
    if len(housing_info)>0:
        print("Found housings!")
        logging.info("Found housing offers. Verifying...")
        await notify_check(housing_info)
    else:
        print("No offers.")
        logging.info("No Housing offers were found.")

async def notify_user(housing_item,user):
    """For specific user, handles message creating and notifying, used in now task"""
    message=create_message(housing_item)
    if "image" in housing_item.keys():
                await bot.send_photo(chat_id=user, photo=housing_item["image"],caption=message)
    else:
                await bot.send_message(chat_id=user, text=message)
    print("Notification Sent!")
    logging.info("Notfied the user of previous offer.")
async def notify_all(msg,users_db=USERS_DB):
    users = load_users(USERS_DB)
    for user in users.keys():
        if users[user]['notify']:
            await bot.send_message(chat_id=user,text=msg)
async def main():
    await notify_all("System is Online 🚀!")
    logging.info("System Online, Notified All Users.")
    while 1:
        try:
            await check_all()
            sleep(5*60)
        except Exception as e:
            print(f"System encountered an error {e}\nNotifying Ouassim by Telegram!")
            logging.error(f"System encountered an error {e}")
            logging.critical("Will attept sleeping for 10 minutes then restarting process.")
            await notify_all(f"🚨 System down!\n🚧 Error : {e}\nWill attempt restarting after 10 minutes!")
            logging.warning("Users have been notified!")
            sleep(10*60)

if __name__ == "__main__":
    asyncio.run(main())    
