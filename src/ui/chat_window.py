import pyperclip
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QScrollBar, QMessageBox, QApplication, QSplitter, QProgressBar
)
from PyQt5.QtCore import Qt, QSettings, QPoint, QSize, QThread, pyqtSignal, QMetaObject
from PyQt5.QtGui import QTextCursor, QFont, QIcon
from typing import Optional

import sys
from pathlib import Path
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))
from src.utils.chat_history import ChatHistory
from src.utils.log_manager import LogManager
from src.utils.config_manager import ConfigManager
from src.utils.path_manager import get_assets_path

class ChatWindow(QMainWindow):
    def __init__(self, on_window_close_callback=None):
        """
        Initialize chat window
        """
        try:
            super().__init__()
            # Initialize logging first
            self._log_manager = LogManager.get_instance()
            self._log_manager.log_info("Initializing chat window")

            # Get required instances
            self._api_client = ConfigManager().get_instance().get_api_client()
            self._chat_history = ChatHistory.get_instance()
            self._chat_history.add_listener(self)
            self._last_loaded_index = 0  # Tracks how many messages have been loaded
            self._api_thread = None

            self._on_window_close_callback = on_window_close_callback

            # icon_path = get_assets_path() / 'Promptly.ico'
            # self.setWindowIcon(QIcon(str(icon_path)))

            self._waiting_for_response = False
            self._initialize_ui()
            self._restore_window_geometry()

            self._messages = None
            self._load_new_messages()   
        except Exception as e:
            self._log_manager.log_error(f"Failed to initialize chat window", error = e)
            raise

    def _initialize_ui(self):
        """
        Initialize the chat window UI
        """
        try:
            self.setWindowTitle("Promptly - Chat")
            self.setMinimumSize(300, 400)  # Set a minimum size for the window
            self.setMaximumSize(999, 1332) # Set a maximum size for the window

            # Main widget and layout
            central_widget = QWidget(self)
            main_layout = QVBoxLayout(central_widget)

            # Create a splitter for chat display and input area
            self._splitter = QSplitter(Qt.Vertical)

            # Chat display area
            self._chat_display = QTextEdit(self)
            self._chat_display.setReadOnly(True)
            self._chat_display.setVerticalScrollBar(QScrollBar())
            self._scrollbar = self._chat_display.verticalScrollBar()
            self._splitter.addWidget(self._chat_display)
            self._markdown_buffer = ""

            # Input area
            input_area = QWidget()
            input_layout = QHBoxLayout(input_area)
            self._user_input = QTextEdit(self)
            input_layout.addWidget(self._user_input)

            # Connect Enter key to sending messages
            self._user_input.installEventFilter(self)

            # Buttons
            button_layout = QVBoxLayout()
            self._send_button = QPushButton("Send", self)
            self._send_button.clicked.connect(self._handle_send_or_stop)
            button_layout.addWidget(self._send_button)

            self._clear_button = QPushButton("Clear History", self)
            self._clear_button.clicked.connect(self._clear_history)
            button_layout.addWidget(self._clear_button)

            self._copy_button = QPushButton("Copy Last Reply", self)
            self._copy_button.clicked.connect(self._copy_last_reply_to_clipboard)
            button_layout.addWidget(self._copy_button)

            input_layout.addLayout(button_layout)
            self._splitter.addWidget(input_area)
            self._splitter.setSizes([700, 100])  # Initial heights for chat display and input area
            main_layout.addWidget(self._splitter)

            # Add an indeterminate progress bar
            self._progress_bar = QProgressBar(self)
            self._progress_bar.setRange(0, 0)  # Indeterminate mode
            self._progress_bar.setVisible(False)  # Initially hidden
            main_layout.addWidget(self._progress_bar)

            # Set central widget and layout
            self.setCentralWidget(central_widget)
        except Exception as e:
            self._log_manager.log_error(f"Failed to initialize chat window: {e}")
            raise
    
    def _save_window_geometry(self):
        """
        Save window size and position
        """
        settings = QSettings("Promptly - Textprocessor", "Chat Window")
        settings.setValue("pos", self.pos())
        settings.setValue("size", self.size())
        settings.setValue("splitter_state", self._splitter.saveState())

    def _restore_window_geometry(self):
        """
        Restore window size and position
        """
        settings = QSettings("Promptly - Textprocessor", "Chat Window")
        self.move(settings.value("pos", QPoint(100, 100)))  # Default position if none saved
        self.resize(settings.value("size", QSize(600, 800)))  # Default size if none saved

        splitter_state = settings.value("splitter_state")
        
        if splitter_state:
            self._splitter.restoreState(splitter_state)

    def _adjust_ui_elements(self):
        """
        Adjust font sizes and button sizes dynamically
        """
        try:
            # Adjust font size based on screen resolution
            screen_geometry = QApplication.primaryScreen().availableGeometry()
            scaling_factor = screen_geometry.width() / 1920  # Base resolution: 1920px
            new_font_size = max(10, int(11 * scaling_factor))  # Ensure a minimum font size

            font = QFont('Aria', new_font_size)
            self._chat_display.setFont(font)
            self._user_input.setFont(font)

            # Adjust button sizes dynamically
            button_width = max(80, int(100 * scaling_factor))
            button_height = max(30, int(40 * scaling_factor))

            for button in [self._send_button, self._clear_button, self._copy_button]:
                button.setFixedSize(button_width, button_height)
                button.setFont(QFont('Arial', new_font_size-2))

        except Exception as e:
            self._log_manager.log_error(f"Failed to adjust UI elements: {e}")
    
    def clear(self):
        """Override the clear method to emit a signal"""
        self._last_loaded_index = 0
        super().clear()  # Call the original clear method

    def resizeEvent(self, event):
        """
        Adjust font size dynamically when resizing
        """
        super().resizeEvent(event)
        self._adjust_ui_elements()

    def eventFilter(self, source, event):
        """
        Handle Enter key press in the user input area
        """
        if source == self._user_input and event.type() == event.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                if event.modifiers() & Qt.ShiftModifier:  # Shift + Enter adds a new line
                    pass
                else:  # Enter sends the message
                    if self._waiting_for_response == False:
                        self._send_message()
                    return True  # Event handled
        return super().eventFilter(source, event)
    
    def update(self):
        """
        Update the chat window when notified of changes
        """
        if not self._chat_display.toPlainText().strip():
            self._last_loaded_index = 0
        self._messages = self._chat_history.get_messages()
        if not self._messages:  # If history is cleared, reset the index and UI
            self._last_loaded_index = 0
            self._clear_display()
            if self._api_client.name == 'gemini':
                self._api_client.clear_history()
        else:
            self._load_new_messages()       

    def _load_new_messages(self):
        """
        Load and display only new messages from chat history
        """
        try:
            self._messages = self._chat_history.get_messages()
            # Load only messages that haven't been displayed yet
            new_messages = self._messages[self._last_loaded_index:]
            if not new_messages:
                return  # No new messages to load

            for message in new_messages:
                sender = "AI" if message['role'] == "assistant" else "You"
                self._chat_display.moveCursor(QTextCursor.End)  # Move cursor to end
                # Track the block number of the last user message
                if sender == "You":
                    self._last_user_block_number = self._chat_display.textCursor().blockNumber()
                self._chat_display.insertPlainText(f"{sender}:\n{message['content']}\n\n")

            # Update the last loaded index
            self._last_loaded_index = len(self._messages)

            self._scroll_to_last_user_message()
        except Exception as e:
            self._log_manager.log_error(f"Failed to load new messages", error = e)

    def _scroll_to_last_user_message(self):
        """
        Scroll so that the user's last message is at the top of the visible area
        """
        try:     
            if hasattr(self, '_last_user_block_number'):              
                document = self._chat_display.document()
                block = document.findBlockByNumber(self._last_user_block_number)
                cursor = QTextCursor(block)

                # Get cursor rectangle in viewport coordinates
                cursor_rect = self._chat_display.cursorRect(cursor)

                # Calculate desired scroll value
                desired_scroll_value = self._scrollbar.value() + cursor_rect.top()

                # Check if scrolling is feasible
                if desired_scroll_value > self._scrollbar.maximum() or desired_scroll_value == 0:
                    # Not enough content to scroll further, scroll to bottom instead
                    self._scrollbar.setValue(self._scrollbar.maximum())
                else:
                    # Scroll to make the message appear at the top
                    self._scrollbar.setValue(desired_scroll_value)
        except Exception as e:
            self._log_manager.log_error(f"Failed to scroll to last user message", error=e)

    def _handle_send_or_stop(self):
        if not self._waiting_for_response:
            # Send message logic
            self._send_message()
        else:
            # Stop logic
            self._stop_request()
    
    def _stop_request(self):
        self._api_client.cancel_request()

    def _send_message(self):
        """
        Send user message to OpenAI and display response
        """
        try:
            message = self._user_input.toPlainText().strip()
            if not message:
                return
            
            self._waiting_for_response = True
            self._send_button.setText("Stop")
            self._first_chunk_received = False
            self._chat_display.verticalScrollBar().actionTriggered.connect(self._on_user_scroll)   
            self._user_scrolled = False
            self._user_scrolled_to_bottom = False
            # Add user message to chat display immediately
            self._add_message_to_display(message, "You")

            # Clear user input field
            self._user_input.clear()    
     
            # Disable buttons and show progress bar
            self._clear_button.setEnabled(False)
            self._progress_bar.setVisible(True)

            # Start a thread to handle the API request
            if self._api_thread is not None:
                self._api_thread.deleteLater()

            self._api_thread = APIRequestThread(message, self._api_client)
            self._api_thread.chunk_received.connect(self._add_message_to_display)
            self._api_thread.finished.connect(self._cleanup_thread)
            self._api_thread.start()          
        except Exception as e:
            self._log_manager.log_error(f"Error sending message", error = e)
            QMessageBox.critical(self, "Error", "Failed to send message.")
    
    def _cleanup_thread(self):
        """
        Clean up the thread instance after it finishes execution
        """
        self._chat_display.verticalScrollBar().actionTriggered.disconnect(self._on_user_scroll)   
        
        # Hide progress bar and re-enable buttons
        self._waiting_for_response = False
        self._send_button.setText("Send")
        self._progress_bar.setVisible(False)
        self._clear_button.setEnabled(True)

        if self._api_thread is not None:
            self._api_thread.deleteLater()
            self._api_thread = None

    def _on_user_scroll(self):
        """
        Check for user scroll
        """
        self._user_scrolled = True
        self._desired_scroll_value = self._scrollbar.value()
        self._user_scrolled_to_bottom = self._scrollbar.value() == self._scrollbar.maximum()

    def _add_message_to_display(self, message: str, sender: Optional[str] = 'AI'):

        """
        Add a message to the chat display
        
        Parameters:
            sender (str): The sender of the message ("You" or "AI")
            message (str): The content of the message
        """
        self._chat_display.moveCursor(QTextCursor.End)
        if sender == 'You':
            self._markdown_buffer = ""
            current_content = self._chat_display.toMarkdown()
            self._last_user_block_number = self._chat_display.textCursor().blockNumber()
            if current_content == "":
                self._chat_display.setMarkdown(current_content + f"**{sender}**:\n\n{message}"+"\n```markdown\n\n```\n")
                # self._chat_display.insertPlainText(f"\n\n\n")
                current_content = self._chat_display.toMarkdown()
                self._chat_display.setMarkdown(current_content + f"**Promptly**:\n\n")
            else:
                self._chat_display.insertPlainText(f"\n\n\n")
                current_content = self._chat_display.toMarkdown()
                self._chat_display.setMarkdown(current_content + "\n```markdown\n\n```\n" + f"**{sender}**:\n\n{message}"+"\n```markdown\n\n```\n")
                # self._chat_display.insertPlainText(f"\n\n\n")
                current_content = self._chat_display.toMarkdown()
                self._chat_display.setMarkdown(current_content + f"**Promptly**:\n\n")
            # if current_content == "":
            #     self._chat_display.setMarkdown(current_content + f"**{sender}**:\n\n{message}"+" "+"\n\n---"+" \n\n**AI**:\n\n")
            # else:
            #     self._chat_display.setMarkdown(
            #         current_content + f"\n\n---\n\n**{sender}**:\n\n{message}" + " " + "\n\n---" + " \n\n**AI**:\n\n")

            # self._chat_display.insertPlainText(f"**{sender}**:\n{message}\n\n")
            self._last_loaded_index = self._last_loaded_index + 2
            # self._chat_display.insertPlainText(f"**AI**:\n")
            self._current_content = self._chat_display.toMarkdown()
        else:
            # if not self._first_chunk_received:
            #     self._chat_display.insertPlainText(f"{sender}:\n{message}")
            #     self._last_loaded_index = self._last_loaded_index + 1
            #     self._first_chunk_received = True
            # else:
            self._markdown_buffer += message
            # current_content = self._chat_display.toMarkdown()
            self._chat_display.setMarkdown(self._current_content + self._markdown_buffer)  # Append new content
            # self._chat_display.insertPlainText(f"{message}")
            # self._markdown_buffer += message
        # self._chat_display.moveCursor(QTextCursor.End)

        if not self._user_scrolled:
            self._scroll_to_last_user_message()
        elif self._user_scrolled_to_bottom:
            self._chat_display.moveCursor(QTextCursor.End)
        else:
            self._scrollbar.setValue(self._desired_scroll_value)

    def scroll_to_bottom(self):
        self._chat_display.moveCursor(QTextCursor.End)
        
    def _clear_history(self):
        """
        Clear chat history from display and storage
        """
        try:
            self._chat_history.clear_history()
            self._chat_history.save_history()
            self._log_manager.log_info("Chat history cleared successfully")
        except:
            self._log_manager.log_error("Failed to clear chat history")
            QMessageBox.critical("Error", "Failed to clear chat history")

    def _clear_display(self):
        """
        Clear the chat display
        """
        try:
            QMetaObject.invokeMethod(self._chat_display, "clear", Qt.QueuedConnection)
            self._last_loaded_index = 0
        except Exception as e:
            self._log_manager.log_error(f"Failed to clear chat display: {e}")

    def show(self):
        """
        Show the chat window
        """
        try:
            # If the window is hidden or not created, show it
            self.update()
            self.showNormal()
            self._user_input.setFocus()
            self.raise_()  # Bring the window to the front
            self.activateWindow()  # Focus on the window

            # Log that the chat window is being shown
            self._log_manager.log_info("Chat window shown.")
        except Exception as e:
            self._log_manager.log_error(f"Failed to show chat window: {e}")

    def closeEvent(self, event):
        """
        Handle window closing
        """
        try:
            self._save_window_geometry()
            self._log_manager.log_info("Chat window closing")
            self.hide()  # Hide the window instead of destroying it
            event.ignore()
            if self._on_window_close_callback:
                self._on_window_close_callback()
        except Exception as e:
            self._log_manager.log_error(f"Error during window closing: {e}")

        """
        Save geometry on close
        """
        # self._save_window_geometry()
        # super().closeEvent(event)

    def _on_closing(self):
        """
        Handle window closing
        """
        try:
            self._log_manager.log_info("Chat window closing")
            self.hide()  # Hide the window instead of destroying it
            if self._on_window_close_callback:
                self._on_window_close_callback()
        except Exception as e:
            self._log_manager.log_error(f"Error during window closing: {e}")
 
    def _copy_last_reply_to_clipboard(self):
        """
        Copy the last AI reply from chat history to the clipboard
        """
        try:
            # Find the last message with role 'assistant'
            last_reply = next(
                (message['content'] for message in reversed(self._messages) if message['role'] == 'assistant'),
                None
            )
            if last_reply:
                pyperclip.copy(last_reply)
        except Exception as e:
            self._log_manager.log_error(f"An error occurred while copying to clipboard", error = e)

class APIRequestThread(QThread):
    """
    Thread for making OpenAI API requests without blocking the UI
    """
    chunk_received = pyqtSignal(str)  # Signal for each streamed chunk
    finished = pyqtSignal()         # Signal when request is complete

    def __init__(self, user_message, api_client):
        """
        Initialize the thread with the user message and OpenAI client.

        Parameters:
            user_message (str): The message to send to the OpenAI API.
            api_client (BaseAPIClient): The singleton instance of a specific BaseAPIClient.
        """
        super().__init__()
        self._user_message = user_message
        self._api_client = api_client

    def run(self):
        """
        Perform the API request in a separate thread
        """
        try:
            for chunk in self._api_client.send_request(self._user_message):
                if chunk:  # Emit each chunk as it arrives
                    self.chunk_received.emit(chunk)
        finally:
            self.finished.emit()