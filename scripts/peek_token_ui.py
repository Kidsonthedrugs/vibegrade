
import urllib.request, re, json, html as H, time
P = "http://127.0.0.1:2081"
op = urllib.request.build_opener(urllib.request.ProxyHandler({"http": P, "https": P}))
HDR = {"User-Agent": "Mozilla/5.0 Chrome/131.0"}

def get(u):
    for _ in range(3):
        try:
            with op.open(urllib.request.Request(u, headers=HDR), timeout=45) as r:
                return r.read()
        except Exception:
            time.sleep(2)
    return None

h = get("https://testnet.vibevibe.fun/docs/protocol")
m = re.search(r'<meta name="seedify-landing" content="(.*?)"', h.decode("utf-8", "replace"), re.S)
mp = json.loads(H.unescape(m.group(1)))
chunk = mp["routes"]["token"][0]
print("chunk:", chunk)
d = get("https://testnet.vibevibe.fun" + chunk)
s = d.decode("utf-8", "replace")
print("bytes:", len(s))

pattern = re.compile(r'"([^"\\]{16,110})"')
strs = set(pattern.findall(s))
kw = ("graduat", "curve", "progress", "left", "target", "holder", "volume", "price impact", "score", "alert", "airdrop")
hits = [x for x in strs if any(k in x.lower() for k in kw) and re.search(r"[a-z] [a-z]", x)]
print("UI strings:", len(hits))
for x in sorted(hits)[:50]:
    print(" -", x)
