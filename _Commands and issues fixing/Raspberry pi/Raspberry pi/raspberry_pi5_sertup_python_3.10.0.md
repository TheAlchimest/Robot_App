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
pip install -r requirements.txt
```

### 8. Run Your Application

```bash
python your_app.py
```

---

## Important Notes for Zero 2 WH (512MB RAM)

When building heavy packages (like numpy, pandas, or opencv-python), you may need to increase swap space temporarily to avoid build failures:

```bash
# Temporarily increase swap to 1GB
sudo sed -i 's/^CONF_SWAPSIZE=.*/CONF_SWAPSIZE=1024/' /etc/dphys-swapfile
sudo dphys-swapfile setup
sudo dphys-swapfile swapon

# After installation, reduce back to 100MB to minimize SD card wear:
# sudo sed -i 's/^CONF_SWAPSIZE=.*/CONF_SWAPSIZE=100/' /etc/dphys-swapfile
# sudo dphys-swapfile setup
# sudo dphys-swapfile swapon
```

---

## Optional Packages

### If Your Project Uses OpenCV

**Lightest option:**
```bash
pip install opencv-python-headless==4.10.0.84
```

**Or use system package (faster installation but tied to system Python):**
```bash
sudo apt install -y python3-opencv
```

### For Audio/Microphone Support

```bash
sudo apt install -y portaudio19-dev && pip install pyaudio
```

**For SpeechRecognition:** Make sure to install ffmpeg and sox if needed:
```bash
sudo apt install -y ffmpeg sox
```

---

## Quick Troubleshooting

### SSL: CERTIFICATE_VERIFY_FAILED during pip

```bash
sudo timedatectl set-ntp true
sudo apt install -y --reinstall ca-certificates
sudo update-ca-certificates
```

### pip Complains About Package Format (like python-dotenv==)

You must specify a complete version number:
```bash
pip install python-dotenv==1.0.1
```

### Slow/Failed Wheel Builds

- Use piwheels (configured above)
- Temporarily increase swap space
- Look for lighter alternatives

---

## Automatic Startup on Boot (Optional)

If you want your script to run automatically:

### 1. Create systemd Service File

```bash
sudo nano /etc/systemd/system/myproject.service
```

### 2. Add the Following Content

```ini
[Unit]
Description=My Python 3.10 App
After=network-online.target

[Service]
User=pi
WorkingDirectory=/home/pi/apps/myproject
Environment="PATH=/home/pi/apps/myproject/.venv/bin"
ExecStart=/home/pi/apps/myproject/.venv/bin/python /home/pi/apps/myproject/your_app.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

### 3. Enable and Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable myproject --now
sudo systemctl status myproject
```

---

## Need Help?

If you need assistance, please provide:

- Contents of `requirements.txt`
- How to run your project (e.g., `python main.py` or `uvicorn...`, etc.)
- Whether you're running Bookworm or Bullseye

This will allow for step-by-step customization for your Zero 2 WH setup. 💪🐍📟