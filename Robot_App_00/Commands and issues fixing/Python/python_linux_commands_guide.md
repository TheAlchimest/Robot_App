# دليل أوامر Python الأساسية على Linux

## 1. فحص وإدارة إصدارات Python

### فحص الإصدار المثبت
```bash
# فحص إصدار Python 3
python3 --version
# أو
python3 -V

# فحص إصدار Python 2 (إذا كان مثبتاً)
python --version

# فحص جميع الإصدارات المثبتة
ls /usr/bin/python*
```

### تثبيت Python
```bash
# على Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv

# على CentOS/RHEL/Fedora
sudo yum install python3 python3-pip
# أو للإصدارات الأحدث
sudo dnf install python3 python3-pip

# على Arch Linux
sudo pacman -S python python-pip
```

## 2. إنشاء وإدارة المشاريع

### إنشاء مجلد المشروع
```bash
# إنشاء مجلد جديد
mkdir my_project

# الانتقال إلى المجلد
cd my_project

# إنشاء هيكل المشروع الأساسي
mkdir src tests docs
touch README.md requirements.txt
```

## 3. البيئات الافتراضية (Virtual Environments)

### إنشاء بيئة افتراضية
```bash
# باستخدام venv (الطريقة المفضلة)
python3 -m venv venv
# أو
python3 -m venv myproject_env

# باستخدام virtualenv (يحتاج تثبيت أولاً)
pip3 install virtualenv
virtualenv venv
```

### تفعيل البيئة الافتراضية
```bash
# تفعيل البيئة
source venv/bin/activate

# للتأكد من التفعيل، يجب أن ترى (venv) في بداية السطر
# (venv) user@hostname:~/my_project$
```

### إلغاء تفعيل البيئة الافتراضية
```bash
# إلغاء التفعيل
deactivate
```

### حذف البيئة الافتراضية
```bash
# إلغاء التفعيل أولاً ثم حذف المجلد
deactivate
rm -rf venv
```

## 4. إدارة المكتبات والحزم

### تثبيت المكتبات
```bash
# تثبيت مكتبة واحدة
pip install package_name

# تثبيت إصدار محدد
pip install package_name==1.2.3

# تثبيت أحدث إصدار متوافق
pip install 'package_name>=1.0,<2.0'

# تثبيت من ملف requirements.txt
pip install -r requirements.txt

# تثبيت للتطوير (إذا كان المشروع له setup.py)
pip install -e .
```

### إدارة المكتبات
```bash
# عرض المكتبات المثبتة
pip list

# عرض معلومات مكتبة
pip show package_name

# البحث عن مكتبة
pip search package_name

# تحديث مكتبة
pip install --upgrade package_name

# إلغاء تثبيت مكتبة
pip uninstall package_name

# إنشاء ملف requirements.txt
pip freeze > requirements.txt
```

## 5. تحديد إصدار Python للمشروع

### استخدام python-version files
```bash
# إنشاء ملف لتحديد إصدار Python
echo "3.9.7" > .python-version
```

### استخدام pyenv لإدارة إصدارات متعددة
```bash
# تثبيت pyenv
curl https://pyenv.run | bash

# إعادة تحميل الـ shell
exec $SHELL

# تثبيت إصدار محدد من Python
pyenv install 3.9.7

# تحديد الإصدار للمشروع الحالي
pyenv local 3.9.7

# تحديد الإصدار العام
pyenv global 3.9.7

# عرض الإصدارات المتاحة
pyenv versions
```

## 6. تشغيل المشاريع

### تشغيل ملفات Python
```bash
# تشغيل ملف Python
python3 script.py
# أو إذا كانت البيئة الافتراضية مفعلة
python script.py

# تشغيل ملف كوحدة
python3 -m module_name

# تشغيل مع معاملات
python3 script.py arg1 arg2 --option value
```

### تشغيل الخادم المحلي
```bash
# Django
python3 manage.py runserver
python3 manage.py runserver 0.0.0.0:8000

# Flask
python3 app.py
# أو
flask run
export FLASK_APP=app.py
flask run --host=0.0.0.0 --port=5000

# FastAPI مع uvicorn
uvicorn main:app --reload
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 7. اختبار الكود

### تشغيل الاختبارات
```bash
# باستخدام pytest
pip install pytest
pytest
pytest tests/
pytest -v  # verbose mode

# باستخدام unittest المدمج
python3 -m unittest discover
python3 -m unittest test_file.py

# تشغيل اختبارات مع تغطية الكود
pip install coverage
coverage run -m pytest
coverage report
coverage html  # إنشاء تقرير HTML
```

## 8. أوامر مفيدة إضافية

### فحص جودة الكود
```bash
# تثبيت أدوات فحص الكود
pip install flake8 black isort mypy

# فحص التنسيق مع flake8
flake8 src/

# تنسيق الكود مع black
black src/

# ترتيب المكتبات مع isort
isort src/

# فحص الأنواع مع mypy
mypy src/
```

### إدارة قواعد البيانات (Django)
```bash
# إنشاء migrations
python3 manage.py makemigrations

# تطبيق migrations
python3 manage.py migrate

# إنشاء superuser
python3 manage.py createsuperuser

# تجميع الملفات الثابتة
python3 manage.py collectstatic
```

### مراقبة العمليات
```bash
# عرض العمليات المفتوحة للبايثون
ps aux | grep python

# قتل عملية Python
pkill -f "python script.py"

# مراقبة استخدام الموارد
top -p $(pgrep python)
```

## 9. المتغيرات البيئية

### تعيين المتغيرات البيئية
```bash
# تعيين مؤقت
export PYTHONPATH=/path/to/project
export DEBUG=True

# تعيين دائم في ~/.bashrc أو ~/.profile
echo 'export PYTHONPATH=/path/to/project' >> ~/.bashrc
source ~/.bashrc

# استخدام ملف .env
pip install python-dotenv
# إنشاء ملف .env
echo "DEBUG=True" > .env
echo "SECRET_KEY=your_secret_key" >> .env
```

## 10. تحسين الأداء والتطوير

### تشغيل في الخلفية
```bash
# تشغيل في الخلفية
nohup python3 app.py &

# مع إعادة توجيه المخرجات
nohup python3 app.py > output.log 2>&1 &

# باستخدام screen
screen -S myapp
python3 app.py
# اضغط Ctrl+A ثم D للخروج
# للعودة: screen -r myapp
```

### مراقبة التغييرات وإعادة التشغيل
```bash
# تثبيت watchdog
pip install watchdog

# أو استخدام nodemon (يحتاج Node.js)
npm install -g nodemon
nodemon --exec python3 app.py
```

## مثال كامل: إنشاء مشروع Django

```bash
# 1. إنشاء مجلد المشروع
mkdir django_project && cd django_project

# 2. إنشاء البيئة الافتراضية
python3 -m venv venv
source venv/bin/activate

# 3. تثبيت Django
pip install django

# 4. إنشاء مشروع Django
django-admin startproject mysite .

# 5. إنشاء تطبيق
python3 manage.py startapp myapp

# 6. تشغيل الخادم
python3 manage.py migrate
python3 manage.py runserver

# 7. حفظ المتطلبات
pip freeze > requirements.txt
```

## نصائح مهمة

- **استخدم دائماً البيئات الافتراضية** لتجنب تضارب المكتبات
- **احتفظ بملف requirements.txt محدث** للمشاركة مع الفريق
- **استخدم .gitignore** لاستثناء البيئة الافتراضية من Git
- **فعل البيئة الافتراضية قبل العمل** على المشروع
- **استخدم pyenv** لإدارة إصدارات Python المختلفة على نفس النظام