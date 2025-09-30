# دليل أوامر Python الأساسية على Windows

## 1. فحص وإدارة إصدارات Python

### فحص الإصدار المثبت
```cmd
# فحص إصدار Python
python --version
# أو
python -V

# فحص جميع الإصدارات المثبتة (إذا كان لديك Python Launcher)
py -0
py --list

# فحص إصدار pip
pip --version
```

### تثبيت Python
```cmd
# تحميل من الموقع الرسمي: https://www.python.org/downloads/
# أو باستخدام Chocolatey
choco install python

# أو باستخدام Winget
winget install Python.Python.3.11

# أو باستخدام Microsoft Store
# ابحث عن "Python" في Microsoft Store
```

### Python Launcher للويندوز
```cmd
# تشغيل أحدث إصدار Python 3
py

# تشغيل إصدار محدد
py -3.9
py -3.11

# تشغيل أحدث إصدار Python 2 (إذا كان مثبتاً)
py -2
```

## 2. إنشاء وإدارة المشاريع

### إنشاء مجلد المشروع
```cmd
# إنشاء مجلد جديد
mkdir my_project

# الانتقال إلى المجلد
cd my_project

# إنشاء هيكل المشروع الأساسي
mkdir src
mkdir tests
mkdir docs
echo. > README.md
echo. > requirements.txt

# أو باستخدام PowerShell
New-Item -ItemType Directory -Name "src", "tests", "docs"
New-Item -ItemType File -Name "README.md", "requirements.txt"
```

## 3. البيئات الافتراضية (Virtual Environments)

### إنشاء بيئة افتراضية
```cmd
# باستخدام venv (الطريقة المفضلة)
python -m venv venv
# أو
py -m venv venv
# أو
py -3.11 -m venv myproject_env

# باستخدام virtualenv (يحتاج تثبيت أولاً)
pip install virtualenv
virtualenv venv
```

### تفعيل البيئة الافتراضية
```cmd
# في Command Prompt
venv\Scripts\activate

# في PowerShell
venv\Scripts\Activate.ps1
# أو
.\venv\Scripts\Activate.ps1

# للتأكد من التفعيل، يجب أن ترى (venv) في بداية السطر
# (venv) C:\path\to\my_project>
```

### حل مشكلة تفعيل PowerShell
```powershell
# إذا ظهرت رسالة خطأ في PowerShell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# بعد ذلك يمكنك تفعيل البيئة
.\venv\Scripts\Activate.ps1
```

### إلغاء تفعيل البيئة الافتراضية
```cmd
# إلغاء التفعيل
deactivate
```

### حذف البيئة الافتراضية
```cmd
# إلغاء التفعيل أولاً ثم حذف المجلد
deactivate
rmdir /s venv

# في PowerShell
Remove-Item -Recurse -Force venv
```

## 4. إدارة المكتبات والحزم

### تثبيت المكتبات
```cmd
# تثبيت مكتبة واحدة
pip install package_name

# تثبيت إصدار محدد
pip install package_name==1.2.3

# تثبيت أحدث إصدار متوافق
pip install "package_name>=1.0,<2.0"

# تثبيت من ملف requirements.txt
pip install -r requirements.txt

# تثبيت للتطوير (إذا كان المشروع له setup.py)
pip install -e .

# تثبيت مع تجاهل الـ cache
pip install --no-cache-dir package_name
```

### إدارة المكتبات
```cmd
# عرض المكتبات المثبتة
pip list

# عرض المكتبات القديمة
pip list --outdated

# عرض معلومات مكتبة
pip show package_name

# تحديث مكتبة
pip install --upgrade package_name

# تحديث pip نفسه
python -m pip install --upgrade pip

# إلغاء تثبيت مكتبة
pip uninstall package_name

# إنشاء ملف requirements.txt
pip freeze > requirements.txt
```

## 5. تحديد إصدار Python للمشروع

