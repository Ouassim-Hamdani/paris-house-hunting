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