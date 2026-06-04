"""Check Cloudflare tunnel config and docker compose."""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("120.76.40.7", 22, "root", "sBHXvrQF44fuSpz",
            look_for_keys=False, allow_agent=False)


def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode().strip(), stderr.read().decode().strip()


print("=== Cloudflare Tunnel Config ===")
out, err = run("cat /root/.cloudflared/config.yml")
print(out[:1000] if out else "NO CONFIG")
if err: print("ERR:", err[:200])

print()
print("=== Docker Compose (relevant section) ===")
out2, err2 = run(r"grep -E 'ports:|environment:|command:|image:|restart:' /root/E-commerce-Operations-Platform/docker/docker-compose.yml | head -20")
print(out2[:1000] if out2 else "NO OUTPUT")
if err2: print("ERR:", err2[:200])

print()
print("=== Check cloudflared tunnel list ===")
out3, err3 = run("cloudflared tunnel list 2>/dev/null || echo 'Cannot list tunnels'")
print(out3[:500] if out3 else "NO OUTPUT")
if err3: print("ERR:", err3[:200])

print()
print("=== Check nginx error logs ===")
out4, err4 = run(r"docker logs docker-nginx-1 --tail 30 2>&1")
print(out4[:800] if out4 else "NO OUTPUT")
if err4: print("ERR:", err4[:200])

print()
print("=== API logs for the recent browser test ===")
out5, err5 = run(r"docker logs docker-api-1 --tail 30 2>&1")
print(out5[:1500] if out5 else "NO OUTPUT")
if err5: print("ERR:", err5[:200])

ssh.close()
