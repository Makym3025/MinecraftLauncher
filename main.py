import sys
import minecraft_launcher_lib
import subprocess
import os
import uuid # Added for generating offline UUID
import json # Added for saving/loading settings
import shutil # Added for file backups

# --- Settings Management ---
SETTINGS_FILE = "launcher_settings.json"
DEFAULT_MINECRAFT_DIR = os.path.join(os.getcwd(), "minecraft")

def load_settings():
    """Loads settings from SETTINGS_FILE. Returns defaults if file not found or invalid."""
    default_settings = {
        'minecraft_directory': DEFAULT_MINECRAFT_DIR,
        'profiles': [],
        'last_selected_profile': None
    }
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
                # Validate essential keys and provide defaults
                if 'minecraft_directory' not in settings:
                    settings['minecraft_directory'] = DEFAULT_MINECRAFT_DIR
                if 'profiles' not in settings or not isinstance(settings['profiles'], list):
                    settings['profiles'] = []
                if 'last_selected_profile' not in settings:
                    settings['last_selected_profile'] = None

                # Ensure Minecraft directory exists
                mc_dir = settings['minecraft_directory']
                if not os.path.exists(mc_dir):
                     try:
                         os.makedirs(mc_dir)
                     except OSError as e:
                         print(f"Warning: Could not create Minecraft directory {mc_dir}: {e}")
                         settings['minecraft_directory'] = DEFAULT_MINECRAFT_DIR
                         if not os.path.exists(DEFAULT_MINECRAFT_DIR):
                             try:
                                 os.makedirs(DEFAULT_MINECRAFT_DIR)
                             except OSError as e2:
                                 print(f"Fatal: Could not create default Minecraft directory {DEFAULT_MINECRAFT_DIR}: {e2}. Exiting.")
                                 sys.exit(1)
                return settings
    except (json.JSONDecodeError, OSError, FileNotFoundError) as e:
        print(f"Error loading settings: {e}. Using default settings.")

    # Fallback to default settings if file doesn't exist or loading failed
    if not os.path.exists(DEFAULT_MINECRAFT_DIR):
        try:
            os.makedirs(DEFAULT_MINECRAFT_DIR)
        except OSError as e:
             print(f"Fatal: Could not create default Minecraft directory {DEFAULT_MINECRAFT_DIR}: {e}. Exiting.")
             sys.exit(1)
    return default_settings

def save_settings(settings):
    """Saves the given settings dictionary to SETTINGS_FILE."""
    try:
        # Ensure profiles is a list before saving
        if 'profiles' not in settings or not isinstance(settings['profiles'], list):
            settings['profiles'] = []
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=4)
    except OSError as e:
        print(f"Error saving settings: {e}")

# Make sure the directory exists (This part will be handled by load_settings now)
# MINECRAFT_DIR = os.path.join(os.getcwd(), "minecraft") 
# if not os.path.exists(MINECRAFT_DIR):
#     os.makedirs(MINECRAFT_DIR)

# Updated imports for QProgressBar and threading
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout,
                               QListWidget, QPushButton, QProgressBar, QMessageBox,
                               QLineEdit, QSpinBox, QHBoxLayout,
                               QComboBox, QDialog, QDialogButtonBox, 
                               QFormLayout, QCheckBox)
from PySide6.QtCore import Qt, QThread, Signal, Slot

