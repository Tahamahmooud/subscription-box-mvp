# صندوقي — منصة الاشتراكات العربية 📦

منصة اشتراكات شهرية عربية: قهوة، عناية، كتب، حلويات وأكثر — تصلك لباب بيتك.

## ✨ الميزات

- 🎨 واجهة عربية RTL متجاوبة (Bootstrap 5)
- 👤 تسجيل وتسجيل دخول للمستخدمين
- 📦 تصفح صناديق الاشتراك والاشتراك فيها
- 🔄 إدارة الاشتراكات (إلغاء / عرض)
- 🛠️ لوحة تحكم إدارية كاملة
- 📊 إحصائيات (مستخدمين، اشتراكات، إيرادات)
- 🔌 REST API للصناديق

## 🚀 التشغيل المحلي

```bash
# تثبيت المكتبات
pip install flask flask-sqlalchemy werkzeug

# تشغيل التطبيق
python app.py
```

ثم افتح: http://localhost:5000

## 🔑 بيانات الدخول التجريبية

| الدور | البريد الإلكتروني | كلمة المرور |
|-------|-------------------|-------------|
| مدير | `admin@box.com` | `admin123` |

> ⚠️ **غيّر كلمة مرور المدير قبل النشر للإنتاج!**

## 🗺️ المسارات

| المسار | الوصف |
|--------|-------|
| `/` | الصفحة الرئيسية |
| `/login` | تسجيل الدخول |
| `/register` | إنشاء حساب |
| `/box/<id>` | تفاصيل الصندوق |
| `/my-subscriptions` | اشتراكاتي |
| `/admin` | لوحة التحكم (للمدير) |
| `/api/boxes` | API الصناديق |

## 🛠️ التقنيات

- **Backend:** Flask + SQLAlchemy
- **Frontend:** Bootstrap 5 + Bootstrap Icons
- **Database:** SQLite

## 📁 هيكل المشروع

```
subscription-box-mvp/
├── app.py                 # التطبيق الرئيسي
├── requirements.txt       # المكتبات
├── templates/             # قوالب HTML
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── box_detail.html
│   ├── my_subscriptions.html
│   └── admin/
│       ├── dashboard.html
│       ├── boxes.html
│       ├── add_box.html
│       ├── edit_box.html
│       └── subscriptions.html
└── instance/              # قاعدة البيانات (غير مرفوعة)
```

## 📝 الترخيص

MIT
