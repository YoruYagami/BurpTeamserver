from burp import IBurpExtender, ITab
from java.awt import BorderLayout, GridBagLayout, GridBagConstraints, Insets, Dimension, Color, Font
from java.awt.event import KeyAdapter, KeyEvent
from javax.swing import (
    JPanel, JLabel, JTextField, JButton, JScrollPane,
    SwingUtilities, JOptionPane, JTabbedPane, JColorChooser, JTextPane, JTextArea, BorderFactory, JSplitPane
)
from javax.swing.border import LineBorder
from javax.swing.text import Style, StyleConstants, StyledDocument
from java.lang import Object
from java.io import BufferedReader, InputStreamReader, OutputStreamWriter
from java.net import URL
import threading
import json
import time
from datetime import datetime
import re

class BurpExtender(IBurpExtender, ITab):
    def registerExtenderCallbacks(self, callbacks):
        # Initialize extension
        self.callbacks = callbacks
        self.helpers = callbacks.getHelpers()
        self.callbacks.setExtensionName("Modern Team Chat")
        
        # Initialize variables
        self.bot_token = ""
        self.chat_id = ""
        self.is_connected = False
        self.last_update_id = 0
        self.user_name = "User"
        self.user_color = "#007bff"
        self.unread_messages = 0
        
        # Load saved settings
        self.loadSettings()
        
        # Create UI components
        self.createUI()
        
        # Add as a new tab in Burp Suite
        callbacks.addSuiteTab(self)
        
        # Start message receiving thread if already connected
        if self.bot_token and self.chat_id and self.user_name:
            self.is_connected = True
            self.appendChatMessage("Connected to Telegram.", "System", "#28a745", "")
            t = threading.Thread(target=self.receiveMessages)
            t.setDaemon(True)  # Set the thread as a daemon
            t.start()
    
    def createUI(self):
        # Main panel with tabs
        self.main_panel = JTabbedPane()
        
        # Settings Tab
        self.settings_panel = JPanel(GridBagLayout())
        gbc = GridBagConstraints()
        gbc.insets = Insets(10, 10, 10, 10)
        gbc.fill = GridBagConstraints.HORIZONTAL
        
        # Display Name Field
        gbc.gridx = 0
        gbc.gridy = 0
        self.settings_panel.add(JLabel("Display Name:"), gbc)
        gbc.gridx = 1
        self.name_field = JTextField(20)
        self.name_field.setText(self.user_name)
        self.settings_panel.add(self.name_field, gbc)
        
        # Message Color Picker
        gbc.gridx = 0
        gbc.gridy = 1
        self.settings_panel.add(JLabel("Message Color:"), gbc)
        gbc.gridx = 1
        self.color_button = JButton("Choose Color", actionPerformed=self.chooseColor)
        self.settings_panel.add(self.color_button, gbc)
        self.color_preview = JPanel()
        self.color_preview.setBackground(Color.decode(self.user_color))
        self.color_preview.setPreferredSize(Dimension(50, 25))
        gbc.gridx = 2
        self.settings_panel.add(self.color_preview, gbc)
        
        # Bot Token Field
        gbc.gridx = 0
        gbc.gridy = 2
        self.settings_panel.add(JLabel("Bot Token:"), gbc)
        gbc.gridx = 1
        self.token_field = JTextField(20)
        self.token_field.setText(self.bot_token)
        self.settings_panel.add(self.token_field, gbc)
        
        # Chat ID Field
        gbc.gridx = 0
        gbc.gridy = 3
        self.settings_panel.add(JLabel("Chat ID:"), gbc)
        gbc.gridx = 1
        self.chat_id_field = JTextField(20)
        self.chat_id_field.setText(self.chat_id)
        self.settings_panel.add(self.chat_id_field, gbc)
        
        # Save Profile Button
        gbc.gridx = 0
        gbc.gridy = 4
        self.save_button = JButton("Save Profile", actionPerformed=self.saveProfile)
        self.settings_panel.add(self.save_button, gbc)
        
        # Connect Button
        gbc.gridx = 1
        self.connect_button = JButton("Connect", actionPerformed=self.connectToTelegram)
        self.settings_panel.add(self.connect_button, gbc)
        
        # Clear Chat Button
        gbc.gridx = 2
        self.clear_chat_button = JButton("Clear Chat", actionPerformed=self.clearChat)
        self.settings_panel.add(self.clear_chat_button, gbc)
        
        # Chat Tab
        self.chat_panel = JPanel(BorderLayout())
        
        # Chat Display Area
        self.chat_area = JTextPane()
        self.chat_area.setEditable(False)
        self.chat_area.setBorder(LineBorder(Color.LIGHT_GRAY, 1))
        self.chat_area.setFont(Font("Segoe UI", Font.PLAIN, 14))
        self.chat_area.setBackground(Color.DARK_GRAY)
        self.chat_area.setForeground(Color.WHITE)
        self.chat_area.setContentType("text/html")
        self.chat_area.setText("<html><body style='font-family:Segoe UI; font-size:14px;'></body></html>")
        
        # Scroll Pane for Chat Display
        self.chat_scroll = JScrollPane(self.chat_area)
        self.chat_scroll.setVerticalScrollBarPolicy(JScrollPane.VERTICAL_SCROLLBAR_ALWAYS)
        self.chat_scroll.setBorder(LineBorder(Color.LIGHT_GRAY, 1))
        
        # Chat Input Area - JTextArea for multiline support
        self.chat_input = JTextArea(3, 50)
        self.chat_input.setFont(Font("Segoe UI", Font.PLAIN, 14))
        self.chat_input.setLineWrap(True)
        self.chat_input.setWrapStyleWord(True)
        self.chat_input.setBorder(LineBorder(Color.LIGHT_GRAY, 1))
        self.chat_input.setBackground(Color.DARK_GRAY)
        self.chat_input.setForeground(Color.WHITE)
        self.chat_input.addKeyListener(KeyListenerImpl(self))
        
        # Scroll Pane for Chat Input
        self.chat_input_scroll = JScrollPane(self.chat_input)
        self.chat_input_scroll.setVerticalScrollBarPolicy(JScrollPane.VERTICAL_SCROLLBAR_AS_NEEDED)
        self.chat_input_scroll.setPreferredSize(Dimension(0, 60))
        
        # Send Button
        self.send_button = JButton("Send", actionPerformed=lambda e: self.sendMessage())
        self.send_button.setBackground(Color.decode("#007bff"))
        self.send_button.setForeground(Color.WHITE)
        self.send_button.setFont(Font("Segoe UI", Font.BOLD, 14))
        self.send_button.setFocusPainted(False)
        self.send_button.setBorder(BorderFactory.createEmptyBorder(5, 15, 5, 15))
        
        # Chat Input Panel
        self.chat_input_panel = JPanel(BorderLayout())
        self.chat_input_panel.add(self.chat_input_scroll, BorderLayout.CENTER)
        self.chat_input_panel.add(self.send_button, BorderLayout.EAST)
        
        # JSplitPane to make chat input area resizable by dragging its top edge
        self.split_pane = JSplitPane(JSplitPane.VERTICAL_SPLIT, self.chat_scroll, self.chat_input_panel)
        self.split_pane.setResizeWeight(1.0)
        self.split_pane.setOneTouchExpandable(True)
        self.split_pane.setDividerSize(5)
        self.split_pane.setDividerLocation(400)
        
        # Add JSplitPane to Chat Panel
        self.chat_panel.add(self.split_pane, BorderLayout.CENTER)
        
        # Add tabs to Main Panel
        self.main_panel.addTab("Settings", self.settings_panel)
        self.main_panel.addTab("Chat", self.chat_panel)
        
        # Add main panel to Burp Suite
        self.callbacks.customizeUiComponent(self.main_panel)
        
        # Add ChangeListener to handle tab selection for notifications
        self.main_panel.addChangeListener(self.tabChanged)
        self.current_tab = "Settings"
    
    def chooseColor(self, event):
        # Open color chooser dialog
        color = JColorChooser.showDialog(None, "Choose Message Color", Color.decode(self.user_color))
        if color:
            self.user_color = '#{:02x}{:02x}{:02x}'.format(color.getRed(), color.getGreen(), color.getBlue())
            self.color_preview.setBackground(color)
    
    def saveProfile(self, event):
        # Save profile settings
        self.user_name = self.name_field.getText().strip()
        self.bot_token = self.token_field.getText().strip()
        self.chat_id = self.chat_id_field.getText().strip()
        
        # Save settings using Burp's extension settings
        self.callbacks.saveExtensionSetting("user_name", self.user_name)
        self.callbacks.saveExtensionSetting("bot_token", self.bot_token)
        self.callbacks.saveExtensionSetting("chat_id", self.chat_id)
        self.callbacks.saveExtensionSetting("user_color", self.user_color)
        
        # Provide feedback to the user
        JOptionPane.showMessageDialog(None, "Profile saved successfully.", "Success", JOptionPane.INFORMATION_MESSAGE)
    
    def loadSettings(self):
        # Load saved settings
        self.user_name = self.callbacks.loadExtensionSetting("user_name")
        if self.user_name is None:
            self.user_name = "User"
        
        self.bot_token = self.callbacks.loadExtensionSetting("bot_token")
        if self.bot_token is None:
            self.bot_token = ""
        
        self.chat_id = self.callbacks.loadExtensionSetting("chat_id")
        if self.chat_id is None:
            self.chat_id = ""
        
        self.user_color = self.callbacks.loadExtensionSetting("user_color")
        if self.user_color is None:
            self.user_color = "#007bff"
    
    def connectToTelegram(self, event):
        # Update settings from fields
        self.user_name = self.name_field.getText().strip()
        self.bot_token = self.token_field.getText().strip()
        self.chat_id = self.chat_id_field.getText().strip()
        
        if self.user_name and self.bot_token and self.chat_id:
            if not self.is_connected:
                self.is_connected = True
                self.appendChatMessage("Connected to Telegram.", "System", "#28a745", "")
                # Start a thread to listen for incoming messages
                t = threading.Thread(target=self.receiveMessages)
                t.setDaemon(True)  # Set the thread as a daemon
                t.start()
            else:
                JOptionPane.showMessageDialog(None, "Already connected to Telegram.", "Info", JOptionPane.INFORMATION_MESSAGE)
        else:
            JOptionPane.showMessageDialog(None, "Please enter Display Name, Bot Token, and Chat ID.", "Error", JOptionPane.ERROR_MESSAGE)
    
    def clearChat(self, event):
        # Clear the chat area
        self.chat_area.setText("<html><body style='font-family:Segoe UI; font-size:14px;'></body></html>")
        self.unread_messages = 0
        self.updateTabTitle()
    
    def sendMessage(self):
        message = self.chat_input.getText().strip()
        if message:
            if self.is_connected:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                full_message = "[{}] [{}]: {}".format(timestamp, self.user_name, message)
                self.sendTelegramMessage(full_message)
                self.appendChatMessage(message, self.user_name, self.user_color, timestamp)
                self.chat_input.setText("")
            else:
                self.appendChatMessage("Not connected. Please configure your profile.", "System", "#dc3545", "")
    
    def sendTelegramMessage(self, message):
        try:
            url = URL("https://api.telegram.org/bot{}/sendMessage".format(self.bot_token))
            conn = url.openConnection()
            conn.setDoOutput(True)
            conn.setRequestMethod("POST")
            conn.setRequestProperty("Content-Type", "application/json; charset=utf-8")
            
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            out = OutputStreamWriter(conn.getOutputStream(), "UTF-8")
            out.write(json.dumps(data))
            out.close()
            
            response_code = conn.getResponseCode()
            if response_code != 200:
                self.appendChatMessage("Failed to send message. Response code: {}".format(response_code), "System", "#dc3545", "")
        except Exception as e:
            self.appendChatMessage("Error sending message: {}".format(e), "System", "#dc3545", "")
    
    def receiveMessages(self):
        while self.is_connected:
            try:
                url = URL("https://api.telegram.org/bot{}/getUpdates?offset={}".format(self.bot_token, self.last_update_id + 1))
                conn = url.openConnection()
                conn.setRequestMethod("GET")
                
                reader = BufferedReader(InputStreamReader(conn.getInputStream(), "UTF-8"))
                response = ""
                line = reader.readLine()
                while line is not None:
                    response += line
                    line = reader.readLine()
                reader.close()
                
                updates = json.loads(response)
                for result in updates.get("result", []):
                    self.last_update_id = result["update_id"]
                    message = result.get("message", {})
                    if str(message.get("chat", {}).get("id", "")) == self.chat_id:
                        text = message.get("text", "")
                        sender_info = message.get("from", {})
                        sender = sender_info.get("first_name", "Unknown")
                        if text:
                            # Ignore messages sent by self to prevent duplication
                            if sender == self.user_name:
                                continue
                            self.appendChatMessage(text, sender, "#17a2b8", "")
                time.sleep(2)
            except Exception as e:
                self.appendChatMessage("Error receiving messages: {}".format(e), "System", "#dc3545", "")
                self.is_connected = False
    
    def appendChatMessage(self, message, sender, color_hex, timestamp):
        def updateChat():
            try:
                # Ensure content type is HTML
                if self.chat_area.getContentType() != "text/html":
                    self.chat_area.setContentType("text/html")
                
                # Apply Markdown parsing
                formatted_message = self.parseMarkdown(message)
                
                # Create HTML for the message
                if timestamp:
                    full_message = "<p style='color:{};'><strong>[{}] {}:</strong> {}</p>".format(color_hex, timestamp, sender, formatted_message)
                else:
                    full_message = "<p style='color:{};'><strong>{}:</strong> {}</p>".format(color_hex, sender, formatted_message)
                
                # Insert the message before the closing </body> tag
                current_text = self.chat_area.getText()
                insert_position = current_text.rfind("</body>")
                if insert_position != -1:
                    new_text = current_text[:insert_position] + full_message + current_text[insert_position:]
                    self.chat_area.setText(new_text)
                
                # Update notifications if chat tab is not active and sender is not system
                if self.main_panel.getSelectedComponent() != self.chat_panel and sender != "System":
                    self.unread_messages += 1
                    self.updateTabTitle()
                
                # Scroll to the bottom
                self.chat_area.setCaretPosition(self.chat_area.getDocument().getLength())
            except Exception as e:
                print("Error updating chat area: {}".format(e))
        SwingUtilities.invokeLater(updateChat)
    
    def parseMarkdown(self, text):
        """
        Parse basic Markdown syntax and convert to HTML.
        Supports:
        - **bold**
        - *italic*
        - ```code```
        """
        # Escape HTML special characters
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        # Handle code snippets: ```code```
        code_pattern = re.compile(r'```(.*?)```', re.DOTALL)
        text = code_pattern.sub(r'<pre style="background-color:#2d2d2d;padding:10px;border-radius:5px;color:#ffffff;">\1</pre>', text)
        
        # Bold: **text**
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        
        # Italic: *text*
        text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
        
        return text
    
    def updateTabTitle(self):
        if self.unread_messages > 0:
            self.main_panel.setTitleAt(1, "Chat (*)")
        else:
            self.main_panel.setTitleAt(1, "Chat")
    
    def tabChanged(self, event):
        selected_index = self.main_panel.getSelectedIndex()
        selected_component = self.main_panel.getSelectedComponent()
        if selected_component == self.chat_panel:
            # Reset unread messages
            self.unread_messages = 0
            self.updateTabTitle()
    
    def getTabCaption(self):
        return "Team Chat"
    
    def getUiComponent(self):
        return self.main_panel

class KeyListenerImpl(KeyAdapter):
    def __init__(self, extender):
        self.extender = extender
    
    def keyPressed(self, event):
        # Check if Shift+Enter is pressed
        if event.getKeyCode() == KeyEvent.VK_ENTER and event.isShiftDown():
            # Insert newline in the chat input
            current_text = self.extender.chat_input.getText()
            cursor_pos = self.extender.chat_input.getCaretPosition()
            new_text = current_text[:cursor_pos] + "\n" + current_text[cursor_pos:]
            self.extender.chat_input.setText(new_text)
            self.extender.chat_input.setCaretPosition(cursor_pos + 1)
            event.consume()
        elif event.getKeyCode() == KeyEvent.VK_ENTER and not event.isShiftDown():
            # Send message on Enter
            self.extender.sendMessage()
            event.consume()
