import re, sys, urllib.parse, urllib.request
from collections import OrderedDict

B = "https://raw.githubusercontent.com/QingRex/LoonKissSurge/main/Surge/"
APPS = ["广告平台", "百度贴吧", "百度网盘", "拼多多", "淘宝", "京东", "豆瓣", "脉脉", "闲鱼",
        "高德地图", "小黑盒", "什么值得买", "知乎", "最右",
        "12306", "丰巢", "虎扑", "迅雷", "X"]
# 可莉版丰巢需要 IPA 重签名，用奶思的；豆瓣两份叠加；X 可莉仓库里没有
F = "https://raw.githubusercontent.com/fmz200/wool_scripts/main/Surge/module/split/"
OVERRIDE = {"豆瓣": [B + urllib.parse.quote("豆瓣去广告.sgmodule"), F + "partD/Douban.sgmodule"], "丰巢": F + "partF/FengChao.sgmodule",
            "X": F + "partT/Twitter.sgmodule",
            # 可莉的通用规则：拦截穿山甲、广点通、百度、快手联盟等广告 SDK
            "广告平台": B + urllib.parse.quote("广告平台拦截器.sgmodule")}
SRC = []
for a in APPS:
    urls = OVERRIDE.get(a) or B + urllib.parse.quote(a + "去广告.sgmodule")
    SRC += [(a, u) for u in (urls if isinstance(urls, list) else [urls])]
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

out = ["#!name=去广告合集", "#!desc=" + "、".join(OrderedDict.fromkeys(a for a, _ in SRC)) + ""]
if args:
    out.append("#!arguments=" + ",".join(args))
if args_desc:
    out.append("#!arguments-desc=" + "\\n".join(args_desc))
for sec, lines in sections.items():
    if sec == "[MITM]":
        continue
    out += ["", sec] + lines
# 豆瓣广告图走 img*.doubanio.com/view/dale-online/dale_ad/，要解密才能被 URL Rewrite 拦下
hosts += ["img*.doubanio.com", "erebor.douban.com"]
# 解密 frodo.douban.com 会导致豆瓣影视详情打不开（blackmatrix7/ios_rule_script#1225）
hosts = [h for h in hosts if h != "frodo.douban.com"]
out += ["", "[MITM]", "hostname = %APPEND% " + ", ".join(OrderedDict.fromkeys(hosts))]
open(sys.argv[1], "w", encoding="utf-8").write("\n".join(out) + "\n")
print("ok", len(out), "lines,", len(set(hosts)), "hosts")
