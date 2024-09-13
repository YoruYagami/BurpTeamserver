# BurpTeamserver

**BurpTeamserver** is a Burp Suite extension that integrates real-time team chat via Telegram, enhancing collaboration during security testing. Enjoy a seamless messaging experience directly within Burp with a modern, dark-themed UI.

## Features

- **Real-Time Chat:** Communicate with your team without leaving Burp Suite.
- **Telegram Integration:** Leverage Telegram's messaging platform for reliable communication.
- **Modern Dark UI:** Interface aligns with Burp's dark theme for consistency.
- **Markdown Support:** Format messages with bold, italic, and code snippets.
- **Resizable Input Area:** Adjust the chat input area's size by dragging its top edge.
- **Notifications:** Receive alerts for new messages when the chat tab is inactive.
- **Clear Chat:** Easily reset the chat history.

## Installation

1. **Download the Extension:**
   ```bash
   git clone https://github.com/YoruYagami/BurpTeamserver.git
   ```
2. **Load into Burp Suite:**
- Open Burp Suite.
- Go to the Extender tab.
- Click on Extensions.
- Click Add and select Python.
- Browse and select BurpTeamserver.py.
- Click Next and Finish.

## Configuration

1. Set Up Telegram Bot:
- Create a Bot:
    - Open Telegram and chat with BotFather.
    - Send /newbot and follow instructions to get your Bot Token.
-  Get Chat ID:
    - Add the bot to your Telegram group/channel.
    - Send a message in the group/channel.
    - Visit https://api.telegram.org/bot<YourBOTToken>/getUpdates and find your Chat ID.
2. Configure BurpTeamserver:
- Navigate to the Settings tab in BurpTeamserver.
- Enter your Display Name.
- Choose your Message Color.
- Input your Bot Token and Chat ID.
- Click Save Profile and then Connect.

## License
This project is licensed under the MIT License.
