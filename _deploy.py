"""Deploy latest code to production server (120.76.40.7)."""
import os, sys, time, paramiko

HOST, PORT, USER, PASSWORD = "120.76.40.7", 22, "root", "sBHXvrQF44fuSpz"
REMOTE = "/root/E-commerce-Operations-Platform"
LOCAL = os.path.dirname(os.path.abspath(__file__))

FILES = [
    "backend/app/api/v1/pages.py",
    "backend/app/static/style.css",
    "backend/app/templates/base.html",
    "backend/app/templates/pages/login.html",
    "backend/app/templates/pages/register.html",
    "backend/app/templates/pages/dashboard.html",
    "backend/app/pro/analytics/__init__.py",
    "backend/app/pro/analytics/metrics.py",
    "backend/app/pro/analytics/inventory.py",
    "backend/app/pro/analytics/sales.py",
    "backend/app/pro/analytics/trends.py",
]

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, PORT, USER, PASSWORD, look_for_keys=False, allow_agent=False)


def run(cmd):
    s, o, e = ssh.exec_command(cmd)
    return o.read().decode().strip(), e.read().decode().strip()


print("1. Uploading files...")
sftp = ssh.open_sftp()
for rel in FILES:
    local = os.path.join(LOCAL, rel).replace("\\", "/")
    remote = f"{REMOTE}/{rel}"
    run(f"mkdir -p {'/'.join(remote.split('/')[:-1])}")
    sftp.put(local, remote)
    print(f"   {rel}")
sftp.close()

print("\n2. Rebuilding API...")
out, _ = run("cd /root/E-commerce-Operations-Platform && docker compose -f docker/docker-compose.yml build api 2>&1")
print(out[-300:] if len(out) > 300 else out)

print("\n3. Restarting containers...")
out, _ = run("cd /root/E-commerce-Operations-Platform && docker compose -f docker/docker-compose.yml up -d api 2>&1")
print(out[:200] if out else "OK")

print("\n4. Waiting for healthy...")
for i in range(15):
    out, _ = run("curl -s -o /dev/null -w '%{http_code}' http://localhost:17452/cello/health --max-time 5")
    code = out[-3:] if len(out) >= 3 else "N/A"
    if code == "200":
        print(f"   API ready (attempt {i+1})")
        break
    time.sleep(3)
else:
    print("   WARNING: API not healthy after 15 attempts")

print("\n5. Verifying login...")
out, _ = run(
    "curl -s -X POST 'http://localhost:17452/cello/api/v1/auth/login' "
    "-H 'Content-Type: application/json' "
    "-d '{\"email\":\"demo@example.com\",\"password\":\"Demo1234!\"}' "
    "--max-time 10 | python3 -c 'import sys,json; d=json.load(sys.stdin); print(\"OK\" if \"access_token\" in d else d)'"
)
print(f"   {out[:100]}")

ssh.close()
print("\nDone! https://hscuuhgctunneld.top/cello/")
