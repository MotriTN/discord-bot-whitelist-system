<div align="center">
  <h1>🛡️ Lineage Protocol</h1>
  <p><b>A sophisticated Discord bot for managing trust networks, reputation, and daily accountability.</b></p>
</div>

---

## 📖 Overview

The **Lineage Protocol** is an advanced moderation, reputation, and accountability framework built for Discord servers. Unlike standard moderation bots, Lineage decentralizes authority by allowing members to **Trust** or **Report** each other using a monthly quota system. It features automated role management based on community consensus, private network capabilities, and a private, self-accountability engine for daily goal setting.

## ✨ Core Features

*   **⚖️ Decentralized Reputation System:** Members have a strictly enforced quota of 2 Trusts and 2 Reports per month (resetting on the 1st of every month).
*   **🌟 Automated Whitelisting/Blacklisting:** Once a member receives trusts from 2 unique people, they are automatically granted the `@Whitelisted` role. Two active reports banish them to the `@Blacklisted` role. The bot creates these roles automatically.
*   **🏰 Private Sanctuaries:** Whitelisted members can summon a completely hidden, private category and channel that automatically grants access *only* to the members they have explicitly trusted.
*   **📈 Daily Accountability Engine:** Members can submit a private daily strategic plan (`/plan`). The next day, they can review their progress (`/review`) to build their **Aura** score and public victory streaks.
*   **🛡️ Admin God-Mode:** Administrators can force-whitelist or blacklist users. "Sins of the Brother" alerts notify admins of exactly who trusted a user that gets forcefully blacklisted.

---

## 🛠️ Setup & Installation Guide

To run the Lineage Protocol on your own server, follow these exact steps to configure your environment and Discord Bot settings.

### 1. Discord Developer Portal Configuration

Before touching the code, you need to create a bot user and configure its permissions:

1.  Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2.  Click **New Application** and give your bot a name.
3.  Navigate to the **Bot** tab on the left sidebar:
    *   Click **Reset Token** to get your bot's token. **Copy this and keep it secret.**
    *   Scroll down to **Privileged Gateway Intents**.
    *   ✅ **CRITICAL:** Toggle **Server Members Intent** to ON. The bot *will crash* without this enabled, as it needs to see member roles and profiles.
4.  Navigate to the **OAuth2 > URL Generator** tab:
    *   Under Scopes, check `bot` and `applications.commands`.
    *   Under Bot Permissions, check `Administrator` (or explicitly grant Manage Roles, Manage Channels, Read Messages/View Channels, Send Messages).
    *   Copy the generated URL at the bottom and paste it into your browser to invite the bot to your server.

### 2. Environment Variables (`.env` Setup)

In the root folder of the project, create a file named exactly `.env`. Do not include any file extension. Paste the following template and fill in your specific IDs:

```env
# Your secret bot token from the Discord Developer Portal
DISCORD_TOKEN=your_bot_token_here

# Your Server's ID. Enables instant slash command syncing for testing
GUILD_ID=123456789012345678

# The ID of the private admin channel where Report and Blacklist alerts are sent
ADMIN_CHANNEL_ID=123456789012345678

# The ID of the public channel where Daily Plan Reviews (Victories/Defeats) are posted
DAILY_LOG_CHANNEL_ID=123456789012345678

# Database connection string (Leave as default SQLite for local hosting)
DATABASE_URL=sqlite:///lineage.db
```

*To get a Channel or Server ID, open Discord Settings > Advanced > Enable "Developer Mode". Then right-click a channel or your server name and select "Copy ID".*

### 3. Local Installation

Ensure you have **Python 3.10+** installed on your machine.

1.  Clone or download this repository.
2.  Open a terminal in the project directory.
3.  Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Launch the bot:
    ```bash
    python main.py
    ```

The bot will automatically generate the SQLite database (`lineage.db`) on its first run and sync the slash commands to your server instantly!

---

## 🤖 Command Glossary

### Reputation Commands
*   `/trust @user` - Grant your trust to a member (Costs 1 Trust Charge).
*   `/untrust @user` - Revoke your trust specifically from a member.
*   `/untrust_all` - Instantly revoke all your active trust bonds.
*   `/report @user [reason]` - File a report against a member (Costs 1 Report Charge). Sends an alert to admins.
*   `/forgive @user` - Retract a report you filed against someone.

### Audits & Networks
*   `/identity [@user]` - View a member's Protocol Profile (Status, their trustees, their trusters, and your remaining monthly quotas).
*   `/sanctuary` - (Whitelisted Only) Creates a private channel exclusively for you and your trusted members.

### Accountability Engine
*   `/plan` - Opens a private Modal to declare your Primary Objective and Self-Correction Habit for the day.
*   `/review` - Sends a private prompt to review your most recent plan. Clicking Victory or Defeat logs the result in the `DAILY_LOG_CHANNEL_ID` and updates your Aura/Streak.

### Administrator Commands
*   `/whitelist @user` - Bypass quota thresholds and grant Whitelisted status instantly.
*   `/blacklist @user` - Permanently banish a member. Triggers an audit of all the members who trusted them.

---

## ⚙️ Tech Stack

*   **Language:** Python 3.10+
*   **Library:** [Disnake](https://disnake.dev/) (A fast modern Discord API wrapper)
*   **Database:** SQLAlchemy (ORM) + SQLite
*   **Scheduling:** Croniter (For the monthly quota reset task)
