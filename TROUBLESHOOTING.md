# 🔧 Troubleshooting Guide — Google Ads MCP Server

إذا تعطّل السيرفر، أرسل هذا الـ prompt لـ Claude:

---

## Prompt للنسخ المباشر

```
سيرفر Google Ads MCP تعطّل، حلّل المشكلة وأصلحها.

**بيانات الاتصال:**
ssh root@94.176.182.121 -p 41194

**مواقع المشروع:**
- السيرفر: /opt/google-ads-mcp/
- الخدمة: google-ads-mcp.service
- الـ URL: https://mcpgooads.batteryswap.cc/mcp
- nginx config: /etc/nginx/sites-enabled/mcpGooAds
- Claude Desktop config: C:\Users\Abdulrhman Alhur\AppData\Roaming\Claude\claude_desktop_config.json
- الكود المحلي: C:\Users\Abdulrhman Alhur\google-ads-mcp\

**المشروع:**
FastMCP server يشتغل مباشرة (بدون supergateway) عبر:
uv run main.py --groups all --transport streamable-http --host 0.0.0.0 --port 3100

**خطوات التشخيص:**
1. systemctl status google-ads-mcp
2. journalctl -u google-ads-mcp -n 50 --no-pager
3. curl -si -X POST https://mcpgooads.batteryswap.cc/mcp/ -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' -d '{"jsonrpc":"2.0","method":"initialize","id":1,"params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1"}}}'
4. tail -20 /var/log/nginx/error.log

حلّل وأصلح.
```

---

## معلومات البنية التحتية

| المكوّن | التفاصيل |
|---------|----------|
| السيرفر | VPS — Ubuntu 22.04 |
| IP | 94.176.182.121 |
| SSH Port | 41194 |
| الكود | `/opt/google-ads-mcp/` |
| الخدمة | `google-ads-mcp.service` (systemd) |
| الـ Runtime | FastMCP 2.9.0 + Python 3.12 + uv |
| Transport | `streamable-http` على port 3100 |
| Reverse Proxy | nginx → `/etc/nginx/sites-enabled/mcpGooAds` |
| الـ URL | `https://mcpgooads.batteryswap.cc/mcp` |
| Claude Desktop | `mcp-remote` → `https://mcpgooads.batteryswap.cc/mcp` |

---

## أوامر سريعة على السيرفر

```bash
# حالة الخدمة
systemctl status google-ads-mcp

# سجل مباشر
journalctl -u google-ads-mcp -f

# إعادة تشغيل
systemctl restart google-ads-mcp

# اختبار الاتصال
curl -si -X POST https://mcpgooads.batteryswap.cc/mcp/ \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","method":"initialize","id":1,"params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1"}}}'

# nginx logs
tail -20 /var/log/nginx/error.log
```

---

## systemd Service Config

```ini
[Unit]
Description=Google Ads MCP Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/google-ads-mcp
EnvironmentFile=/opt/google-ads-mcp/.env
ExecStart=/root/.local/bin/uv run --directory /opt/google-ads-mcp main.py --groups all --transport streamable-http --host 0.0.0.0 --port 3100
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

> الملف في: `/etc/systemd/system/google-ads-mcp.service`

---

## nginx Config

```nginx
server {
    listen 80;
    server_name mcpgooads.batteryswap.cc;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name mcpgooads.batteryswap.cc;

    ssl_certificate /etc/letsencrypt/live/mcpgooads.batteryswap.cc/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mcpgooads.batteryswap.cc/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location / {
        proxy_pass http://127.0.0.1:3100;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection keep-alive;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
        proxy_buffering off;
        proxy_cache off;
    }
}
```

---

## Claude Desktop Config

الملف: `C:\Users\Abdulrhman Alhur\AppData\Roaming\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "google-ads": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://mcpgooads.batteryswap.cc/mcp"
      ]
    }
  }
}
```

---

## مشاكل شائعة وحلولها

| المشكلة | السبب | الحل |
|---------|-------|------|
| `Could not attach to MCP server` | الخدمة متوقفة أو تكرش | `systemctl restart google-ads-mcp` |
| `502 Bad Gateway` | nginx لا يصل للـ backend | تحقق من الخدمة، ثم `systemctl reload nginx` |
| `Already connected to a transport` | استخدام supergateway مع SSE | لا تستخدم supergateway — شغّل FastMCP مباشرة |
| `No connection established for request ID: 2` | supergateway streamableHttp بدون session | استخدم FastMCP native `--transport streamable-http` |
| عدة python processes تأكل الـ RAM | supergateway streamableHttp يولّد process لكل request | شغّل FastMCP مباشرة بدون supergateway |
| `upstream prematurely closed connection` | nginx لا يدعم SSE بشكل صحيح | أضف `proxy_set_header Connection keep-alive` |

---

## تحديث الكود على السيرفر

```bash
ssh root@94.176.182.121 -p 41194
cd /opt/google-ads-mcp
git pull
systemctl restart google-ads-mcp
```
