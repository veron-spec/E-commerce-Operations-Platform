import urllib.request

r = urllib.request.urlopen('http://localhost:8100/')
html = r.read().decode('utf-8')
checks = [
    ('sidebar', 'sidebar' in html),
    ('dark mode toggle', 'themeIcon' in html),
    ('toast container', 'toastContainer' in html),
    ('nav links', '数据看板' in html),
    ('page title', '电商运营' in html),
    ('Chart.js', 'chart.js' in html),
    ('Bootstrap CSS', 'bootstrap.min.css' in html),
    ('app.js', 'app.js' in html),
    ('style.css', 'style.css' in html),
]
for name, ok in checks:
    print(f'  {"OK" if ok else "MISSING"} {name}')
print(f'\nHTML size: {len(html)} bytes')
print(f'Contains orders link: {"orders" in html}')
print(f'Contains automation link: {"automation" in html}')
print(f'Contains settings link: {"settings" in html}')

# Test orders page
r2 = urllib.request.urlopen('http://localhost:8100/orders')
html2 = r2.read().decode('utf-8')
print(f'\nOrders page: {len(html2)} bytes, title check: {"订单管理" in html2}')

# Test automation page
r3 = urllib.request.urlopen('http://localhost:8100/automation')
html3 = r3.read().decode('utf-8')
print(f'Automation page: {len(html3)} bytes, title check: {"自动化规则" in html3}')

# Test API routes
r4 = urllib.request.urlopen('http://localhost:8100/api/v1/orders')
import json
orders_data = json.loads(r4.read())
print(f'\nOrders API: total={orders_data["total"]}, page={orders_data["page"]}')

r5 = urllib.request.urlopen('http://localhost:8100/api/v1/automation/rules')
rules_data = json.loads(r5.read())
print(f'Automation API: total={rules_data["total"]}, active={rules_data["active_count"]}')

# Test sales page
r6 = urllib.request.urlopen('http://localhost:8100/sales')
print(f'Sales page: {len(r6.read().decode("utf-8"))} bytes')

# Test inventory page
r7 = urllib.request.urlopen('http://localhost:8100/inventory')
print(f'Inventory page: {len(r7.read().decode("utf-8"))} bytes')

# Test stores page
r8 = urllib.request.urlopen('http://localhost:8100/stores')
print(f'Stores page: {len(r8.read().decode("utf-8"))} bytes')

# Test settings page
r9 = urllib.request.urlopen('http://localhost:8100/settings')
print(f'Settings page: {len(r9.read().decode("utf-8"))} bytes')

print('\nAll pages OK!')
