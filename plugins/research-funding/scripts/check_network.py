#!/usr/bin/env python3
"""Check, in a few seconds, whether this environment can reach the data the pipeline needs.

Run it before anything else. It tests the GitHub data mirror, the EU Funding & Tenders
API, the CORDIS download server, ORCID and the Python package index, plus the Python
packages the scripts import. All checks run in parallel with short timeouts.

Usage:
    python check_network.py            # full report
    python check_network.py --quiet    # only the verdict, plus the fix instructions if blocked

Exit codes:
    0 = READY: call and CORDIS data can be fetched (from the EU or the GitHub mirror).
        Warnings (e.g. ORCID blocked) may still be printed.
    2 = BLOCKED: the pipeline cannot fetch verified data. Show the user the text between
        the USER MESSAGE lines, in the user's language, and stop.
"""
import importlib.util
import json
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor

TIMEOUT = 8
UA = {"User-Agent": "horizon-europe-consortium-finder-plugin"}
MIRROR = "https://raw.githubusercontent.com/madsberggreen/Horizon-Europe-Consortium-Finder/data/manifest.json"
EU_API = "https://api.tech.ec.europa.eu/search-api/prod/rest/search"
CORDIS = "https://cordis.europa.eu/data/cordis-HORIZONprojects-csv.zip"
ORCID = "https://pub.orcid.org/v3.0/0000-0002-1825-0097/person"  # ORCID's public test record
PYPI = "https://pypi.org/simple/reportlab/"

# Domains the user should allow, in order of importance.
DOMAINS = [
    ("raw.githubusercontent.com", "required: weekly copy of the EU call and CORDIS data"),
    ("api.tech.ec.europa.eu", "recommended: live EU call search"),
    ("ec.europa.eu", "recommended: full call texts"),
    ("cordis.europa.eu", "recommended: live CORDIS project data"),
    ("pub.orcid.org", "recommended: researcher publication lists"),
    ("pypi.org and files.pythonhosted.org", "needed only if Python packages are missing"),
]
PACKAGES = {"requests": "call search", "pandas": "CORDIS analysis", "reportlab": "PDF reports"}


def get(url, method="GET", headers=None, data=None):
    req = urllib.request.Request(url, method=method, data=data, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.status, r.headers.get("Content-Type", ""), r.read(200_000) if method != "HEAD" else b""


def check_mirror():
    status, _, body = get(MIRROR)
    built = json.loads(body).get("built", "unknown")
    return status == 200, f"data copy built {built}"


def check_eu_api():
    # A one-result search; a blocking proxy answers with an HTML error page instead of JSON.
    boundary = "----cfcheck"
    parts = []
    for name, value in (("query", '{"bool":{"must":[{"terms":{"type":["1"]}}]}}'), ("languages", '["en"]')):
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"; filename="blob"\r\n'
                     f"Content-Type: application/json\r\n\r\n{value}\r\n")
    data = ("".join(parts) + f"--{boundary}--\r\n").encode()
    status, _, body = get(EU_API + "?apiKey=SEDIA&text=education&pageSize=1&pageNumber=1", method="POST",
                          headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}, data=data)
    json.loads(body)
    return status == 200, "live search answers"


def check_cordis():
    status, ctype, _ = get(CORDIS, method="HEAD")
    return status == 200 and "html" not in ctype.lower(), "download server answers"


def check_orcid():
    status, _, body = get(ORCID, headers={"Accept": "application/json"})
    json.loads(body)
    return status == 200, "public API answers"


def check_pypi():
    status, _, _ = get(PYPI)
    return status == 200, "package index answers"


def run(fn):
    try:
        ok, note = fn()
        return ok, note
    except Exception as e:  # blocked, timed out, proxy error page, bad JSON ...
        return False, f"{type(e).__name__}: {str(e)[:90]}"


def user_message(missing_pkgs, pypi_ok):
    lines = [
        "Claude can't reach the internet from its work environment, so it can't fetch the open",
        "Horizon Europe calls and EU project data. The plugin itself works; this is a setting.",
        "",
        "How to fix it (about 2 minutes):",
        "1. In Claude, open Settings, then Capabilities.",
        "2. Under code execution (\"Code execution and file creation\"), turn on network access",
        "   (\"Allow network egress\").",
        "3. Add these domains to the list of allowed domains:",
    ]
    lines += [f"     - {d}  ({why})" for d, why in DOMAINS]
    lines += [
        "   raw.githubusercontent.com alone is enough to run the whole search.",
        "   If the added domains don't take effect, choose \"All domains\" instead.",
        "4. On an organisation account (Team or Enterprise), only an owner or admin can change",
        "   this, under Organization settings, then Capabilities. Send them the list above.",
        "5. To be safe, start a new chat and run /start again.",
    ]
    if missing_pkgs and not pypi_ok:
        lines += ["", "Also missing Python packages: " + ", ".join(missing_pkgs) +
                  ". Allowing pypi.org and files.pythonhosted.org lets Claude install them."]
    return lines


def main():
    quiet = "--quiet" in sys.argv
    checks = {"GitHub data copy (raw.githubusercontent.com)": check_mirror,
              "EU call search (api.tech.ec.europa.eu)": check_eu_api,
              "CORDIS downloads (cordis.europa.eu)": check_cordis,
              "ORCID (pub.orcid.org)": check_orcid,
              "Python package index (pypi.org)": check_pypi}
    with ThreadPoolExecutor(max_workers=len(checks)) as ex:
        results = dict(zip(checks, ex.map(run, checks.values())))
    mirror_ok, eu_ok, cordis_ok, orcid_ok, pypi_ok = (results[k][0] for k in checks)
    missing = [p for p in PACKAGES if importlib.util.find_spec(p) is None]

    calls_ok = mirror_ok or eu_ok
    cordis_data_ok = mirror_ok or cordis_ok
    pkgs_ok = not missing or pypi_ok
    ready = calls_ok and cordis_data_ok and pkgs_ok

    if not quiet:
        print("NETWORK CHECK")
        for name, (ok, note) in results.items():
            print(f"  [{'OK' if ok else 'BLOCKED'}] {name} - {note}")
        for p, use in PACKAGES.items():
            print(f"  [{'OK' if p not in missing else 'MISSING'}] Python package {p} ({use})")
        print()

    warnings = []
    if ready and not orcid_ok:
        warnings.append("ORCID is blocked: build the profile from the institution's pages and web search, "
                        "and say so in the profile. Tell the user that allowing pub.orcid.org gives better profiles.")
    if ready and missing:
        warnings.append(f"Install missing packages before use: pip install {' '.join(missing)}")
    if ready and not eu_ok:
        warnings.append("EU servers are blocked; the scripts will use the GitHub data copy automatically. No action needed.")

    if ready:
        print("VERDICT: READY")
        for w in warnings:
            print("WARNING: " + w)
        sys.exit(0)

    print("VERDICT: BLOCKED - stop here; do not start the profile or any other step.")
    print("Give the user the message below in their own language, keep the domain names unchanged:")
    print("----- USER MESSAGE -----")
    print("\n".join(user_message(missing, pypi_ok)))
    print("----- END USER MESSAGE -----")
    sys.exit(2)


if __name__ == "__main__":
    main()
