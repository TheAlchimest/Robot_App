# دليل شامل للتعامل مع Raspberry Pi 5

## 1. الإعداد الأولي

### متطلبات التشغيل
```bash
# الحد الأدنى للمتطلبات:
# - بطاقة microSD بسعة 16GB أو أكثر (Class 10 أو أفضل)
# - محول طاقة USB-C 5V/5A (27W) رسمي
# - كيبل HDMI أو micro HDMI للعرض
# - لوحة مفاتيح وفأرة USB أو Bluetooth
```

### تحضير بطاقة SD
```bash
# تحميل Raspberry Pi Imager
# من: https://www.raspberrypi.org/software/

# أو استخدام dd في Linux
sudo dd if=raspios-lite.img of=/dev/sdX bs=4M status=progress
sync
```

### التشغيل الأول
```bash
# 1. إدراج بطاقة SD
# 2. توصيل الكيبلات (HDMI، USB، Ethernet اختياري)
# 3. توصيل الطاقة أخيراً

# عند التشغيل الأول، سيظهر معالج الإعداد
# اتبع الخطوات لتعيين:
# - المنطقة الزمنية واللغة
# - كلمة مرور المستخدم pi
# - شبكة WiFi
# - تحديثات النظام
```

## 2. الأوامر الأساسية للنظام

### معلومات النظام
```bash
# معلومات النظام والأجهزة
cat /proc/cpuinfo          # معلومات المعالج
cat /proc/meminfo          # معلومات الذاكرة
vcgencmd measure_temp      # درجة حرارة المعالج
vcgencmd measure_volts     # فولتية النظام
vcgencmd get_throttled     # حالة التحكم في الأداء

# معلومات نظام التشغيل
uname -a                   # معلومات kernel
cat /etc/os-release        # إصدار نظام التشغيل
df -h                      # استخدام القرص
free -h                    # استخدام الذاكرة
uptime                     # وقت تشغيل النظام

# معلومات GPIO وواجهات الاتصال
pinout                     # خريطة GPIO
lsusb                      # أجهزة USB المتصلة
lspci                      # أجهزة PCI (في Pi 5)
```

### التحكم في النظام
```bash
# إعادة التشغيل والإيقاف
sudo reboot                # إعادة التشغيل
sudo shutdown -h now      # إيقاف فوري
sudo shutdown -r +10      # إعادة تشغيل بعد 10 دقائق

# إدارة الخدمات
sudo systemctl status service_name    # حالة خدمة
sudo systemctl start service_name     # تشغيل خدمة
sudo systemctl stop service_name      # إيقاف خدمة
sudo systemctl enable service_name    # تفعيل تشغيل تلقائي
sudo systemctl disable service_name   # إلغاء التشغيل التلقائي

# مراقبة العمليات والموارد
top                        # مراقبة العمليات
htop                       # مراقبة محسنة (يحتاج تثبيت)
ps aux                     # جميع العمليات
kill process_id            # قتل عملية
killall process_name       # قتل جميع العمليات بنفس الاسم
```

## 3. إعداد وتكوين النظام

### أداة raspi-config
```bash
# فتح أداة التكوين الرسمية
sudo raspi-config

# الخيارات الرئيسية:
# 1. System Options (خيارات النظام)
#    - تغيير كلمة المرور
#    - تعيين hostname
#    - تفعيل/إلغاء تفعيل auto-login
# 2. Display Options (خيارات العرض)
#    - دقة الشاشة
#    - overscan
# 3. Interface Options (واجهات الاتصال)
#    - SSH, VNC, SPI, I2C, Camera, etc.
# 4. Performance Options (خيارات الأداء)
#    - GPU memory split
#    - Overclocking (محدود في Pi 5)
# 5. Localisation Options (الإعدادات المحلية)
#    - المنطقة الزمنية، اللغة، لوحة المفاتيح
```

