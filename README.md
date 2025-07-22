# 🏠 Paris House Hunting

This project is a Python-based automated housing availability checker, for students in Paris, since it is so hard. It scrapes various housing websites, checks for available properties in specified residences, and sends notifications via a Telegram bot.

## ✨ Features

- **🤖 Automated Checking:** Periodically checks for housing availability on multiple platforms.
- **🌐 Multi-Platform Support:** Scrapes CROUS, Studefi, ARPEJ, and Fac-Habitat.
- **📢 Telegram Notifications:** Sends real-time notifications to users about new housing opportunities.
- **🔧 Customizable:** Users can configure the residences to be checked and other parameters.
- **❤️ Health Monitoring:** Includes a health check script to monitor the main application's status.

## Project Structure

```
.
├── data/
│   ├── database.csv
│   └── users.csv
├── housing/
│   ├── __init__.py
│   ├── checkers.py
│   ├── constants.py
│   └── utils.py
├── logs/
│   └── main.log
├── .env
├── .gitignore
├── health.py
├── main.py
├── Makefile
├── requirements.txt
└── README.md
```

- **`main.py`**: The main script that runs the housing check loop.
- **`health.py`**: A script to monitor the health of the main application.
- **`Makefile`**: Contains commands for running the application.
- **`requirements.txt`**: Project dependencies.
- **`housing/`**: Directory containing the core logic for checking housing.
  - **`checkers.py`**: Functions for scraping each housing website.
  - **`constants.py`**: Constants and configuration, such as the list of residences to check.
  - **`utils.py`**: Utility functions for CSV handling and time checks.
- **`data/`**: Directory for data files.
  - **`database.csv`**: Stores a history of notifications sent.
  - **`users.csv`**: A list of users to be notified.
- **`logs/`**: Directory for log files.

## 🚀 How to Deploy

### 1. Environment Setup

1.  **Create a virtual environment**:
    ```bash
    python3 -m venv .venv
    ```

2.  **Activate the virtual environment**:

    ```bash
    source .venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

### 2. Telegram Bot Setup

1.  **Create a Telegram Bot**:
    -   Talk to the [BotFather](https://t.me/BotFather) on Telegram.
    -   Use the `/newbot` command to create a new bot.
    -   Give your bot a name and a username.
    -   The BotFather will give you a **token**.

2.  **Set up the `.env` file**:
    -   Create a file named `.env` in the root of the project.
    -   Add your Telegram bot token to this file:
        ```
        BOT=YOUR_TELEGRAM_BOT_TOKEN
        DB="data/database.csv"
        USER_DB="data/users.csv"
        PIPE_FILE="data/pipe_communication"
        ```

### 3. Configuration

-   **Residences**: You can customize which residences are checked by modifying the lists in `housing/constants.py`.
    -   For ARPEJ and Fac-Habitat, you can add or remove residences from the `ARPEJ_RES` and `FAC_HAB_RES` lists.
-   **CROUS Map**: The area for CROUS housing is determined by the URL in the `check_crous_housing` function in `housing/checkers.py`. You can modify this URL to scan a different area.
-   **Studefi**: All Studefi residences are checked by default.

## ▶️ Running the Application

You can use the `Makefile` to run the application.

-   **Run the main application**:
    ```bash
    make run
    ```
    This will start the `main.py` script in the background.

-   **Run the health check**:
    ```bash
    make health
    ```
    This will start the `health.py` script in the background.

-   **Run both**:
    ```bash
    make all
    ```

-   **Check running processes**:
    ```bash
    make check
    ```

Alternatively, you can run the scripts directly:

```bash
python3 main.py
python3 health.py
```

## 🤖 Usage

Interact with the bot on Telegram using the following commands:

| Command     | Description                                      |
|-------------|--------------------------------------------------|
| `Register *password*`  | Register to receive housing notifications, password in code :3       |
| `Health`    | Check the current status of the system.          |
| `Info`      | Get information about the bot and the system.    |
| `Notify`        | Turn on your notifications.                      |
| `Unnotify`       | Turn off your notifications.                     |
| `Help`      | Display the list of available commands.          |
| `Now`      | Display current real time available offers.          |



### 👑 Admin Commands

| Command     | Description                                      |
|-------------|--------------------------------------------------|
| `start`     | Start the housing check service.                 |
| `kill`      | Stop the housing check service.                  |
| `DB`      | Return Database history of offers found.          |
| `Log`      | Return Main log tracing.        |


## ⚠️ Warning

This application is designed to run on **Unix-based operating systems** (such as Linux or macOS). It relies on specific kernel commands for its operation, and a native Windows implementation has not been developed.

For continuous 24/7 monitoring, it is highly recommended to deploy this script on a server rather than running it on a local machine.

If you need to run this application on a Windows machine, you should use the **Windows Subsystem for Linux (WSL)**.





---
🦸 Created by a fellow Paris House Hunter Student **Ouassim Hamdani**.
