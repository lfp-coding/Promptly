# Promptly

## Overview
**Promptly** is a productivity tool designed to streamline interactions with Large Language Models (LLMs). It allows users to quickly execute frequently used prompts via hotkeys, directly from any text-based application (e.g., Word, Outlook). The tool runs in the background, listens for configured hotkeys, and automates the process of copying selected text, applying a predefined prompt, sending it to the LLM through the Gemini API, and pasting the response back into the active application.

Additionally, Promptly includes a **prompt selector menu** for quick access to all prompts and a **chat window** for interactive conversations or debugging prompt behavior.

---

## Features
- **Hotkey-Triggered Prompts**: Assign hotkeys to predefined prompts for quick execution.
- **Prompt Selector Menu**: A quick-access menu to choose from all available prompts.
- **Chat Window**: Use as a standalone chat interface or debug prompt responses.
- **Tray Icon**: Provides easy access to
   - Open the chat window
   - Access settings
	- Quit the application
- **Customizable Prompts**: Define prompts with the following settings
  - **Clear History**: Optionally clear chat history before executing a prompt.
  - **Additional Input Field**: Add dynamic context to prompts using `{input}` placeholders.
  - **Output Options**: Choose to display responses in the chat window or paste them directly into the active application.
  - **Behavior Settings**:
    - When text is selected: Process or skip execution.
    - When no text is selected: Skip processing, select all text, or process without selection.
  - **Enabled State**: Enable or disable individual hotkeys.
- **Windows Autostart**: Optionally configure Promptly to start with Windows.

---

## Installation
1. Download the `.zip` file containing Promptly from the GitHub repository.
2. Extract the `.zip` file into your user folder (e.g. C:\Users\<YourUsername>\Promptly). This is important because:
   - Administrator rights are not required when placed in the user folder.
   - The Gemini API key will be securely stored in the Windows Credential Manager.
3. The extracted folder will include:
   - `Promptly.exe`: The main executable file.
   - `LICENSE`: The license file specifying usage rights and permissions for the software.
   - `README.txt`: Documentation explaining how to use Promptly, including installation and usage instructions.
4. On first launch:
   - You will be prompted to enter your Gemini API key.
   - Promptly will create additional folders (e.g. configuration and logs) in its directory.
   - Shortcuts will be created for:
     - Opening the chat window
     - Starting and stopping the hotkey listener
     - Uninstalling Promptly (removes all associated files such as credentials, autostart configuration, lock files, and shortcuts)

---

## Usage
1. Launch Promptly by running `Promptly.exe` file or one of the shortcuts. 
2. Configure your prompts and hotkeys in the settings menu:
   - Define a prompt template using `{text}` for selected text and `{input}` for additional input fields.
   - Assign hotkeys for each prompt.
3. Use hotkeys in any text-based application:
   - Select text and trigger the hotkey to execute the associated prompt.
   - The response will be pasted back into your application or displayed in a separate window based on your configuration.
4. Access additional features:
   - Open the chat window for interactive conversations or debugging.
   - Use the prompt selector menu for quick access to all configured prompts.
5. When running, Promptly creates a tray icon in your system's notification area. The tray icon provides quick access to essential functions:
	- Open the chat window for interactive conversations or debugging prompts.
	- Access settings to configure your prompts and hotkeys.
	- Quit Promptly from the tray icon menu.

---

## Configuration
Each prompt can be customized with the following attributes:
- **Clear History**: Clears previous interactions before sending the new prompt.
- **Additional Input Field**: Allows dynamic input by replacing `{input}` in the template with user-provided context.
- **Output Options**: Choose between direct pasting or displaying results in a separate chat window.
- **Behavior Settings**:
  - When text is selected: Skip processing or proceed with execution.
  - When no text is selected: Skip, select all text automatically, or process without selection.

---

## Verifying Intergrity
To verify that the downloaded .zip matches this release:
1. Generate a SHA256 checksum for your downloaded Promptly.zip file:

   `certutil -hashfile Promptly.zip SHA256`
2. Compare it with the expected checksum provided below:

   `e083579ad28683567db92ee2d3237aa7c6f4546f6e46a80cf9570418e3e73fdb`
   
This ensures that the executable has not been tampered with.

---

## Building from Source
To build Promptly from source:
   1. Clone this repository:
      ```
      git clone https://github.com/lfp-coding/Promptly.git
      cd Promptly
      ```
   2. Install Python 3.x and required dependencies:

      `pip install -r requirements.txt`
   3. Use PyInstaller to create an executable:

      `pyinstaller --onefile --icon=assets\Promptly.ico --noconsole --name=Promptly.exe src\main.py`
   4. The resulting Promptly.exe will be located in the dist/ folder.

---

## License
This project is licensed under the MIT License. See `LICENSE` file for details.

---

## Contributions
This is currently a private project and not open for contributions. If you have suggestions or feedback, feel free to open an issue on GitHub.
