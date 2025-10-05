# Raspberry Pi Bluetooth Headset Connection Guide

## Overview

This comprehensive guide explains how to connect a Bluetooth headset to your Raspberry Pi, covering wired (USB and 3.5mm) and wireless (Bluetooth) options with step-by-step instructions and troubleshooting tips.

---

## 1. System Update (First Step)

Before anything else, open the terminal and run:

```bash
sudo apt update && sudo apt upgrade -y
```

---

## 2. Wired USB Headset

### Connect and Verify

1. Plug the headset into a USB port

2. Check if the device is detected:

```bash
aplay -l     # List audio output devices
arecord -l   # List audio input devices (microphones)
```

### Test Audio

```bash
aplay /usr/share/sounds/alsa/Front_Center.wav
```

### Set Device as Default (Temporary)

```bash
# Example: Use device hw:1,0
aplay -D hw:1,0 /usr/share/sounds/alsa/Front_Center.wav
```

### Set Device as Default (Permanent)

Create or edit the ALSA configuration file:

```bash
sudo nano /etc/asound.conf
```

Add the following (replace `card 1` based on your `aplay -l` output):

```ini
pcm.!default {
  type hw
  card 1
}
ctl.!default {
  type hw
  card 1
}
```

Save and exit (`Ctrl+X`, then `Y`, then `Enter`).

---

## 3. Wired 3.5mm Headset (Built-in Audio Jack)

If your Pi has a 3.5mm audio jack (some models output via HDMI or 3.5mm):

### Force 3.5mm Output

```bash
sudo raspi-config
```

Navigate to:
- **Advanced Options** → **Audio** → **Force 3.5mm** (or select appropriate output)

### Test Audio

```bash
aplay /usr/share/sounds/alsa/Front_Center.wav
```

---

## 4. Bluetooth Headset (Complete Setup)

### Requirements

- Bluetooth enabled on Raspberry Pi
- Basic Bluetooth packages (Bluez + PulseAudio or PipeWire)

### Step 1: Install Required Packages

```bash
sudo apt update
sudo apt install -y bluetooth bluez bluez-tools pulseaudio-module-bluetooth pavucontrol
```

### Step 2: Enable and Start Bluetooth Service

```bash
sudo systemctl enable bluetooth
sudo systemctl start bluetooth
```

Verify it's running:

```bash
systemctl status bluetooth
```

### Step 3: Enter Bluetooth Control Tool

```bash
bluetoothctl
```

Inside the interactive interface, run these commands one by one:

```
power on
agent on
default-agent
scan on
```

📌 **Important:** The MAC address of your headset will appear (format: `XX:XX:XX:XX:XX:XX`)

### Step 4: Pair and Connect

Once you see your headset's MAC address:

```
pair XX:XX:XX:XX:XX:XX
trust XX:XX:XX:XX:XX:XX
connect XX:XX:XX:XX:XX:XX
exit
```

You should hear a "Connected" sound from the headset or see a success message.

### Step 5: Set Headset as Default Audio Output

#### With GUI (Desktop Environment):

```bash
pavucontrol
```

- Under **Output Devices**, select your Bluetooth headset
- If it has a microphone, under **Input Devices**, select it

#### Without GUI (Headless):

```bash
pactl list short sinks
pactl set-default-sink <headset_sink_name>
```

### Step 6: Test Audio

Play a test sound:

```bash
aplay /usr/share/sounds/alsa/Front_Center.wav
```

Test microphone (if headset has one):

```bash
arecord -d 5 test.wav
aplay test.wav
```

---

## 5. Troubleshooting and Useful Commands

### Open ALSA Audio Settings

```bash
alsamixer
```

- Press `F6` to select the correct sound card
- Make sure nothing is muted (`MM` means muted → press `M` to unmute)

### View Audio Devices

```bash
aplay -l
arecord -l
pactl list short sinks
pactl list short sources
```

### Bluetooth Won't Connect?

Try restarting Bluetooth and PulseAudio services:

```bash
sudo systemctl restart bluetooth
pulseaudio --start
```

Then put your headset in pairing mode before running `scan on` again.

### Bluetooth Audio Profiles

Some Bluetooth headsets operate in two modes:

- **A2DP**: High-quality audio (music only, no microphone)
- **HSP/HFP**: Phone call mode (lower quality audio with microphone)

You can switch between them in `pavucontrol` or using `blueman` GUI.

---

## 6. Important Notes by Raspberry Pi Model

- **Raspberry Pi Zero (original)**: Requires external USB Bluetooth dongle (no built-in Bluetooth)
- **Raspberry Pi Zero W/2W**: Has built-in Bluetooth
- **Raspberry Pi 3/4/5**: Has built-in Bluetooth

**Audio Quality Note:** Bluetooth microphone quality may be limited due to protocol constraints (HSP/HFP). For better microphone quality, consider using a USB headset or USB audio card with external mic.

---

## 7. Automated Setup Script

Save time by using this Bash script that handles all setup steps automatically.

### Create the Script

