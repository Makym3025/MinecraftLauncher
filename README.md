# MinecraftLauncher

# Simple Offline Minecraft Launcher

Hey there! This is a simple little program made with Python that lets you launch Minecraft Java Edition. It's built specifically for playing offline or joining 'cracked' servers (those that have `online-mode=false` in their settings).

## What it Does

*   **Manage Your Setups (Profiles):** You can create different profiles for playing, maybe one for each server or modpack you use. Give them names, edit them, or delete them easily.
*   **Pick Your Version:** Choose the Minecraft version you want to play from the ones you have installed, or install a new one right from the profile editor.
*   **Your Nickname & RAM:** Set your in-game nickname and decide how much RAM (memory) Minecraft should use for each profile.
*   **Offline Ready:** The launcher automatically sets things up for offline servers – you don't need to worry about special settings.
*   **"Fix Version" Button (Use Carefully!):** There's a button labeled "Fix Selected Profile for Offline Play". This button tries to modify the game's configuration file (`.json`) for the selected version. While this *might* sometimes help with older versions or specific server issues, **it's generally recommended NOT to use this button unless you know what you're doing.** It can potentially mess things up, though it does try to make a backup first (`.json.backup`).
*   **Looks Nice (Hopefully!):** Uses a dark theme (`QDarkStyle`) to be easy on the eyes.

## What You Need

*   **Python 3:** Make sure you have Python installed on your computer.
*   **Some Python Magic (Libraries):** The program needs a few extra bits of Python code. They're listed in `requirements.txt`:
    *   `PySide6` (for the window, buttons, etc.)
    *   `minecraft-launcher-lib` (does the heavy lifting for Minecraft stuff)
    *   `qdarkstyle` (makes it look dark and cool)

## Getting Started

1.  **Get the Code:** Either clone this repository using Git or just download the files as a ZIP.
    ```bash
    # If using Git:
    git clone <your-repository-url>
    cd <repository-folder>
    ```
2.  **Install the Extras:** Open your terminal or command prompt in the folder where you put the code (the one with `requirements.txt`). Then run:
    ```bash
    pip install -r requirements.txt
    ```
    *(The launcher might try to do this for you the first time you run it, but doing it yourself first is usually smoother.)*

## How to Use It

Just run the main file using Python:

```bash
python main.py
```

1.  **Make a Profile:** Hit "Add". Type in a name, pick a Minecraft version from the list, enter the nickname you want to use in-game, and choose how much memory to give it. Click Save.
2.  **Choose Your Profile:** Select the profile you just made (or another one) from the list.
3.  **Install (if needed):** If it's a version you haven't used before, the big button at the bottom will say "Install...". Click it and give it a moment to download and set up.
4.  **Launch!** Once installed, the button changes to "Launch...". Click it, and Minecraft should start up.
5.  **(Optional - Be Careful!) The "Fix" Button:** If you're having trouble connecting to a specific offline server, *as a last resort*, you could try selecting the profile and clicking "Fix Selected Profile for Offline Play". Then try launching again. But remember the warning above!

## Where's the Game Data?

The launcher will automatically create a folder named `minecraft` **in the same directory where you run `main.py` from.** All the game versions, saves, resource packs, etc., for this launcher will go inside that `minecraft` folder.

## Important Stuff to Remember

*   This is for **offline play** or **non-premium (`cracked`) servers only.**
*   You **CANNOT** use this to join official Minecraft servers (like Hypixel) or other servers that require you to own the game. You need to buy Minecraft for that!
*   Messing with the "Fix" button could potentially cause problems. Use it at your own risk! 