### تحديث النظام
```bash
# تحديث قائمة الحزم
sudo apt update

# ترقية الحزم المثبتة
sudo apt upgrade -y

# ترقية شاملة للنظام
sudo apt full-upgrade -y

# تنظيف الحزم غير المستخدمة
sudo apt autoremove -y
sudo apt autoclean

# تحديث firmware
sudo rpi-update

# إعادة تشغيل بعد تحديث firmware
sudo reboot
```

## 4. إدارة الشبكة

### WiFi
```bash
# فحص شبكات WiFi المتاحة
sudo iwlist wlan0 scan | grep ESSID

# الاتصال بشبكة WiFi عبر سطر الأوامر
sudo wpa_passphrase "SSID" "password" >> /etc/wpa_supplicant/wpa_supplicant.conf

# إعادة تشغيل واجهة WiFi
sudo wpa_cli -i wlan0 reconfigure

# فحص حالة الاتصال
iwconfig wlan0
ip addr show wlan0
```

### Ethernet وإعدادات الشبكة
```bash
# فحص واجهات الشبكة
ip link show
ifconfig

# فحص عنوان IP
hostname -I
ip route show

# اختبار الاتصال
ping google.com
ping -c 4 192.168.1.1

# فحص منافذ الشبكة المفتوحة
netstat -tuln
ss -tuln
```

### SSH وVNC
```bash
# تفعيل SSH
sudo systemctl enable ssh
sudo systemctl start ssh

# تفعيل VNC
sudo systemctl enable vncserver-x11-serviced
sudo systemctl start vncserver-x11-serviced

# الاتصال من جهاز آخر
ssh pi@raspberry_pi_ip
# VNC: استخدم VNC Viewer مع IP address

# تغيير منفذ SSH (للأمان)
sudo nano /etc/ssh/sshd_config
# غير Port 22 إلى رقم آخر
sudo systemctl restart ssh
```

## 5. إدارة GPIO والأجهزة

### أوامر GPIO الأساسية
```bash
# عرض خريطة GPIO
pinout

# استخدام gpio utility
gpio readall               # قراءة حالة جميع المنافذ
gpio read pin_number       # قراءة منفذ محدد
gpio write pin_number value # كتابة قيمة (0 أو 1)
gpio mode pin_number out   # تعيين المنفذ كخرج
gpio mode pin_number in    # تعيين المنفذ كدخل

# أمثلة عملية
gpio mode 18 out          # تعيين GPIO 18 كخرج
gpio write 18 1           # تشغيل LED على GPIO 18
gpio write 18 0           # إطفاء LED
```

### I2C وSPI
```bash
# تفعيل I2C
sudo raspi-config # Interface Options > I2C > Enable

# فحص أجهزة I2C
sudo i2cdetect -y 1

# تثبيت أدوات I2C
sudo apt install i2c-tools

# تفعيل SPI
sudo raspi-config # Interface Options > SPI > Enable

# اختبار SPI
ls /dev/spi*
```

### الكاميرا
```bash
# تفعيل الكاميرا (Pi 5 يستخدم libcamera)
sudo raspi-config # Interface Options > Camera > Enable

# أوامر libcamera (Pi 5)
libcamera-hello              # عرض معاينة
libcamera-still -o image.jpg # التقاط صورة
libcamera-vid -t 10000 -o video.h264 # تسجيل فيديو 10 ثواني

# معاينة مع تأثيرات
libcamera-hello --qt-preview
```

## 6. الصوت والفيديو

### إعداد الصوت
```bash
# فحص أجهزة الصوت
aplay -l
arecord -l

# تعيين جهاز الصوت الافتراضي
sudo raspi-config # System Options > Audio

# تشغيل ملف صوتي
aplay audio_file.wav
speaker-test -t sine -f 1000 -l 1

# تسجيل صوت
arecord -D plughw:1,0 -f cd recording.wav
```

