# 🧩 n8n Commands and UI Operations

قائمة شاملة لأوامر **n8n** من سطر الأوامر (CLI) ومن الواجهة الرسومية (Editor UI)

---

## 🧠 أوامر CLI (سطر الأوامر)

| الأمر | الوصف |
|--------|--------|
| `npm install n8n -g` | تثبيت n8n عالميًا على الجهاز. |
| `n8n` | تشغيل n8n في الوضع التفاعلي. |
| `n8n start` | تشغيل الخادم في الخلفية. |
| `n8n stop` | إيقاف الخادم. |
| `n8n restart` | إعادة تشغيل الخدمة. |
| `n8n status` | عرض حالة التشغيل الحالية. |
| `n8n update` | تحديث n8n إلى أحدث إصدار. |
| `n8n import:workflow --input=workflow.json` | استيراد Workflow من ملف JSON. |
| `n8n export:workflow --id=1 --output=workflow.json` | تصدير Workflow إلى ملف JSON. |
| `n8n import:credentials --input=creds.json` | استيراد بيانات الاتصال (Credentials). |
| `n8n export:credentials --id=1 --output=creds.json` | تصدير بيانات الاتصال. |
| `n8n help` | عرض قائمة المساعدة. |

---

## ⚙️ إعداد البيئة (Environment Variables)

| الأمر | الوصف |
|--------|--------|
| `export N8N_PORT=5678` | تحديد المنفذ المستخدم. |
| `export N8N_BASIC_AUTH_ACTIVE=true` | تفعيل المصادقة. |
| `export N8N_BASIC_AUTH_USER=admin` | تعيين اسم المستخدم. |
| `export N8N_BASIC_AUTH_PASSWORD=12345` | تعيين كلمة المرور. |
| `export N8N_ENCRYPTION_KEY=mySecretKey` | مفتاح التشفير للبيانات. |
| `export N8N_LOG_LEVEL=debug` | تفعيل وضع التصحيح. |

> على Windows استخدم `set` بدل `export`

---

## 🧰 إدارة الخدمة باستخدام PM2

| الأمر | الوصف |
|--------|--------|
| `pm2 start n8n` | تشغيل n8n كخدمة. |
| `pm2 stop n8n` | إيقاف الخدمة. |
| `pm2 restart n8n` | إعادة تشغيل الخدمة. |
| `pm2 logs n8n` | عرض السجلات. |
| `pm2 startup` | تشغيل تلقائي عند الإقلاع. |
| `pm2 save` | حفظ الإعدادات الحالية. |

---

## 💾 إعداد قاعدة البيانات

| الأمر | الوصف |
|--------|--------|
| `export DB_TYPE=postgresdb` | تحديد نوع قاعدة البيانات. |
| `export DB_POSTGRESDB_HOST=localhost` | المضيف. |
| `export DB_POSTGRESDB_USER=n8n_user` | اسم المستخدم. |
| `export DB_POSTGRESDB_PASSWORD=pass123` | كلمة المرور. |
| `export DB_POSTGRESDB_DATABASE=n8n_db` | اسم قاعدة البيانات. |

---

## 🔐 أوامر الأمان

| الأمر | الوصف |
|--------|--------|
| `export N8N_JWT_AUTH_ACTIVE=true` | تفعيل JWT. |
| `export N8N_JWT_AUTH_SECRET=mySecretToken` | مفتاح JWT السري. |
| `export N8N_BASIC_AUTH_ACTIVE=true` | تفعيل تسجيل الدخول الأساسي. |

---

## 🌐 تشغيل n8n عبر Docker

| الأمر | الوصف |
|--------|--------|
| `docker run -it --rm -p 5678:5678 n8nio/n8n` | تشغيل n8n داخل Docker. |
| `docker-compose up -d` | تشغيل الخدمة من ملف docker-compose. |
| `docker-compose down` | إيقاف الخدمة. |
| `docker logs n8n` | عرض السجلات. |

---

## 🧩 أوامر داخل واجهة n8n (Editor UI)

### 📁 إدارة الـ Workflows
| العملية | الوصف |
|----------|--------|
| ➕ **New Workflow** | إنشاء جديد. |
| 💾 **Save** | حفظ التعديلات. |
| ▶️ **Execute Workflow** | تشغيل يدوي. |
| 🧠 **Execute Node** | اختبار Node واحدة. |
| 🧭 **Activate Workflow** | تفعيل العمل التلقائي. |
| 🛑 **Deactivate Workflow** | تعطيل العمل التلقائي. |
| 🧱 **Duplicate Workflow** | نسخ Workflow. |
| ⬇️ **Export** | تصدير إلى JSON. |
| ⬆️ **Import** | استيراد من JSON. |
| 🗑️ **Delete** | حذف الـ Workflow. |

---

### ⚙️ إدارة العقد (Nodes)
| العملية | الوصف |
|----------|--------|
| ➕ **Add Node** | إضافة Node جديدة. |
| ✏️ **Rename Node** | إعادة التسمية. |
| 🔗 **Connect Nodes** | ربط عقدتين. |
| 🧹 **Remove Connection** | فك الربط. |
| 📥 **View Input** | عرض الإدخال. |
| 📤 **View Output** | عرض الإخراج. |
| ⚙️ **Edit Parameters** | تعديل الإعدادات. |
| 📋 **Duplicate Node** | نسخ العقدة. |
| ❌ **Delete Node** | حذف العقدة. |
| 🧩 **Pin Data** | تثبيت البيانات الناتجة. |

---

### ⏰ **Triggers & Scheduling**
| العملية | الوصف |
|----------|--------|
| ⏱️ **Cron Node** | تشغيل مجدول. |
| 🌐 **Webhook Node** | استقبال طلبات HTTP. |
| 💬 **Telegram / Gmail / API Trigger** | تشغيل تلقائي عند حدث خارجي. |
| 🧭 **Manual Trigger** | تشغيل يدوي للتجربة. |

---

### 🧠 **تحليل وتتبع التنفيذ**
| العملية | الوصف |
|----------|--------|
| 🧾 **Execution List** | عرض قائمة التشغيل السابقة. |
| 🔍 **View Details** | عرض تفاصيل التشغيل. |
| 📈 **Display Data** | عرض البيانات الناتجة. |
| 🔁 **Re-Execute** | إعادة التشغيل بنفس البيانات. |
| 📉 **Error View** | عرض الأخطاء وتتبّعها. |

---

### 🔒 **Credentials**
| العملية | الوصف |
|----------|--------|
| ➕ **Add Credentials** | إضافة بيانات اتصال جديدة. |
| ✏️ **Edit Credentials** | تعديل بيانات الاتصال. |
| 🧪 **Test Connection** | اختبار الاتصال. |
| 🗑️ **Delete Credentials** | حذف بيانات الاتصال. |

---

### ⚙️ **Settings**
| العملية | الوصف |
|----------|--------|
| ⚙️ **General** | إعدادات عامة (لغة، ثيم، إلخ). |
| 🧾 **User Management** | إدارة المستخدمين والصلاحيات. |
| 🔐 **Security** | إعدادات الأمان والمصادقة. |
| 💾 **Backup & Restore** | النسخ الاحتياطي والاسترجاع. |
| 🧭 **Logs** | عرض السجلات. |

---

> **📘 ملاحظة:**  
> يمكن دمج أوامر CLI مع بيئة Docker أو PM2 لتشغيل n8n بشكل دائم على الخوادم.