### استخدام Python Launcher
```cmd
# إنشاء ملف py.ini في مجلد المشروع
echo [defaults] > py.ini
echo python=3.11 >> py.ini

# أو إنشاء ملف .python-version
echo 3.11.0 > .python-version
```

### استخدام pyenv-win لإدارة إصدارات متعددة
```cmd
# تثبيت pyenv-win
git clone https://github.com/pyenv-win/pyenv-win.git %USERPROFILE%\.pyenv

# إضافة إلى PATH في متغيرات البيئة:
# %USERPROFILE%\.pyenv\pyenv-win\bin
# %USERPROFILE%\.pyenv\pyenv-win\shims

# تثبيت إصدار محدد من Python
pyenv install 3.11.0

# تحديد الإصدار للمشروع الحالي
pyenv local 3.11.0

# تحديد الإصدار العام
pyenv global 3.11.0

# عرض الإصدارات المتاحة
pyenv versions
```

## 6. تشغيل المشاريع

### تشغيل ملفات Python
```cmd
# تشغيل ملف Python
python script.py
# أو باستخدام Python Launcher
py script.py
py -3.11 script.py

# تشغيل ملف كوحدة
python -m module_name

# تشغيل مع معاملات
python script.py arg1 arg2 --option value

# تشغيل في الخلفية (Windows لا يدعم nohup مباشرة)
start /B python script.py
```

### تشغيل الخادم المحلي
```cmd
# Django
python manage.py runserver
python manage.py runserver 127.0.0.1:8000

# Flask
python app.py
# أو
set FLASK_APP=app.py
flask run
flask run --host=0.0.0.0 --port=5000

# FastAPI مع uvicorn
uvicorn main:app --reload
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 7. اختبار الكود

### تشغيل الاختبارات
```cmd
# باستخدام pytest
pip install pytest
pytest
pytest tests\
pytest -v

# باستخدام unittest المدمج
python -m unittest discover
python -m unittest test_file.py

# تشغيل اختبارات مع تغطية الكود
pip install coverage
coverage run -m pytest
coverage report
coverage html
```

## 8. أوامر مفيدة إضافية

### فحص جودة الكود
```cmd
# تثبيت أدوات فحص الكود
pip install flake8 black isort mypy

# فحص التنسيق مع flake8
flake8 src\

# تنسيق الكود مع black
black src\

# ترتيب المكتبات مع isort
isort src\

# فحص الأنواع مع mypy
mypy src\
```

### إدارة قواعد البيانات (Django)
```cmd
# إنشاء migrations
python manage.py makemigrations

# تطبيق migrations
python manage.py migrate

# إنشاء superuser
python manage.py createsuperuser

# تجميع الملفات الثابتة
python manage.py collectstatic
```

### مراقبة العمليات
```cmd
# عرض العمليات المفتوحة للبايثون
tasklist | findstr python

# قتل عملية Python (بحاجة لمعرف العملية)
taskkill /PID process_id /F
# أو قتل جميع عمليات Python
taskkill /IM python.exe /F

# مراقبة استخدام الموارد
# استخدم Task Manager أو Resource Monitor
```

## 9. المتغيرات البيئية

### تعيين المتغيرات البيئية
```cmd
# تعيين مؤقت في Command Prompt
set PYTHONPATH=C:\path\to\project
set DEBUG=True

# تعيين مؤقت في PowerShell
$env:PYTHONPATH = "C:\path\to\project"
$env:DEBUG = "True"

# تعيين دائم عبر واجهة Windows
# System Properties > Environment Variables

# أو باستخدام setx (دائم)
setx PYTHONPATH "C:\path\to\project"
setx DEBUG "True"

# استخدام ملف .env
pip install python-dotenv
echo DEBUG=True > .env
echo SECRET_KEY=your_secret_key >> .env
```

## 10. تحسين الأداء والتطوير

### تشغيل في الخلفية
```cmd
# تشغيل في الخلفية مع إخفاء النافذة
start /B /MIN python app.py

