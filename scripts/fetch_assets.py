
import urllib.request, os, time
P="http://127.0.0.1:2081"
op=urllib.request.build_opener(urllib.request.ProxyHandler({"http":P,"https":P}))
HDR={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0 Safari/537.36"}
OUT=os.path.expanduser("~/vibegrade/assets"); os.makedirs(OUT,exist_ok=True)
B="https://testnet.vibevibe.fun"
files={
 "clashdisplay-600.woff2":"/fonts/clashdisplay-600-latin-core.woff2",
 "instrumentsans.woff2":"/fonts/instrumentsans-latin.woff2",
 "jetbrainsmono.woff2":"/fonts/jetbrainsmono-latin.woff2",
 "vibevibe-lockup.svg":"/vibevibe-lockup.svg",
 "vibevibe-mark.svg":"/vibevibe-mark.svg",
 "logo-soft-light.svg":"/assets/logo-soft-light.svg",
 "favicon.svg":"/favicon.svg",
}
for n,u in files.items():
    ok=False
    for i in range(3):
        try:
            with op.open(urllib.request.Request(B+u,headers=HDR),timeout=40) as r:
                d=r.read(); open(os.path.join(OUT,n),"wb").write(d)
                print(f"OK {n:26s} {len(d):>7d}  {r.headers.get('content-type')}")
                ok=True; break
        except Exception as e:
            time.sleep(1.5)
    if not ok: print("FAIL",n,u)
