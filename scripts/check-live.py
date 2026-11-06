# /// script
# dependencies = ["pyyaml"]
# ///
"""Re-fetch live Render settings and compare them field by field with render.yaml.
Reads env var NAMES only. The API key is read from ~/.render/cli.yaml and never printed."""
import json, os, re, sys, urllib.request
import yaml

key = re.search(r"^\s*key:\s*\"?([^\"\s]+)", open(os.path.expanduser("~/.render/cli.yaml")).read(), re.M).group(1)
OWNER = "tea-d69tn76mcj7s738vmt10"

def get(path):
    out, cursor = [], None
    while True:
        url = f"https://api.render.com/v1{path}{'&' if '?' in path else '?'}limit=100" + (f"&cursor={cursor}" if cursor else "")
        d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})))
        if not isinstance(d, list):
            return d
        out += d
        if len(d) < 100:
            return out
        cursor = d[-1]["cursor"]

bp = yaml.safe_load(open(sys.argv[1]))
fsvc = {}
for p in bp.get("projects", []):
    for e in p["environments"]:
        for s in e.get("services", []):
            fsvc[s["name"]] = (s, f"{p['name']}/{e['name']}")
for s in bp.get("services", []):
    fsvc[s["name"]] = (s, None)

live = [x["service"] for x in get(f"/services?ownerId={OWNER}")]
proj_ids = set()
for pr in get(f"/projects?ownerId={OWNER}"):
    for env in get(f"/environments?projectId={pr['project']['id']}"):
        proj_ids |= set(env["environment"]["serviceIds"])
groups = {}
for g in get(f"/env-groups?ownerId={OWNER}"):
    g = g["envGroup"]
    full = get(f"/env-groups/{g['id']}")
    groups[g["name"]] = (sorted(v["key"] for v in full.get("envVars", [])), [l["id"] for l in g.get("serviceLinks", [])])

problems = []
def eq(svc, field, filev, livev):
    if filev != livev:
        problems.append(f"{svc}: {field}: file={filev!r} live={livev!r}")

eq("*", "service count", len(fsvc), len(live))
for s in live:
    n = s["name"]
    if n not in fsvc:
        problems.append(f"{n}: missing from file"); continue
    f, where = fsvc[n]
    sd = s["serviceDetails"]
    eq(n, "in project", where is not None, s["id"] in proj_ids)
    eq(n, "repo", f.get("repo"), s["repo"])
    eq(n, "branch", f.get("branch"), s["branch"])
    eq(n, "rootDir", f.get("rootDir", ""), s.get("rootDir", ""))
    eq(n, "autoDeployTrigger", f.get("autoDeployTrigger"), s["autoDeployTrigger"])
    bf = s.get("buildFilter") or {}
    eq(n, "buildFilter", f.get("buildFilter", {}), {k: v for k, v in bf.items() if v})
    if s["type"] == "static_site":
        eq(n, "type/runtime", (f["type"], f["runtime"]), ("web", "static"))
        eq(n, "buildCommand", f.get("buildCommand"), sd.get("buildCommand"))
        eq(n, "staticPublishPath", f.get("staticPublishPath"), sd["publishPath"])
        eq(n, "previews", f.get("previews", {}).get("generation"), sd["previews"]["generation"])
        rts = sorted((r["route"] for r in get(f"/services/{s['id']}/routes")), key=lambda r: r["priority"])
        eq(n, "routes", f.get("routes", []), [{"type": r["type"], "source": r["source"], "destination": r["destination"]} for r in rts])
        hd = [h["header"] for h in get(f"/services/{s['id']}/headers")]
        eq(n, "headers", f.get("headers", []), [{"path": h["path"], "name": h["name"], "value": h["value"]} for h in hd])
    else:
        esd = sd["envSpecificDetails"]
        eq(n, "type", f["type"], {"web_service": "web", "cron_job": "cron"}[s["type"]])
        eq(n, "runtime", f.get("runtime"), sd["runtime"])
        eq(n, "plan", f.get("plan"), sd["plan"])
        eq(n, "region", f.get("region"), sd["region"])
        eq(n, "buildCommand", f.get("buildCommand"), esd["buildCommand"])
        eq(n, "startCommand", f.get("startCommand"), esd["startCommand"])
        if s["type"] == "cron_job":
            eq(n, "schedule", f.get("schedule"), sd["schedule"])
        else:
            eq(n, "healthCheckPath", f.get("healthCheckPath", ""), sd.get("healthCheckPath", ""))
            eq(n, "numInstances", f.get("numInstances"), sd["numInstances"])
            eq(n, "previews", f.get("previews", {}).get("generation"), sd["previews"]["generation"])
    if s["type"] != "cron_job":
        eq(n, "renderSubdomainPolicy", f.get("renderSubdomainPolicy"), sd.get("renderSubdomainPolicy"))
        cds = [c["customDomain"] for c in get(f"/services/{s['id']}/custom-domains")]
        livedom = sorted(c["name"] for c in cds)
        filedom = set(f.get("domains", []))
        implied = {"www." + d for d in filedom if not d.startswith("www.") and d.count(".") == 1}
        eq(n, "domains (incl. implied www)", sorted(filedom | (implied & set(livedom))), livedom)
    ev = f.get("envVars", [])
    eq(n, "env names", sorted(e["key"] for e in ev if "key" in e), sorted(v["envVar"]["key"] for v in get(f"/services/{s['id']}/env-vars")))
    eq(n, "env groups", sorted(e["fromGroup"] for e in ev if "fromGroup" in e), sorted(g for g, (_, ids) in groups.items() if s["id"] in ids))
    bad = [e for e in ev if "key" in e and (e.get("sync") is not False or "value" in e)]
    eq(n, "env vars not sync:false or with value", bad, [])

fg = {g["name"]: g for g in bp.get("envVarGroups", [])}
eq("*", "env group names", sorted(fg), sorted(groups))
for g, (keys, _) in groups.items():
    if g in fg:
        eq(g, "group keys", sorted(e["key"] for e in fg[g]["envVars"]), keys)
        eq(g, "group vars sync:false, no value", [e for e in fg[g]["envVars"] if e.get("sync") is not False or "value" in e], [])

print("\n".join(problems) if problems else f"OK: {len(live)} services and {len(groups)} env groups match the file on every checked field.")
