"""Check recent API logs for the failed login."""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("120.76.40.7", 22, "root", "sBHXvrQF44fuSpz",
            look_for_keys=False, allow_agent=False)


def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode().strip(), stderr.read().decode().strip()


# API logs with timestamps
out, err = run("docker logs docker-api-1 --tail 50 2>&1")
print("=== API Logs ===")
print(out if out else "NO LOGS")
if err: print("ERR:", err[:300])

print()

# Check if rate limiter data persists across restarts
out2, err2 = run(r"docker exec docker-api-1 python3 -c \"from app.infrastructure.rate_limiter import _limiter; print(dir(_limiter))\"" 2>&1 || echo "check failed")
print("=== Rate Limiter Check ===")
print(out2[:300] if out2 else "NO OUTPUT")
if err2: print("ERR:", err2[:300])

print()

# Check nginx access logs for the login POST
out3, err3 = run(r"docker logs docker-nginx-1 --tail 30 2>&1")
print("=== Nginx Logs ===")
print(out3[:1000] if out3 else "NO LOGS")
if err3: print("ERR:", err3[:300])

ssh.close()