# Thread for installation to avoid freezing GUI
class InstallThread(QThread):
    progress_update = Signal(int)
    progress_max_update = Signal(int)
    status_update = Signal(str)
    finished_signal = Signal(bool, str) # success (bool), message (str)

    def __init__(self, version_id, minecraft_dir):
        super().__init__()
        self.version_id = version_id
        self.minecraft_dir = minecraft_dir
        self.callback = {
            "setStatus": self.set_status,
            "setProgress": self.set_progress,
            "setMax": self.set_max
        }

    def set_status(self, status):
        self.status_update.emit(status)

    def set_progress(self, value):
        self.progress_update.emit(value)

    def set_max(self, value):
        self.progress_max_update.emit(value)

    def run(self):
        try:
            minecraft_launcher_lib.install.install_minecraft_version(
                self.version_id,
                self.minecraft_dir,
                callback=self.callback
            )
            self.finished_signal.emit(True, f"Version {self.version_id} installed successfully!")
        except Exception as e:
            error_message = f"Failed to install {self.version_id}: {e}"
            print(error_message) # Log error
            self.finished_signal.emit(False, error_message)


# --- Profile Edit/Add Dialog ---
class ProfileDialog(QDialog):
    def __init__(self, parent=None, existing_profile=None, minecraft_dir=None):
        super().__init__(parent)
        self.setWindowTitle("Add/Edit Profile" if not existing_profile else f"Edit Profile: {existing_profile.get('name')}")
        self.minecraft_dir = minecraft_dir or DEFAULT_MINECRAFT_DIR # Use default if not provided
        self.existing_profile = existing_profile

        self.layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()

        # Profile Name
        self.name_input = QLineEdit()
        self.form_layout.addRow("Profile Name:", self.name_input)

        # Minecraft Version
        self.version_combo = QComboBox()
        self.version_combo.setPlaceholderText("Loading versions...")
        self.form_layout.addRow("Minecraft Version:", self.version_combo)
        self.load_minecraft_versions()

        # Username
        self.username_input = QLineEdit()
        self.form_layout.addRow("Username:", self.username_input)

        # Memory (GB)
        self.memory_spinbox = QSpinBox()
        self.memory_spinbox.setRange(1, 16)
        self.memory_spinbox.setSuffix(" GB")
        self.form_layout.addRow("Memory:", self.memory_spinbox)

        self.layout.addLayout(self.form_layout)

        # Dialog Buttons (Save/Cancel)
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        # Populate fields if editing
        if self.existing_profile:
            self.name_input.setText(self.existing_profile.get('name', ''))
            # Set version later after loading
            self.username_input.setText(self.existing_profile.get('username', 'Player'))
            self.memory_spinbox.setValue(self.existing_profile.get('memory_gb', 2))

    def load_minecraft_versions(self):
        self.version_combo.clear()
        self.version_combo.setEnabled(False) # Disable while loading
        try:
            # This might take a moment, consider a thread for very slow connections
            versions = minecraft_launcher_lib.utils.get_available_versions(self.minecraft_dir)
            available_ids = [v['id'] for v in versions]
            self.version_combo.addItems(available_ids)
            self.version_combo.setEnabled(True)
            self.version_combo.setPlaceholderText("Select a version")

            # Select existing version if editing
            if self.existing_profile:
                existing_version = self.existing_profile.get('version_id')
                if existing_version in available_ids:
                    self.version_combo.setCurrentText(existing_version)
                else:
                     self.version_combo.setPlaceholderText(f"Version '{existing_version}' not found?")

        except Exception as e:
            print(f"Error loading versions for dialog: {e}")
            QMessageBox.warning(self, "Error", f"Could not load Minecraft versions: {e}")
            self.version_combo.setPlaceholderText("Error loading versions")

    def get_profile_data(self):
        """Returns the entered profile data as a dictionary."""
        name = self.name_input.text().strip()
        version = self.version_combo.currentText() if self.version_combo.currentIndex() >= 0 else None
        username = self.username_input.text().strip() or "Player" # Default to Player if empty
        memory = self.memory_spinbox.value()
        
        if not name:
             QMessageBox.warning(self, "Input Error", "Profile name cannot be empty.")
             return None
        if not version:
             QMessageBox.warning(self, "Input Error", "Please select a Minecraft version.")
             return None

        return {
            "name": name,
            "version_id": version,
            "username": username,
            "memory_gb": memory
        }

    def accept(self):
        """Override accept to validate data before closing."""
        data = self.get_profile_data()
        if data: # Only accept if data is valid
            super().accept()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Load Settings
        self.settings = load_settings()
        self.minecraft_dir = self.settings.get('minecraft_directory', DEFAULT_MINECRAFT_DIR)
        # Store profiles directly for easier access
        self.profiles = self.settings.get('profiles', []) 
        self.last_selected_profile_name = self.settings.get('last_selected_profile', None)
        self.current_selected_profile = None # Will hold the dictionary of the selected profile

        self.setWindowTitle("Minecraft Launcher")
        self.setGeometry(100, 100, 500, 550)
        self.install_thread = None # To hold the installation thread

        self.layout = QVBoxLayout(self)

        # --- User Options (Now tied to selected profile) ---
        # Username Input
        self.username_layout = QHBoxLayout() 
        self.username_label = QLabel("Username:")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Select or create a profile")
        self.username_input.setEnabled(False) # Enabled when profile selected
        self.username_layout.addWidget(self.username_label)
        self.username_layout.addWidget(self.username_input)
        self.layout.addLayout(self.username_layout)

        # Memory Allocation Input
        self.memory_layout = QHBoxLayout()
        self.memory_label = QLabel("Memory (GB):")
        self.memory_spinbox = QSpinBox()
        self.memory_spinbox.setRange(1, 16) 
        self.memory_spinbox.setEnabled(False) # Enabled when profile selected
        self.memory_layout.addWidget(self.memory_label)
        self.memory_layout.addWidget(self.memory_spinbox)
        self.layout.addLayout(self.memory_layout)

        # --- Add offline mode setting checkbox ---
        self.offline_mode_layout = QHBoxLayout()
        # self.offline_mode_checkbox = QCheckBox("Enable Offline Multiplayer") # Removed
        # self.offline_mode_checkbox.setChecked(True)  # Removed
        # self.offline_mode_checkbox.setToolTip("Allow playing multiplayer without Microsoft account.\\nRequires creating a local server or using an offline server.") # Removed
        # self.offline_mode_layout.addWidget(self.offline_mode_checkbox) # Removed
        
        # Button to check and fix a version
        self.fix_version_button = QPushButton("Fix Selected Profile for Offline Play")
        self.fix_version_button.setEnabled(False)  # Enable when profile selected
        self.fix_version_button.clicked.connect(self.fix_version_for_offline)
        self.offline_mode_layout.addWidget(self.fix_version_button)
        
        self.layout.addLayout(self.offline_mode_layout)

        # --- Profile Management (Replaces Version List) ---
        self.profile_label = QLabel("Profile:")
        self.layout.addWidget(self.profile_label)

        self.profile_selection_layout = QHBoxLayout()
        self.profile_combo = QComboBox()
        self.profile_combo.setPlaceholderText("No profiles created")
        self.profile_combo.currentIndexChanged.connect(self.on_profile_selected)
        self.profile_selection_layout.addWidget(self.profile_combo)

        # Profile Action Buttons
        self.add_profile_button = QPushButton("Add")
        self.add_profile_button.clicked.connect(self.add_profile) # Connect Add button
        self.edit_profile_button = QPushButton("Edit")
        self.edit_profile_button.setEnabled(False) # Enabled when profile selected
        self.edit_profile_button.clicked.connect(self.edit_profile) # Connect Edit button
        self.delete_profile_button = QPushButton("Delete")
        self.delete_profile_button.setEnabled(False) # Enabled when profile selected
        self.delete_profile_button.clicked.connect(self.delete_profile) # Connect Delete button

        self.profile_selection_layout.addWidget(self.add_profile_button)
        self.profile_selection_layout.addWidget(self.edit_profile_button)
        self.profile_selection_layout.addWidget(self.delete_profile_button)
        self.layout.addLayout(self.profile_selection_layout)

        # Progress Bar and Status Label
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False) # Hide initially
        self.progress_bar.setRange(0, 100)
        self.layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setVisible(False) # Hide initially
        self.layout.addWidget(self.status_label)

        # Action button (Install/Launch)
        self.action_button = QPushButton("Select or create a profile")
        self.action_button.setEnabled(False)
        self.action_button.clicked.connect(self.start_launch)  # Connect to start_launch method
        self.layout.addWidget(self.action_button)

        # Initial UI state update based on selected profile
        self.update_profile_list()

    def update_profile_list(self):
        """Update the profile combo box with the current profiles."""
        # Block signals temporarily to avoid triggering selection callbacks
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        
        # Add profiles to combo
        for profile in self.profiles:
            name = profile.get('name', 'Unknown')
            self.profile_combo.addItem(name)
        
        # Try to select the last selected profile or the first profile
        if self.profiles:
            index_to_select = 0  # Default to first profile
            
            if self.last_selected_profile_name:
                # Find index of last selected profile
                for i, profile in enumerate(self.profiles):
                    if profile.get('name') == self.last_selected_profile_name:
                        index_to_select = i
                        break
            
            self.profile_combo.setCurrentIndex(index_to_select)
        
        # Re-enable signals
        self.profile_combo.blockSignals(False)
        
        # Manually trigger selection handler
        if self.profiles:
            if hasattr(self, 'action_button'):  # Перевірка, чи існує action_button перед викликом on_profile_selected
                self.on_profile_selected(self.profile_combo.currentIndex())
        else:
            if hasattr(self, 'action_button'):  # Перевірка, чи існує action_button перед викликом on_profile_selected
                self.on_profile_selected(-1)  # No profiles

    @Slot(int)
    def on_profile_selected(self, index):
        # Перевірка наявності необхідних атрибутів
        if not hasattr(self, 'action_button') or not hasattr(self, 'username_input') or not hasattr(self, 'memory_spinbox'):
            return  # Виходимо, якщо атрибути ще не створені
            
        if index == -1:  # No selection
            self.current_selected_profile = None
            self.username_input.setText("")
            self.username_input.setEnabled(False)
            self.memory_spinbox.setValue(2)
            self.memory_spinbox.setEnabled(False)
            self.action_button.setText("Select or create a profile")
            self.action_button.setEnabled(False)
            if hasattr(self, 'fix_version_button'):
                self.fix_version_button.setEnabled(False)
            if hasattr(self, 'edit_profile_button'):
                self.edit_profile_button.setEnabled(False)
            if hasattr(self, 'delete_profile_button'):
                self.delete_profile_button.setEnabled(False)
            return

        # Get profile from combo box
        profile_name = self.profile_combo.currentText()
        found_profile = None
        for profile in self.profiles:
            if profile.get('name') == profile_name:
                found_profile = profile
                break

        if not found_profile:
            print(f"Error: Profile '{profile_name}' not found in profiles list")
            self.current_selected_profile = None
            self.action_button.setEnabled(False)
            if hasattr(self, 'fix_version_button'):
                self.fix_version_button.setEnabled(False)
            if hasattr(self, 'edit_profile_button'):
                self.edit_profile_button.setEnabled(False)
            if hasattr(self, 'delete_profile_button'):
                self.delete_profile_button.setEnabled(False)
            return

        # Update current selected profile and UI fields
        self.current_selected_profile = found_profile
        self.username_input.setText(found_profile.get('username', 'Player'))
        self.username_input.setEnabled(True)
        self.memory_spinbox.setValue(found_profile.get('memory_gb', 2))
        self.memory_spinbox.setEnabled(True)
        if hasattr(self, 'fix_version_button'):
            self.fix_version_button.setEnabled(True)
        
        # Активуємо кнопки редагування і видалення профілю
        if hasattr(self, 'edit_profile_button'):
            self.edit_profile_button.setEnabled(True)
        if hasattr(self, 'delete_profile_button'):
            self.delete_profile_button.setEnabled(True)
        
        # Відключаємо існуючі сигнали перед підключенням нових, щоб уникнути дублювання
        try:
            self.username_input.textChanged.disconnect()
        except:
            pass
        try:
            self.memory_spinbox.valueChanged.disconnect()
        except:
            pass
        
        # Check if needed to update the profile when values change
        self.username_input.textChanged.connect(lambda text: self.update_profile_field('username', text))
        self.memory_spinbox.valueChanged.connect(lambda value: self.update_profile_field('memory_gb', value))

        # Update action button based on version install status
        version_id = found_profile.get('version_id', None)
        if not version_id:
            self.action_button.setText("Select version in Edit Profile")
            self.action_button.setEnabled(False)
            if hasattr(self, 'status_label'):
                self.status_label.setText("Profile has no Minecraft version selected.")
                self.status_label.setVisible(True)
            return

        # Check if version is installed
        version_file_path = os.path.join(self.minecraft_dir, 'versions', version_id, f'{version_id}.json')
        if os.path.exists(version_file_path):
            self.action_button.setText(f"Launch {profile_name}")
            self.action_button.setEnabled(True)
            if hasattr(self, 'status_label'):
                self.status_label.setVisible(False)
        else:
            self.action_button.setText(f"Install {version_id}")
            self.action_button.setEnabled(True)
            if hasattr(self, 'status_label'):
                self.status_label.setText(f"Version {version_id} needs to be installed first.")
                self.status_label.setVisible(True)

    # --- Installation UI Slots ---
    @Slot(int)
    def update_install_progress(self, value):
        self.progress_bar.setValue(value)

    @Slot(int)
    def set_install_progress_max(self, max_value):
        self.progress_bar.setMaximum(max_value)

    @Slot(str)
    def update_install_status(self, status):
        self.status_label.setText(status)

    @Slot(bool, str)
    def on_install_finished(self, success, message):
        self.progress_bar.setVisible(False)
        self.status_label.setText(message)
        self.status_label.setVisible(True) # Keep status visible after completion
        # Re-enable buttons
        self.action_button.setEnabled(True)
        self.profile_combo.setEnabled(True)
        self.add_profile_button.setEnabled(True)
        self.edit_profile_button.setEnabled(self.current_selected_profile is not None)
        self.delete_profile_button.setEnabled(self.current_selected_profile is not None)

        # Reset install thread reference
        self.install_thread = None 

        if success:
            QMessageBox.information(self, "Installation Complete", message)
            # Optionally, try launching again automatically after successful install
            # self.start_launch()
        else:
            QMessageBox.critical(self, "Installation Failed", message)
            # Update action button text if launch couldn't proceed
            if self.current_selected_profile:
                self.action_button.setText(f"Launch {self.current_selected_profile.get('name')}")
            else:
                self.action_button.setText("Select or create a profile")

    def configure_offline_mode(self, version_id):
        """Configure the game to allow playing in offline mode, including multiplayer."""
        try:
            # Шлях до файлу конфігурації авторизації
            version_folder = os.path.join(self.minecraft_dir, 'versions', version_id)
            version_json_path = os.path.join(version_folder, f'{version_id}.json')
            
            # Створюємо резервну копію файлу, якщо вона ще не існує
            backup_path = version_json_path + '.backup'
            if not os.path.exists(backup_path) and os.path.exists(version_json_path):
                shutil.copy2(version_json_path, backup_path)
                self.status_label.setText(f"Created backup of {version_id}.json")
                QApplication.processEvents()
            
            # Читаємо файл конфігурації
            with open(version_json_path, 'r') as f:
                version_data = json.load(f)
            
            # Змінюємо налаштування автентифікації
            if 'arguments' in version_data and 'game' in version_data['arguments']:
                # Додаємо аргументи для обходу перевірки авторизації
                game_args = version_data['arguments']['game']
                
                # Якщо аргументи ще не додані, додаємо їх
                offline_args = ["--skipMultiplayerWarning"]
                for arg in offline_args:
                    if arg not in game_args:
                        game_args.append(arg)
            
            # Змінюємо URL серверів автентифікації на локальні, щоб вони не перевірялися
            # Це дозволить розблокувати мультиплеєр без Microsoft аккаунту
            if version_data.get('net', {}).get('server', {}):
                net_servers = version_data['net']['server']
                # Змінюємо усі сервери автентифікації на локальну адресу
                for key in net_servers:
                    if isinstance(net_servers[key], str) and ('mojang' in net_servers[key] or 'minecraft' in net_servers[key]):
                        net_servers[key] = "http://127.0.0.1:8080"
            
            # На випадок, якщо структура файлу інша
            if 'authenticationService' in version_data:
                if 'baseUrl' in version_data['authenticationService']:
                    version_data['authenticationService']['baseUrl'] = "http://127.0.0.1:8080"
            
            if 'servicesBaseUrl' in version_data:
                version_data['servicesBaseUrl'] = "http://127.0.0.1:8080"
                
            # Зберігаємо модифікований файл
            with open(version_json_path, 'w') as f:
                json.dump(version_data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Failed to configure offline mode: {e}")
            QMessageBox.warning(self, "Offline Mode Configuration", 
                              f"Failed to configure offline mode: {e}\nMultiplayer might be unavailable.")
            return False

    # --- Launch Functionality (Needs Update) ---
    def start_launch(self):
        if not self.current_selected_profile:
            QMessageBox.warning(self, "Warning", "Please select a profile to launch.")
            return

        version_id = self.current_selected_profile.get('version_id')
        if not version_id:
             QMessageBox.critical(self, "Error", f"Profile '{self.current_selected_profile.get('name')}' has no Minecraft version specified!")
             return
             
        # Check if version is installed ( Reuse logic from old update_action_button or add new check )
        version_file_path = os.path.join(self.minecraft_dir, 'versions', version_id, f'{version_id}.json')
        if not os.path.exists(version_file_path):
            # Version not found, trigger installation instead of showing warning
            print(f"Version {version_id} not found locally. Starting installation.")
            self.start_installation_for_profile(self.current_selected_profile)
            return # Stop the launch process, installation will handle next steps

        # --- Version is installed, proceed with launch --- 
        profile_name = self.current_selected_profile.get('name')
        self.action_button.setEnabled(False)
        self.action_button.setText(f"Launching {profile_name}...")
        self.status_label.setText(f"Preparing launch for {profile_name} ({version_id})...")
        self.status_label.setVisible(True)
        QApplication.processEvents()

        # --- Get Profile Options ---
        username = self.current_selected_profile.get('username', "Player")
        memory_gb = self.current_selected_profile.get('memory_gb', 2)
        jvm_arguments = [f"-Xmx{memory_gb}G", f"-Xms{memory_gb}G"]
        # Add profile specific JVM args later if needed

        # --- Set Launch Options ---
        options = {
            "username": username,
            "uuid": str(uuid.uuid4()), # Generate new UUID each time for offline
            "token": "",
            "jvmArguments": jvm_arguments
        }
        
        # Завжди додаємо опції для офлайн-режиму (перевірку прапорця видалено)
        options["customLaunchOptions"] = {
            "--quickPlayMultiplayer": "",
            "--quickPlayRealms": "",
            "--demo": "",
            # Додаткові опції для вимикання перевірки акаунта
            "--skipMultiplayerWarning": ""
        }

        try:
            self.status_label.setText(f"Generating launch command...")
            QApplication.processEvents()
            command = minecraft_launcher_lib.command.get_minecraft_command(version_id, self.minecraft_dir, options)
            print("Launch Command:", command)

            self.status_label.setText(f"Starting {profile_name}...")
            QApplication.processEvents()
            # Use Popen for non-blocking launch
            subprocess.Popen(command)
            self.status_label.setText(f"{profile_name} launched! You can close the launcher.")
            # Optionally close the launcher after successful launch:
            # self.close()
        except Exception as e:
            error_message = f"Failed to launch {profile_name}: {e}"
            print(error_message)
            QMessageBox.critical(self, "Launch Failed", error_message)
            self.status_label.setVisible(False)

        # Re-enable button and update state AFTER launch attempt
        self.action_button.setEnabled(True)
        if self.current_selected_profile: # Check if profile still exists
             self.action_button.setText(f"Launch {self.current_selected_profile.get('name')}")
        else:
             self.action_button.setText("Select or create a profile")
             self.action_button.setEnabled(False)

    # --- Installation --- 
    def start_installation_for_profile(self, profile):
        """Starts the installation process for the given profile's version."""
        if self.install_thread and self.install_thread.isRunning():
            QMessageBox.warning(self, "Busy", "Another installation is already in progress.")
            return

        version_id = profile.get('version_id')
        profile_name = profile.get('name', 'Unknown')
        if not version_id:
            QMessageBox.critical(self, "Error", f"Profile '{profile_name}' has no version selected!")
            return

        print(f"Starting installation for {version_id}...")

        # Disable UI elements
        self.action_button.setEnabled(False)
        self.action_button.setText(f"Installing {version_id}...")
        self.profile_combo.setEnabled(False)
        self.add_profile_button.setEnabled(False)
        self.edit_profile_button.setEnabled(False)
        self.delete_profile_button.setEnabled(False)

        # Show progress UI
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(0) # Indeterminate until max is set
        self.progress_bar.setVisible(True)
        self.status_label.setText(f"Preparing to install {version_id}...")
        self.status_label.setVisible(True)
        QApplication.processEvents()

        # Create and start thread
        self.install_thread = InstallThread(version_id, self.minecraft_dir)

        # Connect signals to slots
        self.install_thread.progress_update.connect(self.update_install_progress)
        self.install_thread.progress_max_update.connect(self.set_install_progress_max)
        self.install_thread.status_update.connect(self.update_install_status)
        self.install_thread.finished_signal.connect(self.on_install_finished)

        self.install_thread.start()

    # --- Profile Management Methods ---
    def add_profile(self):
        dialog = ProfileDialog(parent=self, minecraft_dir=self.minecraft_dir)
        result = dialog.exec()

        if result == QDialog.Accepted:
            new_data = dialog.get_profile_data() # Already validated in accept()
            if new_data:
                 # Check for duplicate name (case-insensitive)
                existing_names = [p.get('name', '').lower() for p in self.profiles]
                if new_data['name'].lower() in existing_names:
                    QMessageBox.warning(self, "Error", f"A profile named '{new_data['name']}' already exists.")
                    return # Or re-open dialog?

                self.profiles.append(new_data)
                self.last_selected_profile_name = new_data['name'] # Select new profile
                self.update_profile_list() # Refresh combo box
                # Save settings immediately? Or wait for close?
                # save_settings(self.settings)

    def edit_profile(self):
        if not self.current_selected_profile:
            return
        
        profile_to_edit = self.current_selected_profile
        profile_original_name = profile_to_edit.get('name')

        dialog = ProfileDialog(parent=self, existing_profile=profile_to_edit, minecraft_dir=self.minecraft_dir)
        result = dialog.exec()

        if result == QDialog.Accepted:
            updated_data = dialog.get_profile_data() # Already validated
            if updated_data:
                # Check for duplicate name if name changed (case-insensitive)
                if updated_data['name'].lower() != profile_original_name.lower():
                    existing_names = [p.get('name', '').lower() for p in self.profiles if p is not profile_to_edit]
                    if updated_data['name'].lower() in existing_names:
                        QMessageBox.warning(self, "Error", f"Another profile named '{updated_data['name']}' already exists.")
                        return
                
                # Find the profile in the list and update it
                # This is safer than assuming self.current_selected_profile is still correct if list changes
                for i, p in enumerate(self.profiles):
                    if p is profile_to_edit: # Use identity check
                        self.profiles[i] = updated_data
                        break
                
                self.last_selected_profile_name = updated_data['name'] # Select edited profile
                self.update_profile_list() # Refresh combo box
                # Save settings immediately? Or wait for close?
                # save_settings(self.settings)

    def delete_profile(self):
        if not self.current_selected_profile:
            return
        profile_name = self.current_selected_profile.get('name')
        reply = QMessageBox.question(self, 'Delete Profile', 
                                       f"Are you sure you want to delete the profile '{profile_name}'?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                       QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            print(f"Deleting profile: {profile_name}")
            self.profiles.remove(self.current_selected_profile)
            self.current_selected_profile = None # Deselect
            self.last_selected_profile_name = None # Clear last selected if it was deleted
            self.update_profile_list() # Update combo box
            # No need to save settings here, will be saved on closeEvent
            # Or call save_settings(self.settings) if immediate persistence is desired
            self.on_profile_selected(self.profile_combo.currentIndex()) # Update UI state

    def closeEvent(self, event):
        """Save settings when the window is closed."""
        # Update the last selected profile name before saving
        if self.current_selected_profile:
            self.settings['last_selected_profile'] = self.current_selected_profile.get('name')
        else:
             self.settings['last_selected_profile'] = None
        # Ensure profiles are correctly stored back in settings dict
        self.settings['profiles'] = self.profiles 
        save_settings(self.settings)
        event.accept()

    def fix_version_for_offline(self):
        """Manually configure the selected profile's version for offline play."""
        if not self.current_selected_profile:
            QMessageBox.warning(self, "Warning", "Please select a profile first.")
            return
            
        version_id = self.current_selected_profile.get('version_id')
        if not version_id:
            QMessageBox.warning(self, "Warning", "Selected profile has no Minecraft version.")
            return
            
        # Проверяем, установлена ли версия
        version_file_path = os.path.join(self.minecraft_dir, 'versions', version_id, f'{version_id}.json')
        if not os.path.exists(version_file_path):
            reply = QMessageBox.question(self, "Version Not Installed", 
                                       f"The version {version_id} is not installed. Install it now?", 
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.start_installation_for_profile(self.current_selected_profile)
            return
            
        # Вызываем configure_offline_mode
        if self.configure_offline_mode(version_id):
            QMessageBox.information(self, "Success", 
                                   f"Successfully configured {version_id} for offline multiplayer.\n\n"
                                   f"Now you can launch the game and play multiplayer on servers with 'online-mode=false' or create a LAN world.")

    def update_profile_field(self, field, value):
        """Updates a field in the currently selected profile."""
        if not self.current_selected_profile:
            return
            
        # Update the value in the profile
        self.current_selected_profile[field] = value
        
        # Save settings to persist the change
        save_settings(self.settings)

if __name__ == "__main__":
    # Attempt to install requirements if libraries are missing
    try:
        import PySide6
        import minecraft_launcher_lib
    except ImportError:
        print("Required libraries not found. Attempting to install...")
        try:
            # Try using python -m pip
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
            print("Libraries installed successfully. Please restart the launcher.")
        except Exception as install_error:
            print(f"Failed to install libraries: {install_error}")
            print("Please install dependencies manually using: python -m pip install -r requirements.txt")
        sys.exit(1) # Exit after attempting install

    app = QApplication(sys.argv)

    # Apply QDarkStyleSheet
    try:
        import qdarkstyle
        app.setStyleSheet(qdarkstyle.load_stylesheet()) # Use 'load_stylesheet' for PySide6/PyQt6
    except ImportError:
        print("QDarkStyleSheet not found. Launcher will use the default system theme.")

    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 