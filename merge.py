import re, sys, urllib.parse, urllib.request
from collections import OrderedDict

B = "https://raw.githubusercontent.com/QingRex/LoonKissSurge/main/Surge/"
APPS = ["百度贴吧", "百度网盘", "拼多多", "淘宝", "京东", "豆瓣", "脉脉", "闲鱼",
        "高德地图", "小黑盒", "什么值得买", "知乎", "最右"]
# 可莉版豆瓣需要 IPA 重签名，App Store 版豆瓣用奶思的
OVERRIDE = {"豆瓣": "https://raw.githubusercontent.com/fmz200/wool_scripts/main/Surge/module/split/partD/Douban.sgmodule"}
SRC = [(a, OVERRIDE.get(a) or B + urllib.parse.quote(a + "去广告.sgmodule")) for a in APPS]
SRC.insert(10, ("YouTube", "https://raw.githubusercontent.com/Maasea/sgmodule/master/YouTube.Enhance.sgmodule"))

sections = OrderedDict()
hosts, args, args_desc = [], [], []
seen = {}
for app, url in SRC:
    text = urllib.request.urlopen(url, timeout=30).read().decode("utf-8")
    cur = None
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("#!arguments-desc="):
            args_desc.append(s.split("=", 1)[1])
        elif s.startswith("#!arguments="):
            args.append(s.split("=", 1)[1])
        elif s.startswith("#!") or not s:
            continue
        elif re.fullmatch(r"\[.+\]", s):
            cur = s
            sections.setdefault(cur, []).append(f"# {app}")
        elif cur == "[MITM]":
            m = re.match(r"hostname\s*=\s*(%APPEND%)?\s*(.*)", s)
            if m:
                hosts += [h.strip() for h in m.group(2).split(",") if h.strip()]
        elif cur == "[Script]" and "=" in s and not s.startswith("#"):
            name, rest = s.split("=", 1)
            name = f"{app}-{name.strip()}"
            seen[name] = seen.get(name, 0) + 1
            if seen[name] > 1:
                name += str(seen[name])
            sections[cur].append(f"{name} ={rest}")
        elif cur:
            sections[cur].append(line)

out = ["#!name=去广告合集", "#!desc=百度贴吧/网盘、拼多多、淘宝、京东、豆瓣、脉脉、闲鱼、高德、YouTube、小黑盒、什么值得买、知乎、最右"]
if args:
    out.append("#!arguments=" + ",".join(args))
if args_desc:
    out.append("#!arguments-desc=" + "\\n".join(args_desc))
for sec, lines in sections.items():
    if sec == "[MITM]":
        continue
    out += ["", sec] + lines
out += ["", "[MITM]", "hostname = %APPEND% " + ", ".join(OrderedDict.fromkeys(hosts))]
open(sys.argv[1], "w", encoding="utf-8").write("\n".join(out) + "\n")
print("ok", len(out), "lines,", len(set(hosts)), "hosts")
