# 🚀 نشر Google Ads MCP Server على VPS

دليل كامل لرفع سيرفر Google Ads MCP وربطه بـ Claude Desktop من أي مكان.

---

## المتطلبات

| المتطلب | التفاصيل |
|---------|----------|
| VPS | Ubuntu 22.04 أو 24.04 |
| RAM | 1GB كحد أدنى |
| Domain | subdomain يشير لـ IP السيرفر |
| Google Ads API | Developer Token + OAuth2 credentials |
| Node.js (محلي) | لتشغيل `mcp-remote` على جهازك |

---

## الخطوة 1 — إعداد DNS

في لوحة تحكم الـ Domain (Cloudflare أو غيره):

1. أضف **A Record** جديد:
   - **Name**: `mcp` (أو أي اسم تريده)
   - **Value**: IP السيرفر
   - **Proxy**: ❌ **DNS Only** (مهم — لا تفعّل Proxy)

2. انتظر 2-5 دقائق حتى ينتشر الـ DNS

---

## الخطوة 2 — تشغيل سكريبت النشر

اتصل بالسيرفر وشغّل أمر واحد فقط:

```bash
ssh root@YOUR_SERVER_IP

# حمّل وشغّل السكريبت
curl -O https://raw.githubusercontent.com/abdulrhmanalhur/google-ads-MCP/main/deploy.sh
chmod +x deploy.sh
bash deploy.sh
```

سيطلب منك السكريبت:
- بيانات Google Ads API (انظر كيفية الحصول عليها أدناه)
- الـ Domain (مثال: `mcp.yourdomain.com`)
- إيميل لشهادة SSL

---

## الخطوة 3 — إعداد Claude Desktop

بعد انتهاء السكريبت، افتح ملف الإعداد:

**Windows:** `C:\Users\USERNAME\AppData\Roaming\Claude\claude_desktop_config.json`
**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

أضف هذا:

```json
{
  "mcpServers": {
    "google-ads": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://mcp.yourdomain.com/mcp"
      ]
    }
  }
}
```

ثم **أعد تشغيل Claude Desktop**.

---

## كيفية الحصول على Google Ads API Credentials

### 1. Developer Token
1. سجّل دخول على [Google Ads](https://ads.google.com)
2. الإعدادات ← مركز واجهة برمجة التطبيقات
3. انسخ الـ **Developer Token**

### 2. OAuth2 Credentials (Client ID + Secret + Refresh Token)

**أ. إنشاء OAuth2 Client:**
1. افتح [Google Cloud Console](https://console.cloud.google.com)
2. APIs & Services ← Credentials ← Create Credentials ← OAuth 2.0 Client ID
3. Application type: **Desktop app**
4. انسخ **Client ID** و **Client Secret**

**ب. الحصول على Refresh Token:**
```bash
pip install google-auth-oauthlib

python3 - <<'EOF'
from google_auth_oauthlib.flow import InstalledAppFlow

flow = InstalledAppFlow.from_client_secrets_file(
    'client_secrets.json',
    scopes=['https://www.googleapis.com/auth/adwords']
)
credentials = flow.run_local_server(port=0)
print("Refresh Token:", credentials.refresh_token)
EOF
```

### 3. Login Customer ID
- هو رقم حساب Google Ads بدون شرطات
- مثال: `123-456-7890` → `1234567890`

---

## إعداد يدوي (بدون السكريبت)

<details>
<summary>اضغط للتوسيع</summary>

### تثبيت Python 3.12
```bash
add-apt-repository -y ppa:deadsnakes/ppa
apt-get update && apt-get install -y python3.12 python3.12-venv
```

### تثبيت uv
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
```

### تثبيت Node.js وsupergateway
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs
npm install -g supergateway
```

### نسخ الكود
```bash
git clone https://github.com/abdulrhmanalhur/google-ads-MCP.git /opt/google-ads-mcp
cd /opt/google-ads-mcp
uv sync
```

### ملف الإعدادات
```bash
cat > /opt/google-ads-mcp/.env << 'EOF'
GOOGLE_ADS_DEVELOPER_TOKEN=your_token
GOOGLE_ADS_CLIENT_ID=your_client_id
GOOGLE_ADS_CLIENT_SECRET=your_secret
GOOGLE_ADS_REFRESH_TOKEN=your_refresh_token
GOOGLE_ADS_LOGIN_CUSTOMER_ID=your_customer_id
EOF
chmod 600 /opt/google-ads-mcp/.env
```

### خدمة systemd
```bash
cat > /etc/systemd/system/google-ads-mcp.service << 'EOF'
[Unit]
Description=Google Ads MCP Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/google-ads-mcp
EnvironmentFile=/opt/google-ads-mcp/.env
ExecStart=/usr/bin/supergateway --port 3100 --outputTransport streamableHttp --stdio '/root/.local/bin/uv run --directory /opt/google-ads-mcp main.py --groups all'
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable google-ads-mcp
systemctl start google-ads-mcp
```

### إعداد nginx + SSL
```bash
# nginx config
cat > /etc/nginx/sites-available/google-ads-mcp << 'EOF'
server {
    listen 80;
    server_name mcp.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:3100;
        proxy_http_version 1.1;
        proxy_set_header Connection '';
        proxy_set_header Host $host;
        proxy_read_timeout 86400s;
        proxy_buffering off;
        proxy_cache off;
    }
}
EOF

ln -sf /etc/nginx/sites-available/google-ads-mcp /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# SSL
apt-get install -y certbot python3-certbot-nginx
certbot --nginx -d mcp.yourdomain.com --email your@email.com --agree-tos --non-interactive --redirect
```

</details>

---

## أوامر مفيدة

```bash
# حالة الخدمة
systemctl status google-ads-mcp

# سجل مباشر
journalctl -u google-ads-mcp -f

# إعادة تشغيل
systemctl restart google-ads-mcp

# اختبار الاتصال
curl -s https://mcp.yourdomain.com/mcp \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","id":1,"params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1"}}}'
```

---

## المجموعات المتاحة

السيرفر يدعم `--groups all` أو يمكن تحديد مجموعات معينة:

| المجموعة | المحتوى |
|----------|---------|
| `core` | الحملات، الميزانية، الكلمات المفتاحية، الإعلانات |
| `assets` | إدارة الأصول والصور |
| `targeting` | الاستهداف والجماهير |
| `bidding` | استراتيجيات العروض |
| `reporting` | التقارير والبيانات |
| `conversion` | تتبع التحويلات |
| `all` | جميع الأدوات (309 أداة) |

---

## استكشاف الأخطاء

| المشكلة | الحل |
|---------|------|
| `502 Bad Gateway` | `systemctl restart google-ads-mcp` |
| `SSL Error` | تحقق أن DNS يشير للسيرفر وليس Cloudflare Proxy |
| `Authentication failed` | تحقق من صحة الـ credentials في `.env` |
| `Connection timeout` | تحقق من فتح المنفذ `443` في Firewall |

---

## الدعم

- **GitHub**: [abdulrhmanalhur/google-ads-MCP](https://github.com/abdulrhmanalhur/google-ads-MCP)
- **Google Ads API Docs**: [developers.google.com/google-ads/api](https://developers.google.com/google-ads/api/docs/start)
