"""Verify login fix deployment."""
import time
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('120.76.40.7', 22, 'root', 'sBHXvrQF44fuSpz',
            look_for_keys=False, allow_agent=False)


def run(cmd):
    s, o, e = ssh.exec_command(cmd)
    return o.read().decode().strip(), e.read().decode().strip()


# Wait for API to be healthy
for i in range(10):
    o, e = run("curl -s -w '%{http_code}' http://localhost:8000/health --max-time 5")
    code = o[-3:] if len(o) >= 3 else 'N/A'
    print(f'Attempt {i+1}: {code}  output={o[:60]}')
    if 'ok' in o.lower():
        print('API is ready!')
        break
    time.sleep(3)

print()

# Test login - use heredoc to avoid quoting hell
cmd = r"""curl -s -w ' HTTP:%{http_code}' -X POST 'http://localhost:17452/cello/api/v1/auth/login' -H 'Content-Type: application/json' -d '{"email":"demo@example.com","password":"Demo1234!"}' --max-time 10"""
o, e = run(cmd)
print(f'Login via nginx: {o[:300]}')

# Direct test
o2, e2 = run(r"""curl -s -w ' HTTP:%{http_code}' -X POST 'http://localhost:8000/api/v1/auth/login' -H 'Content-Type: application/json' -d '{"email":"demo@example.com","password":"Demo1234!"}' --max-time 10""")
print(f'Direct to API: {o2[:300]}')

print()
print('=== API Logs ===')
o3, e3 = run('docker logs docker-api-1 --tail 20 2>&1')
print(o3[-1500:] if o3 else 'NO LOGS')

ssh.close()
