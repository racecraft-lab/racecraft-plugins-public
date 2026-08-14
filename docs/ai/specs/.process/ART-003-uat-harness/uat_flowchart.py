"""ART-003 slice 3 (#439) manual UAT — flowchart.html on a real file:// URL."""

import json
import os
import sys
import tempfile
import time

from cdp import Chrome, Report

# The run this evidence records was performed in a feature worktree that no longer
# exists. Resolve the repository root from this file instead, so the harness runs
# from any clone. ART003_ROOT points it at a different checkout; UAT_URL replaces
# the whole path.
ROOT = os.environ.get("ART003_ROOT") or os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), *[os.pardir] * 5))
URL = os.environ.get("UAT_URL") or ("file://" + ROOT + "/speckit-pro/artifact-gallery/templates/flowchart.html")
# Screenshots land outside the tree by default: a run must not leave untracked
# files in the repository.
SHOTS = os.environ.get("ART003_SHOTS") or os.path.join(tempfile.gettempdir(), "art003-uat-shots")
os.makedirs(SHOTS, exist_ok=True)

R = Report("slice3 / flowchart")

NODE_IDS = ["nodes-connection-returns", "nodes-drain-the-outbox", "nodes-version-unchanged",
            "nodes-merge-the-draft", "nodes-write-acknowledged", "nodes-stop-and-report",
            "nodes-drafts-in-sync"]

