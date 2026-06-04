"""Investigate ERR_CONNECTION_CLOSED on login API."""
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


# Check if the API is responding to curl from the server itself
print("=== 1. Direct API test (within server) ===")
cmd = '''curl -s -w "\\nHTTP:%{http_code}" -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"demo@example.com","password":"Demo1234!"}' --max-time 10'''
out, err = run(cmd)
print(out[:500] if out else "NO OUTPUT")
if err: print("ERR:", err[:300])

print()
print("=== 2. Test via nginx on localhost ===")
cmd2 = '''curl -s -w "\\nHTTP:%{http_code}" -X POST http://localhost:17452/cello/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"demo@example.com","password":"Demo1234!"}' --max-time 10'''
out2, err2 = run(cmd2)
print(out2[:500] if out2 else "NO OUTPUT")
if err2: print("ERR:", err2[:300])

print()
print("=== 3. Test via Cloudflare Tunnel (local) ===")
cmd3 = "curl -s -w '\\nHTTP:%{http_code}' -X POST 'http://localhost:17452/cello/api/v1/auth/login' -H 'Content-Type: application/json' -d '{\"email\":\"demo@example.com\",\"password\":\"Demo1234!\"}' --max-time 10"
out3, err3 = run(cmd3)
print(out3[:500] if out3 else "NO OUTPUT")
if err3: print("ERR:", err3[:300])

print()
print("=== 4. Check rate limiter (flush) ===")
cmd4 = "docker exec docker-api-1 python3 -c \"from app.infrastructure.rate_limiter import RateLimiter; print('Rate limiter imported ok')\""
out4, err4 = run(cmd4)
print(out4[:300] if out4 else "NO OUTPUT")
if err4: print("ERR:", err4[:300])

print()
print("=== 5. Check Cloudflare tunnel status ===")
cmd5 = "ps aux | grep cloudflared | head -5"
out5, err5 = run(cmd5)
print(out5[:500] if out5 else "NO OUTPUT (no cloudflared process?)")
if err5: print("ERR:", err5[:300])

print()
print("=== 6. Check API logs for recent errors ===")
cmd6 = "docker logs docker-api-1 --tail 50 2>&1"
out6, err6 = run(cmd6)
print(out6[:1500] if out6 else "NO OUTPUT")
if err6: print("ERR:", err6[:300])

print()
print("=== 7. Check nginx logs ===")
cmd7 = "docker logs docker-nginx-1 --tail 30 2>&1"
out7, err7 = run(cmd7)
print(out7[:1000] if out7 else "NO OUTPUT")
if err7: print("ERR:", err7[:300])

print()
print("=== 8. Check if cloudflared is running as a service ===")
cmd8 = "systemctl status cloudflared 2>/dev/null | head -10 || cat /etc/systemd/system/cloudflared* 2>/dev/null | head -20 || echo 'No systemd cloudflared found'"
out8, err8 = run(cmd8)
print(out8[:500] if out8 else "NO OUTPUT")
if err8: print("ERR:", err8[:300])

ssh.close()
