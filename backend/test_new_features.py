"""Test the 4 new automation features."""
import json
import urllib.request

BASE = "http://localhost:8100"

pages = [
    ("/product-selections", "捕获选品", "捕获选品"),
    ("/auto-reply", "自动化客服", "自动化客服"),
    ("/suggestions", "运营建议", "运营建议"),
    ("/retrospectives", "复盘分析", "复盘分析"),
]

print("=== Page Tests ===")
all_ok = True
for path, title, keyword in pages:
    try:
        r = urllib.request.urlopen(BASE + path)
        html = r.read().decode("utf-8")
        ok_title = title in html
        ok_keyword = keyword in html
        ok = ok_title and ok_keyword
        if not ok:
            all_ok = False
        print(f'  [{"OK" if ok else "FAIL"}] {path} - title check: {ok_title}, keyword check: {ok_keyword} ({len(html)} bytes)')
    except Exception as e:
        all_ok = False
        print(f'  [FAIL] {path} - {e}')

# Test APIs
print("\n=== API Tests ===")

# Product Selections API
try:
    r = urllib.request.urlopen(BASE + "/api/v1/product-selections")
    data = json.loads(r.read())
    print(f'  Product Selections list: total={data["total"]}, page={data["page"]}')
except Exception as e:
    all_ok = False
    print(f'  [FAIL] Product Selections list: {e}')

try:
    r = urllib.request.urlopen(BASE + "/api/v1/product-selections/stats")
    data = json.loads(r.read())
    print(f'  Product Selections stats: total={data["total"]}')
except Exception as e:
    all_ok = False
    print(f'  [FAIL] Product Selections stats: {e}')

# Auto Reply API
try:
    r = urllib.request.urlopen(BASE + "/api/v1/auto-reply")
    data = json.loads(r.read())
    print(f'  Auto Reply list: total={data["total"]}')
except Exception as e:
    all_ok = False
    print(f'  [FAIL] Auto Reply list: {e}')

try:
    r = urllib.request.urlopen(BASE + "/api/v1/auto-reply/stats")
    data = json.loads(r.read())
    print(f'  Auto Reply stats: total_rules={data.get("total_rules")}, enabled={data.get("enabled")}')
except Exception as e:
    all_ok = False
    print(f'  [FAIL] Auto Reply stats: {e}')

# Suggestions API
try:
    r = urllib.request.urlopen(BASE + "/api/v1/suggestions")
    data = json.loads(r.read())
    print(f'  Suggestions list: total={data["total"]}')
except Exception as e:
    all_ok = False
    print(f'  [FAIL] Suggestions list: {e}')

try:
    r = urllib.request.urlopen(BASE + "/api/v1/suggestions/stats")
    data = json.loads(r.read())
    print(f'  Suggestions stats: total={data["total"]}, pending={data.get("pending")}')
except Exception as e:
    all_ok = False
    print(f'  [FAIL] Suggestions stats: {e}')

# Retrospectives API
try:
    r = urllib.request.urlopen(BASE + "/api/v1/retrospectives")
    data = json.loads(r.read())
    print(f'  Retrospectives list: total={data["total"]}')
except Exception as e:
    all_ok = False
    print(f'  [FAIL] Retrospectives list: {e}')

try:
    r = urllib.request.urlopen(BASE + "/api/v1/retrospectives/stats")
    data = json.loads(r.read())
    print(f'  Retrospectives stats: total={data["total"]}')
except Exception as e:
    all_ok = False
    print(f'  [FAIL] Retrospectives stats: {e}')

# Test feature APIs that generate data
print("\n=== Feature API Actions ===")

# 1. Scan product selections
try:
    req = urllib.request.Request(BASE + "/api/v1/product-selections/scan", method="POST", data=b"")
    r = urllib.request.urlopen(req)
    data = json.loads(r.read())
    print(f'  Scan product selections: found={data.get("found", "?")}')
