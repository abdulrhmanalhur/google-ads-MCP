# TROUBLESHOOTING — Google Ads MCP Server

> **Server:** `94.176.182.121` | **Port:** `3100` | **Path:** `/opt/google-ads-mcp/`
> **Service:** `google-ads-mcp.service` | **Auto-update log:** `/var/log/google-ads-mcp-update.log`

---

## Quick Commands

```bash
# Check service status
systemctl status google-ads-mcp

# View live logs
journalctl -u google-ads-mcp -f

# Restart service
systemctl restart google-ads-mcp

# Check auto-update timer
systemctl list-timers google-ads-mcp-updater.timer

# Run update manually
/opt/google-ads-mcp/scripts/auto-update.sh

# View update log
tail -50 /var/log/google-ads-mcp-update.log
```

---

## Common Issues

### 1. Service won't start

**Symptoms:** `systemctl status google-ads-mcp` shows `failed`

**Steps:**
```bash
journalctl -u google-ads-mcp -n 50
cd /opt/google-ads-mcp
cat .env                     # Verify credentials exist
uv run main.py --groups all  # Test manual start
```

**Common causes:**
- Missing or invalid  credentials
- Port 3100 already in use: `lsof -i :3100`
- Python dependency missing: `uv sync`

---

### 2. Google Ads API authentication error

**Symptoms:** `AuthenticationError` or `401` in logs

**Steps:**
1. Check  values are correct:
   ```
   GOOGLE_ADS_DEVELOPER_TOKEN
   GOOGLE_ADS_REFRESH_TOKEN
   GOOGLE_ADS_CLIENT_ID
   GOOGLE_ADS_CLIENT_SECRET
   ```
2. Refresh token may have expired — regenerate via Google OAuth2
3. Check developer token is approved in Google Ads account

---

### 3. Auto-update failed — git pull conflict

**Symptoms:** Update log shows `git pull failed`

**Steps:**
```bash
cd /opt/google-ads-mcp
git status                    # See conflicting files
git stash                     # Stash local changes
git pull origin main          # Pull again
git stash pop                 # Re-apply local changes
systemctl restart google-ads-mcp
```

---

### 4. Auto-update failed — uv sync error

**Symptoms:** Update log shows `uv sync failed`

**Steps:**
```bash
cd /opt/google-ads-mcp
uv sync                       # See full error
uv cache clean                # Clear cache if needed
uv sync                       # Retry
```

---

### 5. Service started but MCP tools not responding

**Symptoms:** Service is active but tools return errors

**Steps:**
```bash
# Test HTTP endpoint
curl http://localhost:3100/

# Check all tools loaded
journalctl -u google-ads-mcp | grep "Registered tools"

# Restart
systemctl restart google-ads-mcp
```

---

### 6. Rollback to previous version

```bash
cd /opt/google-ads-mcp
git log --oneline -10          # Find target commit
git reset --hard <commit-hash>
uv sync
systemctl restart google-ads-mcp
```

---

### 7. Manual update (skip waiting for timer)

```bash
/opt/google-ads-mcp/scripts/auto-update.sh
# OR
cd /opt/google-ads-mcp
git pull origin main
uv sync
systemctl restart google-ads-mcp
```

---

## Auto-Update Schedule

| Property | Value |
|---|---|
| Frequency | Every 2 weeks |
| Schedule | 1st and 15th of each month at 03:00 UTC |
| Timer | `google-ads-mcp-updater.timer` |
| Log | `/var/log/google-ads-mcp-update.log` |
| Script | `/opt/google-ads-mcp/scripts/auto-update.sh` |

---

## Auto-Update Errors (Generated Automatically)

| Date | Type | Details |
|---|---|---|
