#!/usr/bin/env python3
"""Create PENDING_UPDATE.md when auto-deploy fails."""
import os
import sys

current = sys.argv[1] if len(sys.argv) > 1 else ""
current_msg = sys.argv[2] if len(sys.argv) > 2 else ""
new_commit = sys.argv[3] if len(sys.argv) > 3 else ""
new_msg = sys.argv[4] if len(sys.argv) > 4 else ""
deploy_time = sys.argv[5] if len(sys.argv) > 5 else ""
http_code = sys.argv[6] if len(sys.argv) > 6 else ""

error_log = (
    open("/tmp/mcp_test.log").read()[-2000:]
    if os.path.exists("/tmp/mcp_test.log")
    else "no logs"
)

lines = [
    "# تحديث معلق",
    "",
    "> التحديث التلقائي فشل — السيرفر يعمل على النسخة السابقة بشكل طبيعي.",
    "",
    "## معلومات المحاولة",
    "",
    "| | |",
    "|---|---|",
    f"| **التاريخ** | {deploy_time} |",
    f"| **Commit المحاول** | `{new_commit}` |",
    f"| **رسالة الـ Commit** | {new_msg} |",
    f"| **HTTP Response** | {http_code} |",
    "",
    "## النسخة الحالية (الشغّالة)",
    "",
    "| | |",
    "|---|---|",
    f"| **Commit** | `{current}` |",
    f"| **رسالة الـ Commit** | {current_msg} |",
    "",
    "## سجل الخطأ",
    "",
    "```",
    error_log,
    "```",
    "",
    "## تطبيق التحديث يدوياً",
    "",
    "```bash",
    "ssh root@94.176.182.121 -p 41194",
    "cd /opt/google-ads-mcp",
    "git pull origin main",
    "uv sync",
    "systemctl restart google-ads-mcp",
    "```",
]

open("/opt/google-ads-mcp/PENDING_UPDATE.md", "w").write("\n".join(lines))
print("PENDING_UPDATE.md created")