### إعداد الفيديو والشاشة
```bash
# فحص دقة الشاشة المتاحة
tvservice -m CEA
tvservice -m DMT

# تعيين دقة محددة في config.txt
sudo nano /boot/firmware/config.txt
# أضف:
# hdmi_mode=82    # 1920x1080 60Hz
# hdmi_group=2    # DMT

# تدوير الشاشة
display_rotate=1  # 90 درجة
display_rotate=2  # 180 درجة
display_rotate=3  # 270 درجة
```

## 7. إدارة التخزين

### بطاقة SD وUSB
```bash
# فحص أجهزة التخزين
lsblk
fdisk -l

# mount وunmount
sudo mount /dev/sda1 /mnt/usb
sudo umount /mnt/usb

# إنشاء نقطة mount دائمة
sudo mkdir /mnt/external
sudo nano /etc/fstab
# أضف: /dev/sda1 /mnt/external ext4 defaults 0 2

# فحص حالة SD card
sudo dmesg | grep mmc
```

### إدارة المساحة
```bash
# فحص استخدام المساحة
df -h
du -sh /*
du -sh ~/.* 2>/dev/null

# تنظيف ملفات مؤقتة
sudo apt clean
sudo apt autoremove
rm -rf ~/.cache/*

# توسيع filesystem (بعد زيادة حجم SD)
sudo raspi-config # Advanced Options > Expand Filesystem
```

## 8. الأمان والمراقبة

### تأمين النظام
```bash
# تغيير كلمة مرور المستخدم pi
passwd

# إنشاء مستخدم جديد
sudo adduser newuser
sudo usermod -aG sudo newuser

# تعطيل المستخدم pi (بعد إنشاء مستخدم آخر)
sudo passwd -l pi

# تكوين firewall
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
```

### مراقبة النظام
```bash
# مراقبة درجة الحرارة
watch -n 1 vcgencmd measure_temp

# مراقبة استخدام المعالج والذاكرة
htop
iotop    # لمراقبة I/O

# سجلات النظام
journalctl -f           # سجلات مباشرة
journalctl -u service   # سجلات خدمة محددة
dmesg                   # سجلات kernel

# فحص حالة النظام
vcgencmd get_throttled
# 0x0 = كل شيء طبيعي
# 0x50000 = تحكم في الطاقة بسبب انخفاض الفولتية
```

## 9. إدارة الطاقة

### وضعيات الطاقة
```bash
# إيقاف WiFi لتوفير الطاقة
sudo iwconfig wlan0 txpower off

# إيقاف Bluetooth
sudo systemctl disable bluetooth
sudo systemctl stop bluetooth

# تقليل سرعة المعالج
echo powersave | sudo tee /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor

# إيقاف LEDs
echo 0 | sudo tee /sys/class/leds/led0/brightness  # PWR LED
echo 0 | sudo tee /sys/class/leds/led1/brightness  # ACT LED
```

### UPS وإدارة الطاقة المتقدمة
```bash
# مراقبة فولتية الطاقة
vcgencmd measure_volts core
vcgencmd measure_volts sdram_c

# إعداد إيقاف آمن عند انقطاع الطاقة (يحتاج UPS HAT)
# مثال لـ GPIO shutdown script
sudo nano /etc/rc.local
# أضف قبل exit 0:
# python3 /home/pi/shutdown_monitor.py &
```

## 10. التطوير والبرمجة

### تثبيت بيئات التطوير
```bash
# Python (مثبت افتراضياً)
python3 --version
pip3 install --upgrade pip

# Node.js
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install nodejs

# Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker pi

# VS Code (ARM64)
wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg
sudo install -o root -g root -m 644 packages.microsoft.gpg /etc/apt/trusted.gpg.d/
sudo sh -c 'echo "deb [arch=arm64,armhf,armv7l signed-by=/etc/apt/trusted.gpg.d/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" > /etc/apt/sources.list.d/vscode.list'
sudo apt update
sudo apt install code
```

