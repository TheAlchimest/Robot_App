# Preparing Raspberry Pi Zero

## 1. Setup with Raspberry Pi Imager
- Download Raspberry Pi Imager: [Raspberry Pi Imager](https://www.raspberrypi.com/software/)  
- Make sure to use the **same Wi-Fi network** that the Raspberry Pi will use.  
- Connect the memory card to your computer.  
- Choose **Raspberry Pi OS (32-bit)** for Raspberry Pi Zero.  
- Select the storage card.  
- Click **Next** → then **Edit Settings** to configure the device.  

### General
- Configure hostname  
- Setup Wi-Fi network  
- Set time zone and keyboard layout  

### Services
- Enable **SSH**  

Click **Save** → then **Yes** to apply changes.  

----------------------
## 2. Access Raspberry Pi
Open terminal and connect via SSH:
```bash
ssh pi@raspberrypi   # or pi@[hostname]
Default password:23072009
----------------------
3. Enable VNC
sudo raspi-config
- From Interface Options → enable VNC.
- From System Options → set boot to Desktop GUI.
- (Optional) Allow autologin.
- Go back to main window → click Finish → reboot.
----------------------
4. Update System
sudo apt update
sudo apt upgrade
sudo reboot
----------------------

5. Remote Access with TigerVNC

- Use TigerVNC to login.

- From Network → Advanced Options:

	- Create Wireless Hotspot

		- Network name: raspzero_1_hotspot

		- WPA2 Password: 23072009

- From Network → Advanced Options → Edit Connections:

	- Set Hotspot connection priority = 0

	- Set Predefined Wi-Fi priority = 1
	
----------------------
# Raspberry Pi Python 3.10.0 Setup Guide

## Overview

Raspberry Pi OS (Bookworm) typically comes with Python 3.11. If your code is compatible with ≥3.10, you can install Python 3.10 specifically via pyenv. This ensures version 3.10 without breaking the system Python.

Reference: [ChatGPT Discussion](https://chatgpt.com/g/g-p-68dbef6461388191b5abbcda5304f3d3-raspberry-pi/c/68de3258-df10-8329-9ced-09262216e6b4)

---

## Installation Steps

### 1. Update System and Build Tools

```bash
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y git curl build-essential \
  libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev \
  libffi-dev liblzma-dev tk-dev libncursesw5-dev xz-utils
```

### 2. Install pyenv for User 'pi'

```bash
curl https://pyenv.run | bash
```

### 3. Link pyenv to Shell (bash)

```bash
echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"'               >> ~/.bashrc
echo 'eval "$(pyenv virtualenv-init -)"'    >> ~/.bashrc
exec $SHELL  # Or logout/login
```

### 4. Install Python 3.10

Choose the latest patch from the 3.10 series:

```bash
pyenv install 3.10.0
```

### 5. Create Project Directory and Virtual Environment

```bash
mkdir -p ~/apps/myproject && cd ~/apps/myproject
pyenv local 3.10.0
python -m venv .venv
source .venv/bin/activate
```

### 6. Configure pip for Speed with piwheels

```bash
python -m pip install --upgrade pip
pip config set global.index-url https://www.piwheels.org/simple
pip config set global.extra-index-url https://pypi.org/simple
```

### 7. Clone Project and Install Dependencies

```bash
git clone <YOUR_REPO_URL> .   # Or copy files manually
pip install -r req.txt
```

### 8. Run Your Application

```bash
python your_app.py
```

---
### 9. Run Your Application Any time

```bash
source .venv/bin/activate
python main.py
```