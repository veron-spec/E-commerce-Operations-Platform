"""Deploy login fix to production server."""
import paramiko

HOST = "120.76.40.7"
PORT = 22
USER = "root"
PASSWORD = "sBHXvrQF44fuSpz"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, PORT, USER, PASSWORD, look_for_keys=False, allow_agent=False)


def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode().strip(), stderr.read().decode().strip()


print("=== 1. Copy updated files ===")
sftp = ssh.open_sftp()
files = [
    ("backend/app/infrastructure/rate_limiter.py", "/root/E-commerce-Operations-Platform/backend/app/infrastructure/rate_limiter.py"),
    ("backend/app/api/v1/__init__.py", "/root/E-commerce-Operations-Platform/backend/app/api/v1/__init__.py"),
    ("backend/app/api/v1/community_analytics.py", "/root/E-commerce-Operations-Platform/backend/app/api/v1/community_analytics.py"),
    ("backend/app/main.py", "/root/E-commerce-Operations-Platform/backend/app/main.py"),
    ("backend/app/templates/pages/login.html", "/root/E-commerce-Operations-Platform/backend/app/templates/pages/login.html"),
    ("docker/nginx.conf", "/root/E-commerce-Operations-Platform/docker/nginx.conf"),
]
for local, remote in files:
    sftp.put(local, remote)
    print(f"  OK {local}")
sftp.close()

print()
print("=== 2. Rebuild API container ===")
out, err = run("cd /root/E-commerce-Operations-Platform && docker compose -f docker/docker-compose.yml build api")
print(out[-500:] if len(out) > 500 else out)
if err: print("ERR:", err[:300])

print()
print("=== 3. Restart API + nginx ===")
out, err = run("cd /root/E-commerce-Operations-Platform && docker compose -f docker/docker-compose.yml up -d --no-deps api nginx")
print(out[:500] if out else "OK")
if err: print("ERR:", err[:300])

print()
print("=== 4. Verify API is healthy ===")
out, err = run("sleep 3 && curl -s -w ' HTTP:%{http_code}' http://localhost:8000/health --max-time 10")
print(out[:200] if out else "NO RESPONSE")
if err: print("ERR:", err[:200])

print()
print("=== 5. Verify login via nginx ===")
out, err = run(r"curl -s -w ' HTTP:%{http_code}' -X POST 'http://localhost:17452/cello/api/v1/auth/login' -H 'Content-Type: application/json' -d '{\"email\":\"demo@example.com\",\"password\":\"Demo1234!\"}' --max-time 10")
print(out[:300] if out else "NO RESPONSE")
if err: print("ERR:", err[:200])

ssh.close()
print()
print("=== Deployment complete ===")