except Exception as e:
    all_ok = False
    print(f'  [FAIL] Scan product selections: {e}')

# 2. List product selections after scan
try:
    r = urllib.request.urlopen(BASE + "/api/v1/product-selections")
    data = json.loads(r.read())
    print(f'  Product Selections after scan: total={data["total"]}')
    for item in data["items"][:2]:
        print(f'    - {item["title"]}: score={item["selection_score"]}')
except Exception as e:
    all_ok = False
    print(f'  [FAIL] Product selections after scan: {e}')

# 3. Generate suggestions
try:
    req = urllib.request.Request(BASE + "/api/v1/suggestions/generate", method="POST", data=b"")
    r = urllib.request.urlopen(req)
    data = json.loads(r.read())
    print(f'  Generate suggestions: generated={data.get("generated", "?")}')
except Exception as e:
    all_ok = False
    print(f'  [FAIL] Generate suggestions: {e}')

# 4. Generate weekly retrospective
try:
    req = urllib.request.Request(BASE + "/api/v1/retrospectives/generate?store_id=1&period_type=weekly", method="POST")
    r = urllib.request.urlopen(req)
    data = json.loads(r.read())
    print(f'  Generate weekly retrospective: id={data.get("id", "?")}')
except Exception as e:
    all_ok = False
    print(f'  [FAIL] Generate retrospective: {e}')

# 5. List retrospectives
try:
    r = urllib.request.urlopen(BASE + "/api/v1/retrospectives")
    data = json.loads(r.read())
    print(f'  Retrospectives after generate: total={data["total"]}')
except Exception as e:
    all_ok = False
    print(f'  [FAIL] Retrospectives list after generate: {e}')

# 6. Get retrospective detail
try:
    rid = data["items"][0]["id"]
    r = urllib.request.urlopen(BASE + f"/api/v1/retrospectives/{rid}")
    detail = json.loads(r.read())
    print(f'  Retrospective detail: revenue={detail["data_summary"]["total_revenue"]}, insights={len(detail.get("insights", []))}')
except Exception as e:
    all_ok = False
    print(f'  [FAIL] Retrospective detail: {e}')

# 7. Publish retrospective
try:
    req = urllib.request.Request(BASE + f"/api/v1/retrospectives/{rid}/publish", method="POST", data=b"")
    r = urllib.request.urlopen(req)
    pub_data = json.loads(r.read())
    print(f'  Publish retrospective: status={pub_data["status"]}')
except Exception as e:
    all_ok = False
    print(f'  [FAIL] Publish retrospective: {e}')

# 8. Create auto reply rule
try:
    rule_data = json.dumps({
        "name": "自动回复测试",
        "trigger_keywords": ["退款", "退货"],
        "match_type": "contains",
        "reply_template": "感谢您的咨询，请联系客服处理退款事宜。",
        "priority": 1,
    }).encode("utf-8")
    req = urllib.request.Request(BASE + "/api/v1/auto-reply", data=rule_data, method="POST", headers={"Content-Type": "application/json"})
    r = urllib.request.urlopen(req)
    new_rule = json.loads(r.read())
    print(f'  Create auto reply rule: id={new_rule.get("id", "?")}')
except Exception as e:
    all_ok = False
    print(f'  [FAIL] Create auto reply rule: {e}')

# 9. Test auto reply match
try:
    test_data = json.dumps({"message": "我要退款"}).encode("utf-8")
    req = urllib.request.Request(BASE + "/api/v1/auto-reply/test", data=test_data, method="POST", headers={"Content-Type": "application/json"})
    r = urllib.request.urlopen(req)
    match_result = json.loads(r.read())
    print(f'  Test auto reply: matched={match_result.get("matched")}, rule="{match_result.get("matched_rule")}"')
except Exception as e:
    all_ok = False
    print(f'  [FAIL] Test auto reply: {e}')

print(f'\n=== {"All tests PASSED" if all_ok else "SOME TESTS FAILED"} ===')
