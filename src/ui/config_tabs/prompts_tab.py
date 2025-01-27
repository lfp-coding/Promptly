from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QPushButton, QLabel, QComboBox, QGroupBox,
    QLineEdit, QTextEdit, QCheckBox, QMessageBox, QScrollBar, QGridLayout
)
from PyQt5.QtCore import Qt, QTimer
from typing import Dict
import copy

import sys
from pathlib import Path
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))
from src.ui.widgets.hotkey_input import HotkeyInputWidget
from src.utils.prompt_manager import PromptManager
from src.utils.dataclasses import Prompt, PromptBehavior, TextSelectionBehaviour
from src.utils.log_manager import LogManager
from src.core.hotkey_manager import HotkeyManager

class DraggablePromptList(QListWidget):
    """
    Custom QListWidget to support drag-and-drop for reordering prompts.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QListWidget.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)

    def dropEvent(self, event):
        """
        Handle drop event to update prompt order in self._modified_prompts.
        """
        super().dropEvent(event)
        # Update internal prompt order after drag-and-drop
        self.parent()._update_prompt_order()

class PromptsTab(QWidget):
    def __init__(self, parent=None):
        """
        Initialize prompts tab
        """
        super().__init__(parent)
        self._log_manager = LogManager.get_instance()
        self._prompt_manager = PromptManager.get_instance()
        self._hotkey_manager = HotkeyManager.get_instance()

        self._modified_prompts = copy.deepcopy(self._prompt_manager.get_all_prompts())
        self._changes = False

        self._current_prompt = None
        self._current_prompt_id = None

        self._create_widgets()

        self._refresh_prompt_list()

        if self._prompt_list.count() > 0:
            self._prompt_list.setCurrentRow(0)
            self._current_prompt_id = self._prompt_list.currentItem().text()
            self._current_prompt = self._modified_prompts[self._current_prompt_id]
            self._load_prompt_details()
            self._changes = False
            
        self._log_manager.log_info("Prompts tab initialized")

    def _create_widgets(self):
        """
        Create all widgets for prompt management
        """
        try:
            # Main layout
            main_layout = QHBoxLayout()

            # Left pane: Prompt list
            self._prompt_list = DraggablePromptList(self)
            self._prompt_list.setSelectionMode(QListWidget.SingleSelection)
            self._prompt_list.setVerticalScrollBar(QScrollBar(self))
            self._prompt_list.currentRowChanged.connect(self._on_prompt_select)

            # Add prompt list to the left pane
            left_layout = QVBoxLayout()
            left_layout.addWidget(QLabel("Prompts"))
            left_layout.addWidget(self._prompt_list)

            # Right pane: Prompt details
            right_layout = QVBoxLayout()

            # Prompt ID
            id_layout = QHBoxLayout()
            id_label = QLabel("Prompt ID:")
            self._id_field = QLineEdit()
            self._id_field.textChanged.connect(self._on_field_change)
            id_layout.addWidget(id_label)
            id_layout.addWidget(self._id_field)

            # Description
            desc_layout = QHBoxLayout()
            desc_label = QLabel("Description:")
            self._desc_field = QLineEdit()
            self._desc_field.textChanged.connect(self._on_field_change)
            desc_layout.addWidget(desc_label)
            desc_layout.addWidget(self._desc_field)

            # Template
            template_label = QLabel("Template:")
            self._template_field = QTextEdit()
            self._template_field.textChanged.connect(self._on_field_change)

            # Behaviors
            behaviour_group = QGroupBox("Behaviour")
            behavior_layout = QGridLayout()
            
            self._clear_history_checkbox = QCheckBox("Clear History")
            self._clear_history_checkbox.stateChanged.connect(self._on_field_change)
            
            text_selected_label = QLabel("Behavior when text is selected:")
            self._text_selected_dropdown = QComboBox()
            self._text_selected_dropdown.addItems(["Skip", "Process"])
            self._text_selected_dropdown.currentIndexChanged.connect(self._on_field_change)  # Track changes

            no_text_selected_label = QLabel("Behavior when no text is selected:")
            self._no_text_selected_dropdown = QComboBox()
            self._no_text_selected_dropdown.addItems(["Skip", "Process", "Select All"])
            self._no_text_selected_dropdown.currentIndexChanged.connect(self._on_field_change)
            
            self._additional_input_checkbox = QCheckBox("Additional Input")
            self._additional_input_checkbox.stateChanged.connect(self._on_field_change)
            
            self._output_on_separate_window_checkbox = QCheckBox("Output on Separate Window")
            self._output_on_separate_window_checkbox.stateChanged.connect(self._on_field_change)

            behavior_layout.addWidget(self._clear_history_checkbox, 0, 0)
            behavior_layout.addWidget(text_selected_label, 1, 0)
            behavior_layout.addWidget(self._text_selected_dropdown, 1, 1)
            behavior_layout.addWidget(no_text_selected_label, 2, 0)
            behavior_layout.addWidget(self._no_text_selected_dropdown, 2, 1)
            behavior_layout.addWidget(self._additional_input_checkbox, 0, 1)
            behavior_layout.addWidget(self._output_on_separate_window_checkbox, 0, 2)

            behaviour_group.setLayout(behavior_layout)

            # Hotkey
            hotkey_group = QGroupBox("Hotkey")
            hotkey_layout = QGridLayout()
            self._hotkey_widget = HotkeyInputWidget(self)
            self._hotkey_widget.hotkeyChanged.connect(self._on_field_change)
            hotkey_layout.addWidget(self._hotkey_widget, 0, 0)

            self._hotkey_enabled_checkbox = QCheckBox("Enabled")
            self._hotkey_enabled_checkbox.stateChanged.connect(self._on_field_change)
            hotkey_layout.addWidget(self._hotkey_enabled_checkbox, 0, 1)

            hotkey_group.setLayout(hotkey_layout)

            # Buttons
            button_layout = QHBoxLayout()
            
            add_button = QPushButton("Add Prompt")
            add_button.clicked.connect(self._add_prompt)  # Connect to add_prompt method
            
            remove_button = QPushButton("Remove Prompt")
            remove_button.clicked.connect(self._remove_prompt)  # Connect to remove_prompt method
            
            button_layout.addWidget(add_button)
            button_layout.addWidget(remove_button)

            # Add components to the right layout
            right_layout.addLayout(id_layout)
            right_layout.addLayout(desc_layout)
            right_layout.addWidget(template_label)
            right_layout.addWidget(self._template_field)
            
            right_layout.addWidget(behaviour_group)
            
            right_layout.addWidget(hotkey_group)

            right_layout.addLayout(button_layout)

            # Add both panes to the main layout
            main_layout.addLayout(left_layout, 1)  # Left pane: Prompt list
            main_layout.addLayout(right_layout, 3)  # Right pane: Prompt details

            main_layout.addStretch()
            self.setLayout(main_layout)
        except Exception as e:
            self._log_manager.log_error(f"Failed to create prompt tab widgets: {e}")
        
    def _add_prompt(self):
        """
        Add a new prompt
        """
        try:
            # Generate a unique name for the new prompt
            base_name = "New Prompt"
            counter = 1
            existing_prompts = self._modified_prompts.keys()
            new_name = base_name

            while new_name in existing_prompts:
                new_name = f"{base_name} {counter}"
                counter += 1

            # Create a default prompt object
            new_prompt = Prompt(
                    description="",
                    template="Insert your prompt here. Reply with only the processed text.\n\nText: {text}",
                    hotkey="",
                    hotkey_enabled=False,
                    behavior=PromptBehavior(
                        clear_history=True,
                        text_selected=TextSelectionBehaviour.PROCESS,
                        no_text_selected=TextSelectionBehaviour.SKIP,
                        additional_input=False,
                        output_on_separate_window=False
                    )
            )

            # Add the new prompt to modified prompts
            self._modified_prompts[new_name] = new_prompt

            # Refresh the prompt list and select the newly added prompt
            self._refresh_prompt_list()
            self._prompt_list.setCurrentRow(self._prompt_list.count() - 1)  # Select last item

            # Load details of the newly added prompt
            self._current_prompt_id = new_name
            self._current_prompt = self._modified_prompts[new_name]
            self._load_prompt_details()

            # Log success
            self._log_manager.log_info(f"Added new prompt: {new_name}")

        except Exception as e:
            # Log and handle errors
            self._log_manager.log_error(f"Failed to add prompt: {e}")

    def _remove_prompt(self):
        """
        Remove selected prompt
        """
        try:
            # Check if a prompt is currently selected
            if not self._current_prompt_id:
                self._log_manager.log_warning("No prompt selected for removal.")
                return

            # Remove the selected prompt from modified prompts
            del self._modified_prompts[self._current_prompt_id]

            # Clear current prompt details
            self._current_prompt_id = None
            self._current_prompt = None
            self._clear_details()

            # Refresh the prompt list
            self._refresh_prompt_list()

            # Log success
            self._log_manager.log_info("Prompt removed successfully.")

        except Exception as e:
            # Log and handle errors
            self._log_manager.log_error(f"Failed to remove prompt: {e}")

    def save_current_prompt(self) -> bool:
        """
        Save changes to current prompt
        """
        try:
            # Check if a prompt is currently selected
            if not self._current_prompt_id:
                self._log_manager.log_warning("No prompt selected to save.")
                return False

            # Extract updated values from form fields
            updated_id = self._id_field.text().strip()
            description = self._desc_field.text().strip()
            template = self._template_field.toPlainText().strip()

            clear_history = self._clear_history_checkbox.isChecked()
            
            # Retrieve Text Selected Behavior
            text_selected_index = self._text_selected_dropdown.currentIndex()
            if text_selected_index == 1:
                text_selected = "Process"
                text_selected = TextSelectionBehaviour.PROCESS
            else:  # Default to "Skip"
                text_selected = TextSelectionBehaviour.SKIP

            # Retrieve No Text Selected Behavior
            no_text_selected_index = self._no_text_selected_dropdown.currentIndex()
            if no_text_selected_index == 1:
                no_text_selected = TextSelectionBehaviour.PROCESS
            elif no_text_selected_index == 2:
                no_text_selected = TextSelectionBehaviour.SELECT_ALL
            else:  # Default to "Skip"
                no_text_selected = TextSelectionBehaviour.SKIP

            additional_input = self._additional_input_checkbox.isChecked()
            output_on_separate_window = self._output_on_separate_window_checkbox.isChecked()

            hotkey = self._hotkey_widget.get_hotkey()
            hotkey_enabled = self._hotkey_enabled_checkbox.isChecked()

            # Validate required fields
            if not updated_id:
                self._log_manager.log_warning("Prompt ID cannot be empty.")
                QMessageBox.warning(self, "Prompt wasn't saved.", "Prompt ID cannot be empty.")
                return False

            # Handle renaming of the prompt
            if updated_id != self._current_prompt_id:
                if updated_id in self._modified_prompts:
                    self._log_manager.log_warning(
                        f"Cannot rename prompt: ID '{updated_id}' already exists."
                    )
                    QMessageBox.warning(self, "Prompt wasn't saved.", f"Cannot rename prompt: ID '{updated_id}' already exists.")
                    return False

                # Rename key while preserving order
                keys = list(self._modified_prompts.keys())
                index = keys.index(self._current_prompt_id)
                keys[index] = updated_id

                new_dict = {k: (self._modified_prompts[k] if k != updated_id else Prompt(
                    description=description,
                    template=template,
                    hotkey=hotkey,
                    hotkey_enabled=hotkey_enabled,
                    behavior=PromptBehavior(
                        clear_history=clear_history,
                        text_selected=text_selected,
                        no_text_selected=no_text_selected,
                        additional_input=additional_input,
                        output_on_separate_window=output_on_separate_window
                    )
                )) for k in keys}

                self._modified_prompts = new_dict
                
                self._current_prompt_id = updated_id
                self._refresh_prompt_list()
            else:
                # Update the current prompt in modified prompts
                self._modified_prompts[self._current_prompt_id] = Prompt(
                        description=description,
                        template=template,
                        hotkey=hotkey,
                        hotkey_enabled=hotkey_enabled,
                        behavior=PromptBehavior(
                            clear_history=clear_history,
                            text_selected=text_selected,
                            no_text_selected=no_text_selected,
                            additional_input=additional_input,
                            output_on_separate_window=output_on_separate_window
                        )
                )
            
            self._changes = False

            self._log_manager.log_info(f"Prompt '{updated_id}' saved successfully.")
            return True

        except Exception as e:
            # Log and handle errors
            self._log_manager.log_error(f"Failed to save prompt: {e}")

    def _refresh_prompt_list(self):
        """
        Populate the prompt list with all available prompts
        """
        try:
            # Clear existing items
            self._prompt_list.clear()

            # Populate QListWidget with prompt IDs
            for prompt_id in self._modified_prompts.keys():
                item = QListWidgetItem(prompt_id)
                self._prompt_list.addItem(item)

            # If there are prompts, select the first one by default
            if self._prompt_list.count() > 0:
                self._prompt_list.setCurrentRow(0)
        except Exception as e:
            self._log_manager.log_error(f"Failed to refresh prompt list: {e}")
            
    def _update_prompt_order(self):
        """
        Update the order of prompts in the internal dictionary based on QListWidget order.
        """
        try:
            ordered_ids = [self._prompt_list.item(i).text() for i in range(self._prompt_list.count())]
            updated_prompts = {id_: self._modified_prompts[id_] for id_ in ordered_ids}
            self._modified_prompts = updated_prompts
            self._on_field_change()
        except Exception as e:
            self._log_manager.log_error(f"Failed to update prompt order: {e}")

    def _on_prompt_select(self, index):
        """
        Handle prompt selection
        """
        try:
            # Track the previous selection

            if self._current_prompt_id and self._changes:
                if not self.save_current_prompt():  # Save the current prompt before switching
                    QTimer.singleShot(0, lambda: self._revert_selection(self._index))
                    return
                
            # Get selected item
            selected_item = self._prompt_list.item(index)
            if not selected_item:
                return  # No item selected

            # Get selected prompt ID
            selected_prompt_id = selected_item.text()

            # Retrieve corresponding prompt data
            self._current_prompt = self._modified_prompts[selected_prompt_id]
            self._current_prompt_id = selected_prompt_id

            # Load details into form fields
            self._load_prompt_details()

            self._changes = False
            self._index = index
        except Exception as e:
            self._log_manager.log_error(f"Failed to handle prompt selection: {e}")

    def _revert_selection(self, previous_index):
        """
        Revert the QListWidget selection to the previous index.
        """
        self._prompt_list.blockSignals(True)  # Temporarily block signals to avoid recursion
        self._prompt_list.setCurrentRow(previous_index)
        self._prompt_list.blockSignals(False)

    def _load_prompt_details(self):
        """
        Load details of the currently selected prompt into form fields
        """
        if not self._current_prompt:
            return  # No current prompt to load

        try:
            # Set ID and description fields
            self._id_field.setText(self._current_prompt_id)
            self._desc_field.setText(self._current_prompt.description)

            # Set template field
            self._template_field.setPlainText(self._current_prompt.template)

            # Set behavior checkboxes
            self._clear_history_checkbox.setChecked(self._current_prompt.behavior.clear_history)

            text_selected_value = self._current_prompt.behavior.text_selected.value
            if text_selected_value == "process":
                self._text_selected_dropdown.setCurrentIndex(1)
            else:  # Default to "Skip"
                self._text_selected_dropdown.setCurrentIndex(0)

            # Set No Text Selected Behavior
            no_text_selected_value = self._current_prompt.behavior.no_text_selected.value
            if no_text_selected_value == "process":
                self._no_text_selected_dropdown.setCurrentIndex(1)
            elif no_text_selected_value == "select_all":
                self._no_text_selected_dropdown.setCurrentIndex(2)
            else:  # Default to "Skip"
                self._no_text_selected_dropdown.setCurrentIndex(0)
            
            self._additional_input_checkbox.setChecked(self._current_prompt.behavior.additional_input)
            self._output_on_separate_window_checkbox.setChecked(self._current_prompt.behavior.output_on_separate_window)

            self._hotkey_widget.set_hotkey(self._current_prompt.hotkey)
            self._hotkey_enabled_checkbox.setChecked(self._current_prompt.hotkey_enabled)
        except Exception as e:
            self._log_manager.log_error(f"Failed to load prompt details: {e}")

    def _clear_details(self):
        """
        Clear all detail fields
        """
        try:
            # Clear text fields
            self._id_field.clear()
            self._desc_field.clear()
            self._template_field.clear()

            # Reset checkboxes
            self._clear_history_checkbox.setChecked(False)
            self._text_selected_dropdown.setCurrentIndex(0)
            self._no_text_selected_dropdown.setCurrentIndex(0)
            self._additional_input_checkbox.setChecked(False)
            self._output_on_separate_window_checkbox.setChecked(False)

            # Reset Hotkey
            self._hotkey_widget.set_hotkey("")
            self._hotkey_enabled_checkbox.setChecked(False)
        except Exception as e:
            # Log any errors during clearing
            self._log_manager.log_error(f"Failed to clear details: {e}")

    def _on_field_change(self, *args):
        """
        Handle field changes
        """
        try:
            # Mark changes as unsaved
            self._changes = True

            # Log change detection (optional)
            self._log_manager.log_debug("Field change detected, marking as unsaved.")
        except Exception as e:
            # Handle any errors during field change tracking
            self._log_manager.log_error(f"Error handling field change: {e}")

    def get_config(self) -> Dict:
        """
        Returns the modified prompts
        """
        return self._modified_prompts