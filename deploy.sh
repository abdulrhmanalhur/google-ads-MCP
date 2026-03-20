#!/bin/bash
# ============================================================
#  Google Ads MCP Server - Auto Deployment Script
#  يدعم: Ubuntu 22.04 / 24.04
# ============================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_step() { echo -e "\n${BLUE}▶ $1${NC}"; }
print_ok()   { echo -e "${GREEN}✓ $1${NC}"; }
print_warn() { echo -e "${YELLOW}⚠ $1${NC}"; }
print_err()  { echo -e "${RED}✗ $1${NC}"; exit 1; }

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════╗"
echo "║     Google Ads MCP Server - Setup        ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"

# ── متطلبات ──────────────────────────────────────────────
[[ $EUID -ne 0 ]] && print_err "شغّل السكريبت كـ root: sudo bash deploy.sh"

# ── جمع المعلومات ─────────────────────────────────────────
print_step "أدخل بيانات Google Ads API"
read -p "  GOOGLE_ADS_DEVELOPER_TOKEN  : " DEV_TOKEN
read -p "  GOOGLE_ADS_CLIENT_ID        : " CLIENT_ID
read -p "  GOOGLE_ADS_CLIENT_SECRET    : " CLIENT_SECRET
read -p "  GOOGLE_ADS_REFRESH_TOKEN    : " REFRESH_TOKEN
read -p "  GOOGLE_ADS_LOGIN_CUSTOMER_ID: " CUSTOMER_ID

echo ""
read -p "  الـ Domain للـ MCP (مثال: mcp.yourdomain.com): " MCP_DOMAIN
read -p "  إيميل لشهادة SSL               : " SSL_EMAIL
read -p "  المنفذ للـ MCP server [3100]   : " MCP_PORT
MCP_PORT=${MCP_PORT:-3100}

INSTALL_DIR="/opt/google-ads-mcp"

# ── 1. تحديث النظام ──────────────────────────────────────
print_step "تحديث النظام وتثبيت المتطلبات"
apt-get update -qq
apt-get install -y curl git nginx certbot python3-certbot-nginx 2>&1 | grep -E "Setting up|already"
print_ok "تم تثبيت المتطلبات الأساسية"

# ── 2. Python 3.12 ───────────────────────────────────────
print_step "تثبيت Python 3.12"
if ! python3.12 --version &>/dev/null; then
    add-apt-repository -y ppa:deadsnakes/ppa -qq
    apt-get update -qq
    apt-get install -y python3.12 python3.12-venv python3.12-dev 2>&1 | grep -E "Setting up|already"
fi
print_ok "Python $(python3.12 --version)"

# ── 3. uv ────────────────────────────────────────────────
print_step "تثبيت uv (مدير الحزم)"
if ! /root/.local/bin/uv --version &>/dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> /root/.bashrc
fi
export PATH="$HOME/.local/bin:$PATH"
print_ok "uv $(/root/.local/bin/uv --version)"

# ── 4. Node.js + supergateway ────────────────────────────
print_step "تثبيت Node.js وsupergateway"
if ! node --version &>/dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - 2>&1 | tail -3
    apt-get install -y nodejs 2>&1 | grep -E "Setting up|already"
fi
npm install -g supergateway 2>&1 | tail -3
print_ok "Node $(node --version) | supergateway $(supergateway --version)"

# ── 5. نسخ الكود ─────────────────────────────────────────
print_step "تحميل Google Ads MCP"
if [ -d "$INSTALL_DIR" ]; then
    print_warn "المجلد موجود - تحديث الكود..."
    cd "$INSTALL_DIR" && git pull
else
    git clone https://github.com/abdulrhmanalhur/google-ads-MCP.git "$INSTALL_DIR"
fi
cd "$INSTALL_DIR"
/root/.local/bin/uv sync 2>&1 | tail -5
print_ok "تم تحميل الكود وتثبيت التبعيات"

# ── 6. ملف .env ───────────────────────────────────────────
print_step "إنشاء ملف الإعدادات"
cat > "$INSTALL_DIR/.env" << ENV
GOOGLE_ADS_DEVELOPER_TOKEN=$DEV_TOKEN
GOOGLE_ADS_CLIENT_ID=$CLIENT_ID
GOOGLE_ADS_CLIENT_SECRET=$CLIENT_SECRET
GOOGLE_ADS_REFRESH_TOKEN=$REFRESH_TOKEN
GOOGLE_ADS_LOGIN_CUSTOMER_ID=$CUSTOMER_ID
ENV
chmod 600 "$INSTALL_DIR/.env"
print_ok "تم إنشاء .env بصلاحيات آمنة (600)"

# ── 7. Systemd Service ────────────────────────────────────
print_step "إنشاء خدمة systemd"
cat > /etc/systemd/system/google-ads-mcp.service << SERVICE
[Unit]
Description=Google Ads MCP Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=/usr/bin/supergateway --port $MCP_PORT --outputTransport streamableHttp --stdio '/root/.local/bin/uv run --directory $INSTALL_DIR main.py --groups all'
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable google-ads-mcp
systemctl restart google-ads-mcp
sleep 3
systemctl is-active google-ads-mcp > /dev/null && print_ok "الخدمة تعمل" || print_err "فشل تشغيل الخدمة"

# ── 8. Nginx ──────────────────────────────────────────────
print_step "إعداد nginx"
cat > /etc/nginx/sites-available/google-ads-mcp << NGINX
server {
    listen 80;
    server_name $MCP_DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:$MCP_PORT;
        proxy_http_version 1.1;
        proxy_set_header Connection '';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
        proxy_buffering off;
        proxy_cache off;
    }
}
NGINX
ln -sf /etc/nginx/sites-available/google-ads-mcp /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
print_ok "nginx جاهز"

# ── 9. SSL ────────────────────────────────────────────────
print_step "الحصول على شهادة SSL"
certbot --nginx -d "$MCP_DOMAIN" \
    --non-interactive --agree-tos \
    --email "$SSL_EMAIL" --redirect
print_ok "SSL جاهز لـ https://$MCP_DOMAIN"

# ── 10. اختبار نهائي ──────────────────────────────────────
print_step "اختبار الاتصال"
sleep 2
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "https://$MCP_DOMAIN/mcp" -X POST \
    -H "Content-Type: application/json" \
    -d '{"jsonrpc":"2.0","method":"initialize","id":1,"params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1"}}}' 2>/dev/null || echo "000")

if [[ "$HTTP_CODE" == "200" ]]; then
    print_ok "الاتصال يعمل بشكل صحيح!"
else
    print_warn "كود الاستجابة: $HTTP_CODE - تحقق من journalctl -u google-ads-mcp"
fi

# ── ملخص ──────────────────────────────────────────────────
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════╗"
echo    "║           تم الإعداد بنجاح! ✓                    ║"
echo    "╚══════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}أضف هذا في claude_desktop_config.json:${NC}"
echo ""
echo '{'
echo '  "mcpServers": {'
echo '    "google-ads": {'
echo '      "command": "npx",'
echo '      "args": ['
echo '        "-y",'
echo '        "mcp-remote",'
echo "        \"https://$MCP_DOMAIN/mcp\""
echo '      ]'
echo '    }'
echo '  }'
echo '}'
echo ""
echo -e "${BLUE}أوامر مفيدة:${NC}"
echo "  systemctl status google-ads-mcp   # حالة الخدمة"
echo "  journalctl -u google-ads-mcp -f   # سجل مباشر"
echo "  systemctl restart google-ads-mcp  # إعادة تشغيل"
