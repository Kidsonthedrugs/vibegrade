
import urllib.request, json, time
P="http://127.0.0.1:2081"
op=urllib.request.build_opener(urllib.request.ProxyHandler({"http":P,"https":P}))
HDR={"User-Agent":"Mozilla/5.0 Chrome/131.0","accept":"application/json","Origin":"https://testnet.vibevibe.fun"}
B="https://testnet.vibevibe.fun/api/v1/chains/46630"

def get(p):
    for i in range(3):
        try:
            with op.open(urllib.request.Request(B+p,headers=HDR),timeout=40) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            return {"__status": e.code, "body": e.read()[:160].decode("utf-8","replace")}
        except Exception as e:
            time.sleep(1.5)

for q in ["/board?tab=GRADUATED", "/board?tab=GRADUATED&page=2", "/board?tab=GRADUATED&page=3",
          "/board?tab=GRADUATED&page=5", "/board?tab=GRADUATED&size=100"]:
    j=get(q)
    if "__status" in j:
        print(f"{q:44s} -> {j['__status']} {j['body'][:80]}")
        continue
    d=j.get("data",{})
    items=d.get("items",[])
    first=(items[0].get("launch") or {}).get("tokenAddress","")[:10] if items else "-"
    page=d.get("page")
    print(f"{q:44s} -> {len(items)} items | page={page} | first={first}")
