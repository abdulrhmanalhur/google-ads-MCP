#!/bin/bash
# ============================================================
# Google Ads MCP - Auto Update Script
# يشتغل كل أسبوعين عبر systemd timer
# ============================================================

SERVICE_NAME="google-ads-mcp"
PROJECT_DIR="/opt/google-ads-mcp"
LOG_FILE="/var/log/google-ads-mcp-update.log"
TROUBLESHOOTING_FILE="$PROJECT_DIR/TROUBLESHOOTING.md"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

update_troubleshooting() {
    local error_type="$1"
    local error_msg="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    # أضف القسم إذا ما كان موجود
    if ! grep -q "## Auto-Update Errors" "$TROUBLESHOOTING_FILE" 2>/dev/null; then
        cat >> "$TROUBLESHOOTING_FILE" << EOF

---

## Auto-Update Errors (Generated Automatically)

| Date | Type | Details |
|---|---|---|
EOF
    fi

    # أضف سطر الخطأ الجديد
    sed -i "/^| Date | Type | Details/a | $timestamp | $error_type | $error_msg |" "$TROUBLESHOOTING_FILE"
}

cd "$PROJECT_DIR" || { log "ERROR: Cannot access $PROJECT_DIR"; exit 1; }

log "====== Starting auto-update check ====="
log "Current commit: $(git rev-parse --short HEAD)"

# 1. جلب آخر التغييرات من GitHub
log "Fetching from origin..."
if ! git fetch origin main 2>&1 | tee -a "$LOG_FILE"; then
    log "ERROR: git fetch failed"
    update_troubleshooting "git fetch failed" "Cannot reach GitHub. Check network or SSH keys."
    exit 1
fi

# 2. تحقق إذا فيه تحديثات
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" = "$REMOTE" ]; then
    log "Already up to date. No update needed."
    log "====== Update check complete ======"
    exit 0
fi

COMMITS_BEHIND=$(git rev-list HEAD..origin/main --count)
log "Found $COMMITS_BEHIND new commit(s). Starting update..."
git log HEAD..origin/main --oneline | tee -a "$LOG_FILE"

# 3. عمل backup للـ .env
cp "$PROJECT_DIR/.env" /tmp/google-ads-mcp-env.bak 2>/dev/null

# 4. تطبيق التحديث
log "Pulling changes..."
if ! git pull origin main 2>&1 | tee -a "$LOG_FILE"; then
    log "ERROR: git pull failed"
    update_troubleshooting "git pull failed" "Merge conflict or permission issue. Run: cd /opt/google-ads-mcp && git status"
    exit 1
fi

# 5. استعادة .env في حال اتحذف
if [ ! -f "$PROJECT_DIR/.env" ] && [ -f /tmp/google-ads-mcp-env.bak ]; then
    cp /tmp/google-ads-mcp-env.bak "$PROJECT_DIR/.env"
    log "Restored .env from backup"
fi

# 6. تحديث الـ dependencies
log "Syncing dependencies with uv..."
if ! /root/.local/bin/uv sync --directory "$PROJECT_DIR" 2>&1 | tee -a "$LOG_FILE"; then
    log "ERROR: uv sync failed"
    update_troubleshooting "uv sync failed" "Dependency error after update. Run: cd /opt/google-ads-mcp && uv sync"
    exit 1
fi

# 7. إعادة تشغيل الـ service
log "Restarting $SERVICE_NAME service..."
if ! systemctl restart "$SERVICE_NAME" 2>&1 | tee -a "$LOG_FILE"; then
    log "ERROR: Service restart failed"
    update_troubleshooting "Service restart failed" "Run: systemctl status google-ads-mcp && journalctl -u google-ads-mcp -n 50"
    exit 1
fi

# 8. تحقق إن الـ service شغال
sleep 5
if systemctl is-active --quiet "$SERVICE_NAME"; then
    log "SUCCESS: Service is running. Updated to: $(git rev-parse --short HEAD)"
else
    log "ERROR: Service failed to start after update"
    update_troubleshooting "Service failed after update" "Check logs: journalctl -u google-ads-mcp -n 100"
    # Rollback
    log "Attempting rollback to previous commit..."
    git reset --hard "$LOCAL"
    systemctl restart "$SERVICE_NAME"
    log "Rolled back to: $(git rev-parse --short HEAD)"
fi

log "====== Auto-update complete ======"
