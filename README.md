# Telegram Ad Submission & Approval Bot

This is a Python-based Telegram bot designed to automate the process of receiving, managing, and publishing advertisements to a designated channel. It provides a full workflow for users to submit ads and for an administrator to approve them.

---

## Features

-   **Membership Check**: Restricts ad submission to members of a specific Telegram channel.
-   **Guided Conversation**: Uses a step-by-step conversation to guide users through the ad submission process (Rules -> Menu -> Content -> Payment).
-   **Admin Approval Workflow**: Forwards all submitted ads and payment receipts to an admin for review. The admin can approve or ignore submissions.
-   **One-Click Publishing**: Admins can approve and post an ad to the channel with a single button click.
-   **Automated Signatures**: Automatically appends the submitting user's username and the channel's ID to every published ad.
-   **User Notifications**: Informs users automatically when their ad has been successfully published.

---

## Setup & Installation

Follow these steps to get the bot running on your own system.

### 1. Prerequisites

-   Python 3.8 or higher.
-   A Telegram Bot Token obtained from [@BotFather](https://t.me/BotFather).
-   The username of the public Telegram channel where ads will be posted.
-   Your personal Telegram User ID for receiving admin notifications (you can get this from [@userinfobot](https://t.me/userinfobot)).

### 2. Configure Environment Variables

The bot's configuration is managed through an `.env` file.

1.  Create a file named `.env` in the root directory of the project.
2.  Copy the contents of `.env.example` into your new `.env` file.
3.  Fill in the values for each variable.

### 3. Install Dependencies

Install the required Python libraries using pip:

```bash
pip install python-telegram-bot python-dotenv
```

### 4. Run the Bot

Start the bot by running the main Python script:

```bash
python main.py
```

The bot will start polling for new messages.

---

## How It Works

1.  A user starts a conversation with the bot using the `/start` command.
2.  The bot checks if the user is a member of the target channel. If not, it prompts them to join.
3.  Once membership is confirmed, the user must agree to a set of rules.
4.  The user selects an ad type and submits their ad content (text or photo) and a payment receipt.
5.  The complete submission (ad content, user info, payment receipt) is forwarded to the `ADMIN_ID`. This message includes an **"Approve & Post Ad"** button.
6.  When the admin clicks the approval button, the bot automatically:
    -   Posts the ad content to the `CHANNEL_USERNAME` channel.
    -   Appends the submitter's username and the channel's handle to the post.
    -   Sends a confirmation message to the original user, informing them their ad is live.
    -   Updates the admin's message to show that the ad has been approved.