c = Chrome()
try:
    c.enable_all()
    c.clear_events()

    # ---------- SC-001 console silence (network AVAILABLE) ----------
    c.navigate(URL, settle=3.0)
    online_console = c.console_report()
    R.check("SC-001", "console silent on load with the network available",
            len(online_console) == 0, json.dumps(online_console, indent=1))

    # ---------- US1-AS1 the drawing paints ----------
    paint = c.js("""
      (() => ({
        links: document.querySelectorAll('a.fc-link').length,
        edges: document.querySelectorAll('path.fc-edge').length,
        edgeLabels: document.querySelectorAll('text.fc-edge-label').length,
        markers: [...document.querySelectorAll('marker')].map(m => m.id),
        allLinksVisible: [...document.querySelectorAll('a.fc-link')]
          .every(a => { const r = a.getBoundingClientRect(); return r.width > 0 && r.height > 0; }),
        shapes: document.querySelectorAll('.fc-shape').length,
      }))()
    """)
    R.eq("US1-AS1", "seven interactive nodes drawn", paint["links"], 7)
    R.eq("US1-AS1", "seven edges drawn", paint["edges"], 7)
    R.eq("US1-AS1", "four edge labels drawn", paint["edgeLabels"], 4)
    R.eq("US1-AS1", "exactly one arrowhead marker", paint["markers"], ["fc-arrow"])
    R.check("US1-AS1", "every node has a non-zero box", paint["allLinksVisible"], paint)

    R.eq("US1-AS6", "rendered title matches the catalog entry byte for byte",
         c.js("document.getElementById('artifact-title').textContent.trim()"), "Flowchart")
    R.eq("US1-AS6", "document title", c.js("document.title"),
         "Flowchart — NIMBUS-101 Offline Draft Sync")

    # ---------- FR-040 detail region non-empty on first paint ----------
    first = c.js("""
      (() => { const open = [...document.querySelectorAll('details.node[open]')];
        return {count: open.length, id: open[0] ? open[0].id : null,
                h: open[0] ? open[0].getBoundingClientRect().height : 0,
                txt: open[0] ? open[0].textContent.trim().length : 0}; })()
    """)
    R.eq("FR-040", "exactly one node open on first paint", first["count"], 1)
    R.eq("FR-040", "the open node is the flow's first", first["id"], "nodes-connection-returns")
    R.check("FR-040", "the open detail renders non-empty",
            first["h"] > 0 and first["txt"] > 20, first)
    c.screenshot(os.path.join(SHOTS, "s3-01-first-paint.png"), full=True)

    # ---------- SC-005 zero export affordances / zero clipboard use ----------
    c.js("""
      window.__clipCalls = 0; window.__execCalls = 0;
      if (navigator.clipboard) { navigator.clipboard.writeText =
        function () { window.__clipCalls += 1; return Promise.resolve(); }; }
      document.execCommand = function () { window.__execCalls += 1; return false; };
    """)
    R.eq("SC-005", "no buttons/inputs beyond the shared theme toggle",
         c.js("document.querySelectorAll('button, input, select, textarea, form, [contenteditable]').length"
              " - document.querySelectorAll('button.rc-theme-toggle').length"), 0)

    # ---------- FR-041a exclusive group + FR-041c fragment reveal ----------
    names = c.js("[...document.querySelectorAll('details.node')].map(d => d.getAttribute('name'))")
    R.check("FR-041a", "all seven disclosures share one exclusive group name",
            len(names) == 7 and set(names) == {"flow-node"}, names)

    exclusive_ok, target_ok, reveal_rows = True, True, []
    for nid in NODE_IDS:
        c.js("location.hash = ''")
        c.js("""(() => { document.querySelectorAll('details.node').forEach(d => d.open = false);
                document.getElementById('nodes-connection-returns').open = true; })()""")
        # Focus the link by keyboard and activate it with Enter — no mouse.
        c.js("document.querySelector('a.fc-link[href=\"#%s-detail\"]').focus()" % nid)
        R.rows and None
        c.key("Enter", "Enter", 13)
        time.sleep(0.45)
        st = c.js("""
          (() => { const open=[...document.querySelectorAll('details.node[open]')];
            const t=document.getElementById('%s-detail');
            return {openCount: open.length, openId: open[0]?open[0].id:null,
                    hash: location.hash, isTarget: t ? t.matches(':target') : false,
                    active: document.activeElement ? document.activeElement.id : null,
                    inView: t ? (t.getBoundingClientRect().top >= -2 &&
                                 t.getBoundingClientRect().top <= window.innerHeight) : false}; })()
        """ % nid)
        reveal_rows.append({"node": nid, **st})
        if st["openCount"] != 1 or st["openId"] != nid:
            exclusive_ok = False
        if st["hash"] != "#%s-detail" % nid or not st["isTarget"]:
            target_ok = False

    R.check("FR-041c", "fragment navigation REVEALS a closed disclosure (all 7 nodes)",
            exclusive_ok, json.dumps(reveal_rows, indent=1))
    R.check("FR-041a", "exactly one disclosure open after every activation",
            all(r["openCount"] == 1 for r in reveal_rows), json.dumps(reveal_rows, indent=1))
    R.check("FR-039", "the activated detail becomes :target and is scrolled into view",
            target_ok and all(r["inView"] for r in reveal_rows), json.dumps(reveal_rows, indent=1))
    # Not only scroll: a reader on a screen reader must land in the entry, or the
    # link reveals content their focus never reaches. The sibling template does
    # this with tabindex="-1" on the same link targets.
    R.check("FR-039", "activating a node link moves focus into that node's entry",
            all(r["active"] == r["node"] + "-detail" for r in reveal_rows),
            json.dumps([{"node": r["node"], "active": r["active"]} for r in reveal_rows], indent=1))
    R.check("FR-019a", "the focusable drawing carries a role and an accessible name",
            c.js("""(() => { const f=document.querySelector('figure.diagram');
                     return !!f.getAttribute('role') && !!f.getAttribute('aria-label'); })()"""),
            c.js("""(() => { const f=document.querySelector('figure.diagram');
                     return {role: f.getAttribute('role'), label: f.getAttribute('aria-label'),
                             tabindex: f.getAttribute('tabindex')}; })()"""))
    R.eq("SC-005", "no clipboard write occurred during any activation",
         c.js("window.__clipCalls"), 0)
    R.eq("SC-005", "no execCommand copy occurred", c.js("window.__execCalls"), 0)

    # ---------- FR-038 disclosed state programmatic, no colour difference ----------
    ax = c.call("Accessibility.getFullAXTree")["nodes"]
    expanded = [n for n in ax if any(p.get("name") == "expanded" for p in n.get("properties", []))]
    exp_true = sum(1 for n in expanded
                   for p in n.get("properties", [])
                   if p.get("name") == "expanded" and p["value"]["value"] is True)
    R.eq("FR-038", "exactly one disclosure reports expanded=true to assistive tech", exp_true, 1)
    same = c.js("""
      (() => { const o=document.querySelector('details.node[open]');
        const cl=[...document.querySelectorAll('details.node')].find(d=>!d.open);
        const k=['color','backgroundColor','borderTopColor','borderLeftColor'];
        const a=getComputedStyle(o), b=getComputedStyle(cl);
        return k.filter(x => a[x] !== b[x]); })()
    """)
    R.check("FR-038", "open and closed disclosures differ in no colour", same == [], same)

    # ---------- SC-003 monochrome ----------
    mono = c.js("""
      (() => { const s=[...document.querySelectorAll('.fc-shape')];
        return {fills:[...new Set(s.map(e=>getComputedStyle(e).fill))],
                strokes:[...new Set(s.map(e=>getComputedStyle(e).stroke))]}; })()
    """)
    R.eq("SC-003", "all node shapes share one fill (shape, not hue, carries role)",
         len(mono["fills"]), 1)
    R.eq("SC-003", "all node shapes share one stroke", len(mono["strokes"]), 1)
    roles = c.js("[...document.querySelectorAll('text.fc-role')].map(t=>t.textContent.trim())")
    R.eq("FR-020a", "every node carries its role as a word", roles,
         ["start", "step", "decision", "step", "decision", "end · failure", "end · success"])
    edges = c.js("""
      (() => { const f=[...document.querySelectorAll('.fc-edge-fail')],
                     all=[...document.querySelectorAll('path.fc-edge')];
        return {fail: f.map(e=>getComputedStyle(e).strokeDasharray),
                plain: all.filter(e=>!e.classList.contains('fc-edge-fail'))
                          .map(e=>getComputedStyle(e).strokeDasharray),
                labels: [...document.querySelectorAll('text.fc-edge-label')].map(t=>t.textContent.trim())}; })()
    """)
    R.check("SC-003", "failure edges are dashed and ordinary edges are not",
            all(d != "none" for d in edges["fail"]) and all(d == "none" for d in edges["plain"]),
            edges)
    R.eq("FR-022a", "edge labels are words", edges["labels"], ["yes", "no", "yes", "no"])
    legend = c.js("""
      (() => ({dt:[...document.querySelectorAll('.legend dl dt')].map(e=>e.textContent.trim()),
               dd: document.querySelectorAll('.legend dl dd').length,
               swatches: document.querySelectorAll('.legend svg, .legend img').length}))()
    """)
    R.eq("FR-023", "legend states all seven conventions in words", legend["dt"],
         ["Stadium", "Rectangle", "Diamond", "Solid line, no label",
          "Solid line labelled yes", "Dashed line labelled no", "The open entry below"])
    R.eq("FR-023", "legend carries no meaning-bearing swatch", legend["swatches"], 0)
    c.vision("achromatopsia")
    time.sleep(0.3)
    c.screenshot(os.path.join(SHOTS, "s3-02-achromatopsia.png"), full=True)
    c.vision("none")

    # ---------- FR-019a accessibility of the drawing ----------
    svg_role = c.js("""
      (() => { const s=document.querySelector('figure.diagram svg');
        return {role: s.getAttribute('role'), labelledby: s.getAttribute('aria-labelledby'),
                title: (document.getElementById('flow-diagram-title')||{}).textContent}; })()
    """)
    R.check("FR-019a", "the drawing does not carry role=img (which would hide its nodes)",
            svg_role["role"] != "img", svg_role)
    ax_links = [n for n in ax if n.get("role", {}).get("value") == "link"
                and n.get("name", {}).get("value")]
    R.check("FR-019a", "all seven nodes survive in the accessibility tree as named links",
            len(ax_links) >= 7, "named links found: %d" % len(ax_links))

    # ---------- FR-030 / SC-002 the words alone carry the flow ----------
    narr = c.js("""
      (() => { const n=document.querySelector('div.narration'); if(!n) return null;
        const cs=getComputedStyle(n); const r=n.getBoundingClientRect();
        return {h:r.height, w:r.width, display:cs.display, visibility:cs.visibility,
                ariaHidden:n.hasAttribute('aria-hidden'), hidden:n.hasAttribute('hidden'),
                inDetails: !!n.closest('details'), len:n.textContent.trim().length}; })()
    """)
    R.check("FR-030", "the text equivalent renders, unhidden and outside any disclosure",
            narr and narr["h"] > 0 and narr["display"] != "none"
            and not narr["ariaHidden"] and not narr["hidden"] and not narr["inDetails"], narr)
    LABELS = ["Connection returns", "Drain the outbox", "Version unchanged?", "Merge the draft",
              "Write acknowledged?", "Stop and report", "Drafts in sync"]
    missing = c.js("""
      (() => { const f=document.querySelector('figure.diagram'); const d=f.style.display;
        f.style.display='none'; const t=document.body.innerText;
        f.style.display=d; return %s.filter(l => t.indexOf(l) === -1); })()
    """ % json.dumps(LABELS))
    R.check("SC-002", "with the drawing hidden, the prose still names every node",
            missing == [], missing)

    # ---------- FR-026 no motion ----------
    motion = c.js("""
      (() => [...document.querySelectorAll('.fc-shape, .fc-edge, .fc-link, .node, .node > summary, .diagram')]
        .filter(e => { const cs=getComputedStyle(e);
          return cs.transitionDuration !== '0s' || cs.animationName !== 'none'; })
        .map(e => e.tagName + '.' + (e.className.baseVal || e.className)))()
    """)
    R.check("FR-026", "the artifact introduces no motion of its own", motion == [], motion)

    # ---------- tab order + focus indicators ----------
    c.js("location.reload()")
    c.pump(2.5)
    c.js("window.scrollTo(0,0)")
    stops = []
    for _ in range(20):
        c.tab()
        cur = c.js("""
          (() => { const a=document.activeElement; if(!a||a===document.body) return null;
            const cs=getComputedStyle(a);
            return {tag:a.tagName, cls:(a.className.baseVal||a.className||'').toString().slice(0,28),
                    id:a.id||null,
                    ind: (cs.outlineStyle!=='none' && parseFloat(cs.outlineWidth)>0) ? 'outline'
                         : (cs.boxShadow!=='none' ? 'boxShadow' : 'NONE')}; })()
        """)
        if cur is None:
            break
        if stops and cur == stops[0]:
            break
        stops.append(cur)
    # SVG elements keep their authored case, so an SVG link reports tagName 'a'
    # rather than the HTML 'A'. Normalise before comparing.
    kinds = [s["tag"].upper() for s in stops]
    R.eq("COINED-TAB-ORDER", "sixteen stops: toggle, drawing, 7 nodes, 7 summaries",
         len(stops), 16)
    R.eq("COINED-TAB-ORDER", "stop order by element kind", kinds,
         ["BUTTON", "FIGURE"] + ["A"] * 7 + ["SUMMARY"] * 7)
    noind = [s for s in stops if s["ind"] == "NONE"]
    R.check("FR-037", "every stop shows a visible focus indicator", noind == [],
            json.dumps(noind, indent=1))
    sw = c.js("""
      (() => { const a=document.querySelector('a.fc-link'); a.focus();
        return getComputedStyle(a.querySelector('.fc-shape')).strokeWidth; })()
    """)
    R.check("FR-037", "a focused node also thickens its stroke (second carrier)",
            sw not in (None, "", "0"), "strokeWidth=%s" % sw)
    R.eq("SC-004", "keyboard alone reaches all seven nodes",
         sum(1 for s in stops if s["tag"].upper() == "A"), 7)

    # ---------- FR-025 no horizontal page scroll / scroll container ----------
    widths = {}
    for w in (320, 480, 768, 1280):
        c.call("Emulation.setDeviceMetricsOverride",
               {"width": w, "height": 900, "deviceScaleFactor": 1, "mobile": False})
        time.sleep(0.35)
        widths[w] = c.js("""
          (() => ({page: document.scrollingElement.scrollWidth <= window.innerWidth + 1,
                   fig: (() => { const f=document.querySelector('figure.diagram');
                          return {scrollable: f.scrollWidth > f.clientWidth,
                                  tabindex: f.getAttribute('tabindex')}; })()}))()
        """)
    R.check("FR-025", "page never scrolls horizontally at 320/480/768/1280",
            all(v["page"] for v in widths.values()), json.dumps(widths, indent=1))
    R.eq("COINED-SCROLL-KEYBOARD", "the drawing's scroll container is keyboard-focusable",
         widths[480]["fig"]["tabindex"], "0")
    c.call("Emulation.setDeviceMetricsOverride",
           {"width": 480, "height": 900, "deviceScaleFactor": 1, "mobile": False})
    time.sleep(0.3)
    scrolled = c.js("""
      (() => { const f=document.querySelector('figure.diagram'); f.focus(); f.scrollLeft=0;
               return {focused: document.activeElement === f, before: f.scrollLeft}; })()
    """)
    c.key("ArrowRight", "ArrowRight", 39, repeat=6)
    time.sleep(0.3)
    after = c.js("document.querySelector('figure.diagram').scrollLeft")
    R.check("COINED-SCROLL-KEYBOARD", "arrow keys scroll the focused container",
            scrolled["focused"] and after > 0, {"before": scrolled, "after": after})
    c.call("Emulation.setDeviceMetricsOverride",
           {"width": 1280, "height": 900, "deviceScaleFactor": 2, "mobile": False})

    # ---------- FR-002 themes ----------
    c.js("location.reload()")
    c.pump(2.0)
    light_bg = c.js("getComputedStyle(document.body).backgroundColor")
    c.click_ref("button.rc-theme-toggle")
    time.sleep(0.5)
    dark = c.js("""(() => ({theme: document.documentElement.getAttribute('data-theme'),
                            bg: getComputedStyle(document.body).backgroundColor,
                            pressed: document.querySelector('.rc-theme-toggle').getAttribute('aria-pressed')}))()""")
    R.check("FR-002", "the toggle flips the theme and tracks aria-pressed",
            dark["theme"] == "dark" and dark["bg"] != light_bg and dark["pressed"] == "true", dark)
    c.screenshot(os.path.join(SHOTS, "s3-03-dark.png"), full=True)
    c.click_ref("button.rc-theme-toggle")
    time.sleep(0.4)

    # ---------- FR-047 offline ----------
    # A fresh browser, because this instance already fetched the webfont while
    # online and would serve it from cache — which would fake the pass.
    off_c = Chrome()
    try:
        off_c.enable_all()
        off_c.offline(True)
        off_c.clear_events()
        off_c.navigate(URL, settle=3.0)
        off = off_c.console_report()
        R.check("FR-047", "offline: only the webfont request fails, nothing else",
                all("fonts.googleapis.com" in (m.get("url") or "") for m in off),
                json.dumps(off, indent=1))
        loaded = off_c.js("[...document.fonts].filter(f => f.status === 'loaded').map(f => f.family)")
        R.check("FR-047", "offline: no webfont is applied", loaded == [], loaded)
        R.eq("FR-047", "offline: the whole drawing still renders",
             off_c.js("document.querySelectorAll('a.fc-link').length"), 7)
        R.check("FR-047", "offline: disclosure still operates",
                off_c.js("""(() => { const d=document.getElementById('nodes-merge-the-draft');
                         d.open=true; const ok=d.open; d.open=false; return ok; })()"""), "")
        off_c.screenshot(os.path.join(SHOTS, "s3-04-offline.png"), full=True)
    finally:
        off_c.close()

    # ---------- FR-048 storage refused ----------
    c.call("Page.addScriptToEvaluateOnNewDocument", {"source": """
      Object.defineProperty(window, 'localStorage', {
        configurable: true,
        get() { return { getItem() { throw new Error('storage refused'); },
                         setItem() { throw new Error('storage refused'); },
                         removeItem() { throw new Error('storage refused'); } }; }
      });
    """})
    c.clear_events()
    c.js("location.reload()")
    c.pump(3.0)
    st_console = [m for m in c.console_report() if m["kind"] in ("exception",)
                  or (m["kind"].startswith("log.") and m.get("source") != "network")]
    R.check("FR-048", "storage refused: no uncaught exception reaches the console",
            st_console == [], json.dumps(st_console, indent=1))
    R.check("FR-048", "storage refused: the page still renders in full",
            c.js("document.querySelectorAll('a.fc-link').length") == 7, "")
    have_toggle = c.js("!!document.querySelector('button.rc-theme-toggle')")
    if have_toggle:
        c.click_ref("button.rc-theme-toggle")
        time.sleep(0.4)
        t1 = c.js("document.documentElement.getAttribute('data-theme')")
        c.click_ref("button.rc-theme-toggle")
        time.sleep(0.4)
        t2 = c.js("document.documentElement.getAttribute('data-theme')")
        R.check("FR-048", "storage refused: the theme control still flips both ways",
                t1 != t2, {"after1": t1, "after2": t2})
    else:
        R.check("FR-048", "storage refused: the theme control still flips both ways", False,
                "theme toggle absent")

    # ---------- SC-006 scripting disabled ----------
    c.call("Emulation.setScriptExecutionDisabled", {"value": True})
    c.clear_events()
    c.call("Page.navigate", {"url": URL})
    c.pump(2.5)
    ns = c.call("Runtime.evaluate", {"expression": "1", "returnByValue": True})
    nos = c.call("DOM.getDocument", {"depth": -1})
    html = c.call("DOM.getOuterHTML", {"nodeId": nos["root"]["nodeId"]})["outerHTML"]
    R.check("SC-006", "scripting disabled: no dead control is offered (no button/input)",
            "<button" not in html and "<input" not in html and "<form" not in html,
            "button=%s input=%s" % ("<button" in html, "<input" in html))
    R.check("SC-006", "scripting disabled: all seven nodes and their prose still render",
            html.count("fc-link") >= 7 and "narration" in html, "")
    R.check("SC-006", "scripting disabled: one node still open by markup alone",
            html.count("<details") == 7 and " open" in html, "")
    c.call("Emulation.setScriptExecutionDisabled", {"value": False})

finally:
    p, t = R.summary()
    R.dump(os.path.join(os.path.dirname(os.path.abspath(__file__)), "slice3-results.json"))
    c.close()
    sys.exit(0 if p == t else 1)