### GPIO Programming Libraries
```bash
# Python GPIO libraries
pip3 install RPi.GPIO
pip3 install gpiozero

# مثال Python بسيط لـ LED
cat << EOF > led_blink.py
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.OUT)

for i in range(10):
    GPIO.output(18, GPIO.HIGH)
    time.sleep(1)
    GPIO.output(18, GPIO.LOW)
    time.sleep(1)

GPIO.cleanup()
EOF

python3 led_blink.py
```

## 11. خدمات مفيدة

### Apache/Nginx Web Server
```bash
# تثبيت Apache
sudo apt install apache2
sudo systemctl enable apache2
sudo systemctl start apache2

# أو Nginx
sudo apt install nginx
sudo systemctl enable nginx
sudo systemctl start nginx

# PHP support
sudo apt install php libapache2-mod-php
```

### Database Servers
```bash
# MySQL/MariaDB
sudo apt install mariadb-server
sudo mysql_secure_installation

# SQLite (مثبت افتراضياً)
sqlite3 database.db

# PostgreSQL
sudo apt install postgresql postgresql-contrib
```

### File Sharing (Samba)
```bash
# تثبيت Samba
sudo apt install samba samba-common-bin

# تكوين مجلد مشارك
sudo nano /etc/samba/smb.conf
# أضف في النهاية:
[shared]
path = /home/pi/shared
writeable = yes
create mask = 0777
directory mask = 0777
public = no

# إضافة مستخدم Samba
sudo smbpasswd -a pi
sudo systemctl restart smbd
```

## 12. استكشاف الأخطاء

### مشاكل شائعة وحلولها
```bash
# مشكلة عدم التشغيل
# 1. فحص LED الطاقة (أحمر مستمر = طاقة جيدة)
# 2. فحص LED النشاط (أخضر يرمش = قراءة SD card)
# 3. فحص كابل الطاقة (5V/5A للـ Pi 5)

# مشكلة ارتفاع درجة الحرارة
vcgencmd measure_temp
# إذا كانت > 80°C، حتاج لمروحة أو heatsink

# مشكلة Wi-Fi لا يعمل
sudo iwconfig wlan0 power off  # إيقاف power management
sudo service networking restart

# مشكلة SD card corruption
# استخدم fsck لفحص وإصلاح
sudo fsck /dev/mmcblk0p2

# فحص logs للأخطاء
dmesg | tail -20
journalctl -xe
```

### أدوات التشخيص
```bash
# تشغيل تشخيص شامل
cat << EOF > pi5_diagnostics.sh
#!/bin/bash
echo "=== Raspberry Pi 5 Diagnostics ==="
echo "Date: $(date)"
echo "Uptime: $(uptime)"
echo "Temperature: $(vcgencmd measure_temp)"
echo "Throttle status: $(vcgencmd get_throttled)"
echo "Memory: $(free -h)"
echo "Disk usage: $(df -h /)"
echo "Network interfaces:"
ip addr show | grep -E "inet|wlan|eth"
echo "==================================="
EOF

chmod +x pi5_diagnostics.sh
./pi5_diagnostics.sh
```

## نصائح مهمة للـ Raspberry Pi 5

1. **استخدم محول طاقة رسمي 27W** لتجنب مشاكل انخفاض الفولتية
2. **استخدم بطاقة SD عالية الجودة** Class 10 أو أفضل
3. **ثبت heatsink أو مروحة** لتبريد أفضل
4. **احتفظ بنسخ احتياطية** من بطاقة SD بانتظام
5. **استخدم UPS** للمشاريع المهمة
6. **تابع التحديثات** لتحسين الأداء والاستقرار

## ميزات جديدة في Pi 5
- **معالج Broadcom BCM2712** رباعي النوى 2.4GHz Cortex-A76
- **ذاكرة LPDDR4X** 4GB أو 8GB
- **منفذ PCIe 2.0** للتوسعات
- **منفذان micro HDMI** بدقة 4K@60Hz
- **منافذ USB 3.0** محسنة
- **PoE+ support** عبر HAT منفصل