# أو إنشاء خدمة Windows (متقدم)
# يحتاج لأدوات مثل NSSM أو sc.exe

# باستخدام Task Scheduler لتشغيل تلقائي
schtasks /create /tn "MyPythonApp" /tr "python C:\path\to\app.py" /sc onstart
```

### مراقبة التغييرات وإعادة التشغيل
```cmd
# تثبيت watchdog
pip install watchdog[watchmedo]

# مراقبة التغييرات
watchmedo auto-restart --patterns="*.py" --recursive -- python app.py

# أو استخدام nodemon (يحتاج Node.js)
npm install -g nodemon
nodemon --exec python app.py
```

## 11. أدوات Windows المحددة

### Windows Subsystem for Linux (WSL)
```cmd
# تمكين WSL
wsl --install

# تشغيل Python في WSL
wsl python3 script.py
```

### استخدام Windows Terminal
```cmd
# تثبيت Windows Terminal من Microsoft Store
# يوفر tabs متعددة ودعم أفضل للألوان

# فتح PowerShell في Windows Terminal
wt powershell

# فتح Command Prompt
wt cmd
```

### إنشاء ملفات Batch للأتمتة
```batch
@echo off
REM activate_and_run.bat
call venv\Scripts\activate.bat
python app.py
pause
```

## مثال كامل: إنشاء مشروع Django

```cmd
REM 1. إنشاء مجلد المشروع
mkdir django_project
cd django_project

REM 2. إنشاء البيئة الافتراضية
python -m venv venv
venv\Scripts\activate

REM 3. تثبيت Django
pip install django

REM 4. إنشاء مشروع Django
django-admin startproject mysite .

REM 5. إنشاء تطبيق
python manage.py startapp myapp

REM 6. تشغيل الخادم
python manage.py migrate
python manage.py runserver

REM 7. حفظ المتطلبات
pip freeze > requirements.txt
```

## مثال PowerShell Script
```powershell
# setup_project.ps1
param(
    [string]$ProjectName = "my_project",
    [string]$PythonVersion = "3.11"
)

# إنشاء مجلد المشروع
New-Item -ItemType Directory -Name $ProjectName -Force
Set-Location $ProjectName

# إنشاء البيئة الافتراضية
py -$PythonVersion -m venv venv

# تفعيل البيئة
.\venv\Scripts\Activate.ps1

# إنشاء ملفات المشروع الأساسية
@"
flask
requests
pytest
"@ | Out-File -FilePath "requirements.txt" -Encoding UTF8

# تثبيت المتطلبات
pip install -r requirements.txt

Write-Host "تم إنشاء المشروع $ProjectName بنجاح!" -ForegroundColor Green
```

## نصائح مهمة لـ Windows

- **استخدم Windows Terminal** للحصول على تجربة أفضل
- **فعل البيئة الافتراضية دائماً** قبل العمل
- **انتبه لمسارات الملفات** (استخدم \ بدلاً من /)
- **استخدم PowerShell** للنصوص البرمجية المتقدمة
- **احتفظ بنسخ احتياطية** من البيئة الافتراضية عبر requirements.txt
- **استخدم .gitignore** لاستثناء venv\ من Git
- **فعل Windows Defender Exclusions** لمجلدات Python لتحسين الأداء

## الاختلافات الرئيسية عن Linux

| الجانب | Linux | Windows |
|--------|-------|---------|
| تفعيل البيئة الافتراضية | `source venv/bin/activate` | `venv\Scripts\activate` |
| فاصل المسارات | `/` | `\` |
| متغيرات البيئة | `export VAR=value` | `set VAR=value` |
| تشغيل في الخلفية | `nohup python app.py &` | `start /B python app.py` |
| مراقبة العمليات | `ps aux \| grep python` | `tasklist \| findstr python` |
| قتل العملية | `pkill -f python` | `taskkill /IM python.exe /F` |