```bash
nano bt-headset.sh
```

### Add the Following Code

```bash
#!/bin/bash

echo "🔄 Updating system..."
sudo apt update -y
sudo apt install -y bluetooth bluez bluez-tools pulseaudio-module-bluetooth pavucontrol

echo "✅ Bluetooth packages installed."

# Start bluetooth service
sudo systemctl enable bluetooth
sudo systemctl start bluetooth

echo "🔎 Launching bluetoothctl..."
echo "👉 Inside bluetoothctl, type these commands:"
echo "power on"
echo "agent on"
echo "default-agent"
echo "scan on"
echo "➡️ When you see your headset's MAC address, use these pairing commands:"
echo "pair XX:XX:XX:XX:XX:XX"
echo "trust XX:XX:XX:XX:XX:XX"
echo "connect XX:XX:XX:XX:XX:XX"
echo "exit"

bluetoothctl
```

### Make the Script Executable

```bash
chmod +x bt-headset.sh
```

### Run the Script

```bash
./bt-headset.sh
```

### After Pairing and Connecting

**With GUI:**

```bash
pavucontrol
```

Select your headset from **Output Devices**.

**Without GUI:**

```bash
pactl list short sinks
pactl set-default-sink <headset_name>
```

**Test audio:**

```bash
aplay /usr/share/sounds/alsa/Front_Center.wav
```

---

## 8. Advanced: Auto-Connect on Boot

To automatically connect to your Bluetooth headset on startup:

### Create Auto-Connect Script

```bash
nano ~/bt-autoconnect.sh
```

Add:

```bash
#!/bin/bash
sleep 10
MAC_ADDRESS="XX:XX:XX:XX:XX:XX"  # Replace with your headset's MAC
bluetoothctl power on
bluetoothctl connect $MAC_ADDRESS
```

### Make Executable

```bash
chmod +x ~/bt-autoconnect.sh
```

### Add to Crontab

```bash
crontab -e
```

Add this line:

```
@reboot /home/pi/bt-autoconnect.sh
```

---

## 9. Quick Reference Commands

### Basic Bluetooth Operations

```bash
# Power on Bluetooth
bluetoothctl power on

# List paired devices
bluetoothctl paired-devices

# Connect to device
bluetoothctl connect XX:XX:XX:XX:XX:XX

# Disconnect from device
bluetoothctl disconnect XX:XX:XX:XX:XX:XX

# Remove device
bluetoothctl remove XX:XX:XX:XX:XX:XX
```

### Audio Control Commands

```bash
# List audio outputs
pactl list short sinks

# Set default output
pactl set-default-sink <sink_name>

# Adjust volume
pactl set-sink-volume <sink_name> 80%

# Mute/unmute
pactl set-sink-mute <sink_name> toggle
```

---

## 10. Common Issues and Solutions

### Issue: "No Default Sink Available"

**Solution:**

```bash
pulseaudio -k
pulseaudio --start
```

### Issue: Audio Stuttering/Choppy

**Solutions:**

1. Reduce distance between Pi and headset
2. Minimize Wi-Fi interference (both use 2.4GHz)
3. Update system: `sudo apt update && sudo apt upgrade -y`
4. Check CPU usage: `top` (high CPU can cause audio issues)

### Issue: Headset Connects but No Audio

**Solution:**

```bash
# Switch to A2DP profile manually
pactl set-card-profile <card_id> a2dp_sink
```

### Issue: Can't Find Headset During Scan

**Solutions:**

1. Make sure headset is in pairing mode (usually flashing LED)
2. Ensure headset is not connected to another device
3. Restart Bluetooth:
   ```bash
   sudo systemctl restart bluetooth
   ```
4. Try scanning again in `bluetoothctl`

---

## 11. Performance Optimization for Low-Power Pi Models

For Raspberry Pi Zero/Zero W with limited resources:

### Edit PulseAudio Configuration

```bash
sudo nano /etc/pulse/daemon.conf
```

Find and modify:

```ini
; resample-method = speex-float-3
resample-method = trivial
```

This uses less CPU for audio resampling.

### Restart PulseAudio

```bash
pulseaudio -k
pulseaudio --start
```

---

## Summary

**For USB Headsets:** Plug in and configure with `alsamixer` or `/etc/asound.conf`

**For 3.5mm Headsets:** Use `raspi-config` to force analog output

**For Bluetooth Headsets:** Install packages → Enable Bluetooth → Use `bluetoothctl` to pair and connect → Set as default output with `pavucontrol` or `pactl`

**Automation:** Use the provided script to simplify setup and auto-connect on boot

Remember: PulseAudio must be running for Bluetooth audio to work properly! 🎧🔊

---

## Additional Resources

- [Raspberry Pi Audio Configuration](https://www.raspberrypi.org/documentation/configuration/audio-config.md)
- [BlueZ Documentation](http://www.bluez.org/)
- [PulseAudio Documentation](https://www.freedesktop.org/wiki/Software/PulseAudio/)
- [ALSA Project](https://www.alsa-project.org/)