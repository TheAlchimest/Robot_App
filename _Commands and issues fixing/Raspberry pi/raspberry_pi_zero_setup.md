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
# Other Commands
sudo poweroff
