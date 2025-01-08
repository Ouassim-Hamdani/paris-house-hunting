import csv
from datetime import datetime, timedelta

def read_notifications_from_csv(CSV_FILE):
    """Reads notification data from the CSV file."""
    try:
        with open(CSV_FILE, 'r',encoding="utf8",newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            return list(reader)
    except FileNotFoundError:
        #logging.warning("Database File was not found, returning empty list of notifications in read_notifications_from_csv()")
        return []  

def write_notifications_to_csv(notifications,CSV_FILE):
    """Writes notification data to the CSV file."""
    with open(CSV_FILE, 'w',encoding="utf8",newline="") as csvfile:
        fieldnames = ['RESIDENCE', 'ADDRESS', 'SOURCE','NOTIFICATION']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(notifications)
        
def has_time_passed(last_notification_time_str, threshold_hours=24):
    """
    Compares the given timestamp string with the current time 
    and returns True if more than threshold_hours have passed 
    since the last notification.
    """
    last_notification_time = datetime.strptime(
        last_notification_time_str, "%Y-%m-%d %H:%M"
    )
    time_difference = datetime.now() - last_notification_time
    return time_difference > timedelta(hours=threshold_hours)



def load_users(USER_DB):
    """
    Loads user data from the CSV database.
    Returns a dictionary where keys are user IDs and 
    values are dictionaries with 'username' and 'role'.
    """
    users = {}
    with open(USER_DB, 'r') as file:
        reader = csv.DictReader(file)  
        for row in reader:
            user_id = int(row['ID'])
            users[user_id] = {
                'username': row['USER'],
                'role': row['ROLE'],
                'notify':row['NOTIFY']=='True'
            }
    return users


def is_registered(user_id,USER_DB):
    """Checks if a user is registered in the database."""
    users = load_users(USER_DB)
    if isinstance(user_id,str):
        user_id=int(user_id)
    
    return user_id in users.keys()


def is_admin(user_id,USER_DB):
    users = load_users(USER_DB)
    if isinstance(user_id,str):
        user_id=int(user_id)
        
    if user_id in users.keys():
        return users[user_id]['role'].lower()=='admin'
    return False # user non existent



def save_users(users,USER_DB):
    """
    Saves user data to the CSV database.
    Expects 'users' to be a dictionary where keys are user IDs and 
    values are dictionaries with 'username' and 'role'.
    """
    with open(USER_DB, 'w',newline='') as file:
        fieldnames = ['USER', 'ID', 'ROLE','NOTIFY']  # Define the header row
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()  # Write the header row
        for user_id, user_data in users.items():
            writer.writerow({
                'USER': user_data['username'],
                'ID': user_id,
                'ROLE': user_data['role'],
                'NOTIFY':str(user_data['notify'])
            })
            
            
            
def register_user(USER_DB,user_id, username,role="Member"):
    """Adds a new user to the database."""
    users = load_users(USER_DB)
    if isinstance(user_id,str):
        user_id=int(user_id)
    users[user_id] = {"username":username,"role":role,'notify':True}
    save_users(users,USER_DB)
    
    
def check_notify(user_id,USER_DB):
    if isinstance(user_id,str):
        user_id=int(user_id)
    if is_registered(user_id,USER_DB):
        users = load_users(USER_DB)
        return users[user_id]["notify"]
    else:
        raise ValueError("User does not exist in database.")
def switch_notify(user_id,USER_DB):
    if isinstance(user_id,str):
        user_id=int(user_id)
    if is_registered(user_id,USER_DB):
        users = load_users(USER_DB)
        print(users[user_id])
        users[user_id]["notify"] =  not users[user_id]["notify"]
        save_users(users,USER_DB)
    else:
        raise ValueError("User does not exist in database.")