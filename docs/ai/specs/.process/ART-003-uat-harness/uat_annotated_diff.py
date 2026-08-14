"""ART-003 slice 2 (#436) manual UAT — annotated-diff.html on a real file:// URL.

Each stage runs in its own browser. That keeps one stage's emulation state
(vision deficiency, media features, disabled scripting) from leaking into the
next, and stops a single hung call from taking the whole run down.
"""

import json
import os
import sys
import tempfile
import time
import traceback

from cdp import Chrome, Report, is_brand_font_request

# The run this evidence records was performed in a feature worktree that no longer
# exists. Resolve the repository root from this file instead, so the harness runs
# from any clone. ART003_ROOT points it at a different checkout; UAT_URL replaces
# the whole path.
ROOT = os.environ.get("ART003_ROOT") or os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), *[os.pardir] * 5))
URL = os.environ.get("UAT_URL") or ("file://" + ROOT + "/speckit-pro/artifact-gallery/templates/annotated-diff.html")
# Screenshots land outside the tree by default: a run must not leave untracked
# files in the repository.
SHOTS = os.environ.get("ART003_SHOTS") or os.path.join(tempfile.gettempdir(), "art003-uat-shots")
os.makedirs(SHOTS, exist_ok=True)

R = Report("slice2 / annotated-diff")
H1 = "hunks-packages-editor-src-draft-queue-ts-l18"
H2 = "hunks-config-editor-json-l12"
TA1 = H1 + "-objection"
TA2 = H2 + "-objection"
OBJ = "The guard should skip the edit, not the flush."

RECORDER = """
window.__clip = [];
(() => { if (!navigator.clipboard) return;
  const real = navigator.clipboard.writeText.bind(navigator.clipboard);
  navigator.clipboard.writeText = function (t) { window.__clip.push(t); return real(t); }; })();
"""

STAGES = []


def stage(fn):
    STAGES.append(fn)
    return fn


def open_page(offline=False, clipboard=False, settle=3.0):
    c = Chrome()
    c.enable_all()
    if clipboard:
        c.grant(["clipboardReadWrite", "clipboardSanitizedWrite"])
        c.call("Emulation.setFocusEmulationEnabled", {"enabled": True})
        c.call("Page.bringToFront")
    if offline:
        c.offline(True)
    c.clear_events()
    c.navigate(URL, settle=settle)
    return c


def set_field(c, tid, value):
    c.js("""(() => { const t=document.getElementById(%s); t.value=%s;
            t.dispatchEvent(new Event('input',{bubbles:true})); })()"""
         % (json.dumps(tid), json.dumps(value)))


# --------------------------------------------------------------- stage 1
@stage
def s1_load_and_render():
    c = open_page(offline=True, clipboard=True, settle=3.5)
    try:
        console = c.console_report()
        non_font = [m for m in console if not is_brand_font_request(m.get("url"))]
        R.check("SC-001", "console silent on load apart from the shared webfont request",
                non_font == [], json.dumps(non_font, indent=1))
        R.check("SC-001", "the only outbound request is the shared webfont",
                [r for r in c.requests() if not r["url"].startswith("file:")
                 and not is_brand_font_request(r["url"])] == [], "")

        ids = ["artifact-title", "feature-id", "feature-name", H1, H2, "export",
               "copy-prompt", "copy-markdown", "export-status", "fallback", "fallback-field"]
        R.check("SC-002", "every pinned id resolves while offline",
                c.js("%s.filter(i => !document.getElementById(i))" % json.dumps(ids)) == [], "")

        r = c.js("""
          (() => ({title: document.getElementById('artifact-title').textContent.trim(),
            hunks: document.querySelectorAll('.hunk').length,
            rows: document.querySelectorAll('.diff-row').length,
            anns: document.querySelectorAll('.ann').length,
            sevs: [...document.querySelectorAll('.sev')].map(s => s.textContent.trim()),
            buttons: [...document.querySelectorAll('#export button')].map(b => b.textContent.trim())}))()
        """)
        R.eq("US1-AS6", "rendered title matches the catalog entry byte for byte",
             r["title"], "Annotated Diff")
        R.eq("RENDER", "document title", c.js("document.title"),
             "Annotated Diff — NIMBUS-101 Offline Draft Sync")
        R.eq("RENDER", "two hunks", r["hunks"], 2)
        R.eq("RENDER", "thirteen diff rows", r["rows"], 13)
        R.eq("RENDER", "three annotations", r["anns"], 3)
        R.eq("RENDER", "two severities, stated as words", r["sevs"],
             ["Severity: blocking", "Severity: minor"])
        R.eq("RENDER", "export buttons named by destination", r["buttons"],
             ["Copy as prompt", "Copy as Markdown"])
        R.check("RENDER", "no webfont applied while offline",
                c.js("[...document.fonts].filter(f=>f.status==='loaded').length") == 0, "")
        c.screenshot(os.path.join(SHOTS, "s2-01-light-full.png"), full=True)

        marks = c.js("""
          (() => [...document.querySelectorAll('#%s .diff-row')].slice(0,3).map(r => ({
              mk: r.querySelector('.mk').textContent,
              before: getComputedStyle(r.querySelector('.mk'), '::before').content,
              after: getComputedStyle(r.querySelector('.mk'), '::after').content,
              lnSelect: getComputedStyle(r.querySelector('.ln')).webkitUserSelect})))()
        """ % H1)
        R.eq("FR-019c", "row state is literal text in the document",
             [m["mk"] for m in marks], [" ", "-", "+"])
        R.check("FR-019c", "no marker comes from CSS generated content",
                all(m["before"] == "none" and m["after"] == "none" for m in marks), marks)
        R.check("FR-019c", "the line-number cell alone is unselectable",
                all(m["lnSelect"] == "none" for m in marks), marks)

        # ---- the actual paste, not an assertion ----
        def copy_row(i):
            c.js("""(() => { const r=document.createRange();
              r.selectNodeContents(document.querySelectorAll('#%s .diff-row')[%d]);
              const s=getSelection(); s.removeAllRanges(); s.addRange(r); })()""" % (H1, i))
            c.js("document.execCommand('copy')")
            return c.js("(async () => await navigator.clipboard.readText())()", await_promise=True)

        pasted = [copy_row(i) for i in (0, 1, 2)]
        R.check("PASTE", "a pasted row never carries the line number",
                not any(t.strip().startswith(("18", "19", "20")) for t in pasted),
                json.dumps(pasted))
        R.eq("PASTE", "a context row pastes as one valid unified-diff line",
             pasted[0], " async function flush() {")
        R.eq("PASTE", "a removed row pastes as one valid unified-diff line",
             pasted[1], "-  for (const edit of queue) {")
        R.eq("PASTE", "an added row pastes as one valid unified-diff line",
             pasted[2], "+  for (const edit of queue.inOrder()) {")
        c.js("""(() => { const rs=document.querySelectorAll('#%s .diff-row');
          const r=document.createRange(); r.setStartBefore(rs[0]); r.setEndAfter(rs[2]);
          const s=getSelection(); s.removeAllRanges(); s.addRange(r); })()""" % H1)
        c.js("document.execCommand('copy')")
        multi = c.js("(async () => await navigator.clipboard.readText())()", await_promise=True)
        R.eq("PASTE", "three consecutive rows paste as three lines",
             len([l for l in multi.split("\n") if l.strip() != ""]), 3)
        c.js("getSelection().removeAllRanges()")

        mono = c.js("""
          (() => { const rows=[...document.querySelectorAll('#%s .diff-row')];
            return {bg:[...new Set(rows.map(r=>getComputedStyle(r).backgroundColor))],
                    fg:[...new Set(rows.map(r=>getComputedStyle(r).color))]}; })()
        """ % H1)
        R.eq("SC-006", "added/removed/context rows share one background (no hue carrier)",
             len(mono["bg"]), 1)
        R.eq("SC-006", "added/removed/context rows share one text colour", len(mono["fg"]), 1)
        R.check("FR-019f", "severity is one style rule with no branch on the word",
                c.js("""(() => { const s=[...document.querySelectorAll('.sev')];
                  const k=['color','backgroundColor','fontWeight','fontFamily','fontSize',
                           'letterSpacing','textTransform','borderTopColor','borderTopWidth'];
                  const a=getComputedStyle(s[0]), b=getComputedStyle(s[1]);
                  return k.filter(x => a[x] !== b[x]); })()""") == [], "")
        nosev = c.js("""
          (() => { const anns=[...document.querySelectorAll('.ann')];
            const k=['backgroundColor','borderLeftColor','borderLeftWidth','color','paddingLeft'];
            const a=getComputedStyle(anns[2]), b=getComputedStyle(anns[0]);
            return {sevCount: anns[2].querySelectorAll('.sev').length,
                    diffs: k.filter(x => a[x] !== b[x])}; })()
        """)
        R.eq("US1-AS6", "an annotation with no severity carries no severity element",
             nosev["sevCount"], 0)
        R.check("US1-AS6", "absence of severity renders as no rank, not a fourth level",
                nosev["diffs"] == [], nosev)
        clean = c.js("""
          (() => { const h=document.getElementById('%s');
            const k=['backgroundColor','borderTopColor','borderTopWidth','borderRadius','padding'];
            const a=getComputedStyle(h), b=getComputedStyle(document.getElementById('%s'));
            return {anns: h.querySelectorAll('.ann').length,
                    note: (h.querySelector('p.note')||{}).textContent || '',
                    diffs: k.filter(x => a[x] !== b[x])}; })()
        """ % (H2, H1))
        R.eq("FR-020b", "the clean hunk carries no annotation", clean["anns"], 0)
        R.eq("FR-020b", "the clean hunk says so in words", " ".join(clean["note"].split()),
             "This hunk was read and carries no annotation. Nothing needed saying about it, "
             "which is a finished state rather than an unfinished one.")
        R.check("FR-020b", "no style distinguishes the clean hunk", clean["diffs"] == [], clean)
        c.vision("achromatopsia")
        time.sleep(0.4)
        c.screenshot(os.path.join(SHOTS, "s2-02-achromatopsia.png"), full=True)
    finally:
        c.close()


# --------------------------------------------------------------- stage 2
@stage
def s2_layout_and_keyboard():
    c = open_page()
    try:
        cont = c.js("""
          (() => [...document.querySelectorAll('.diff')].map(d => ({
            tabindex: d.getAttribute('tabindex'), role: d.getAttribute('role'),
            label: d.getAttribute('aria-label'),
            headingOutside: !!d.previousElementSibling && /^H[1-6]$/.test(d.previousElementSibling.tagName)})))()
        """)
        R.check("FR-019d", "both scroll containers are focusable, grouped and named",
                all(d["tabindex"] == "0" and d["role"] == "group" and d["label"] for d in cont), cont)
        R.check("FR-019d", "the hunk heading sits outside the scroll container",
                all(d["headingOutside"] for d in cont), cont)

        c.viewport(420)
        time.sleep(0.5)
        probe = c.js("""
          (() => { const d=document.querySelector('.diff'); d.focus(); d.scrollLeft=0;
            return {overflows: d.scrollWidth > d.clientWidth, focused: document.activeElement===d}; })()
        """)
        c.key("ArrowRight", "ArrowRight", 39, repeat=8)
        time.sleep(0.4)
        after = c.js("document.querySelector('.diff').scrollLeft")
        R.check("FR-019d", "the focused container scrolls from the keyboard",
                probe["overflows"] and probe["focused"] and after > 0,
                {"probe": probe, "scrollLeft": after})

        widths = {}
        for w in (320, 375, 768, 1280):
            c.viewport(w)
            time.sleep(0.4)
            widths[w] = c.js("document.scrollingElement.scrollWidth <= window.innerWidth + 1")
        R.check("FR-035", "the page never scrolls horizontally at 320/375/768/1280",
                all(widths.values()), widths)
    finally:
        c.close()


# --------------------------------------------------------------- stage 3
@stage
def s3_jump_links_and_tab_order():
    c = open_page()
    try:
        c.js("""document.querySelector('a[href="#finding-inorder-allocation"]').focus()""")
        c.key("Enter", "Enter", 13)
        time.sleep(0.6)
        R.eq("FR-034", "a jump link moves focus, not only scroll position",
             c.js("""(() => [location.hash, document.activeElement.id])()"""),
             ["#finding-inorder-allocation", "finding-inorder-allocation"])
        c.js("""document.querySelector('a[href="#finding-flush-guard"]').focus()""")
        c.key("Enter", "Enter", 13)
        time.sleep(0.6)
        R.eq("FR-034", "the reverse jump link moves focus too",
             c.js("document.activeElement.id"), "finding-flush-guard")

        # Navigate clean rather than reload: the jump-link checks above left a
        # fragment in the URL, and reloading with it would seat the sequential
        # focus navigation starting point at the fragment's target, so the
        # traversal would begin mid-document.
        c.call("Page.navigate", {"url": URL})
        c.pump(2.5)
        c.js("window.scrollTo(0,0)")
        stops = []
        for _ in range(16):
            c.tab()
            cur = c.js("""
              (() => { const a=document.activeElement; if(!a||a===document.body) return null;
                const cs=getComputedStyle(a);
                return {tag:a.tagName, id:a.id||null,
                        txt:(a.getAttribute('aria-label')||a.textContent||'').trim().slice(0,44),
                        ind:(cs.outlineStyle!=='none'&&parseFloat(cs.outlineWidth)>0)?'outline'
                            :(cs.boxShadow!=='none'?'boxShadow':'NONE')}; })()
            """)
            if cur is None or (stops and cur == stops[0]):
                break
            stops.append(cur)
        R.eq("FR-036", "nine tab stops with both disclosures closed", len(stops), 9)
        R.check("FR-036", "every stop shows a visible focus indicator",
                [s for s in stops if s["ind"] == "NONE"] == [],
                json.dumps([s for s in stops if s["ind"] == "NONE"], indent=1))
        R.check("FR-036", "no positive tabindex anywhere",
                c.js("[...document.querySelectorAll('[tabindex]')]"
                     ".every(e => +e.getAttribute('tabindex') <= 0)"),
                c.js("[...document.querySelectorAll('[tabindex]')].map(e=>e.getAttribute('tabindex'))"))
        R.check("FR-036", "the two export buttons are the last two stops",
                [s["txt"] for s in stops[-2:]] == ["Copy as prompt", "Copy as Markdown"],
                [s["txt"] for s in stops])
    finally:
        c.close()


# --------------------------------------------------------------- stage 4
@stage
def s4_disclosure_and_exports():
    c = open_page(clipboard=True)
    try:
        c.js(RECORDER)
        R.eq("FR-021a", "an unfilled objection control states so in text",
             c.js("""(() => document.getElementById(%s).closest('details')
                     .querySelector('summary').textContent.trim())()""" % json.dumps(TA1)),
             "Objection on packages/editor/src/draft-queue.ts lines 18-23: no note recorded")
        R.check("FR-021b", "the disclosure carries no ARIA role or state",
                c.js("""[...document.querySelectorAll('details.objection > summary')]
                     .every(s => !s.hasAttribute('role') && !s.hasAttribute('aria-expanded')
                                 && !s.hasAttribute('aria-pressed'))"""), "")

        c.js("""(() => document.getElementById(%s).closest('details')
                .querySelector('summary').focus())()""" % json.dumps(TA1))
        c.key("Enter", "Enter", 13)
        time.sleep(0.35)
        R.check("US2-AS1", "the objection disclosure opens from the keyboard",
                c.js("document.getElementById(%s).closest('details').open" % json.dumps(TA1)), "")
        c.tab()
        R.eq("US2-AS1", "Tab lands in the objection field", c.js("document.activeElement.id"), TA1)
        c.type_text("T")
        R.eq("FR-021a", "the control's text state recomputes on a single keystroke",
             c.js("""(() => document.getElementById(%s).closest('details')
                     .querySelector('summary').textContent.trim())()""" % json.dumps(TA1)),
             "Objection on packages/editor/src/draft-queue.ts lines 18-23: note recorded")

        set_field(c, TA1, OBJ)
        set_field(c, TA2, "")
        c.js("window.__clip=[]")
        c.click_ref("#copy-prompt")
        time.sleep(0.9)
        prompt_txt = c.js("window.__clip.slice(-1)[0] || ''")
        R.eq("COPY-SUCCESS", "a successful copy is confirmed in words, with a count",
             c.js("document.getElementById('export-status').textContent.trim()"),
             "Copied. 1 objection is on the clipboard.")
        R.check("SC-004", "the export carries exactly the one objection recorded",
                prompt_txt.count(OBJ) == 1 and "config/editor.json" not in prompt_txt, prompt_txt)
        R.check("SC-004", "the export names the artifact and the feature",
                prompt_txt.startswith("Artifact: Annotated Diff\n"
                                      "Feature: NIMBUS-101 Offline Draft Sync"),
                prompt_txt[:130])

        c.js("window.__clip=[]")
        c.click_ref("#copy-markdown")
        time.sleep(0.9)
        md_txt = c.js("window.__clip.slice(-1)[0] || ''")
        diffs = [(a, b) for a, b in zip(prompt_txt.split("\n"), md_txt.split("\n")) if a != b]
        R.eq("FR-023a", "the markdown export differs in exactly one line", len(diffs), 1)
        R.check("FR-023a", "no markdown syntax is emitted",
                not any(t in md_txt for t in ["**", "`", "# ", "- "]), md_txt)

        set_field(c, TA1, "second text")
        c.js("window.__clip=[]")
        c.click_ref("#copy-prompt")
        time.sleep(0.9)
        R.check("FR-026", "an export is derived from live state at the moment of invocation",
                "second text" in c.js("window.__clip.slice(-1)[0] || ''"), "")

        set_field(c, TA1, "   ")
        set_field(c, TA2, "   ")
        c.js("window.__clip=[]")
        c.click_ref("#copy-prompt")
        time.sleep(0.9)
        empty_txt = c.js("window.__clip.slice(-1)[0] || ''")
        R.check("FR-030", "whitespace-only counts as empty, and the export denies approval",
                "No objection was recorded." in empty_txt and "approval" in empty_txt.lower(),
                empty_txt)
    finally:
        c.close()


# --------------------------------------------------------------- stage 5
@stage
def s5_clipboard_refusal():
    modes = {
        "rejected promise": "navigator.clipboard.writeText = () => Promise.reject(new Error('x'));",
        "synchronous throw": "navigator.clipboard.writeText = () => { throw new Error('x'); };",
        # `delete navigator.clipboard` is a no-op: clipboard is an accessor on
        # Navigator.prototype, not an own property, so the delete silently
        # succeeds and leaves the real clipboard in place.
        "clipboard absent":
            "Object.defineProperty(navigator,'clipboard',{value:undefined,configurable:true});",
    }
    statuses, states = [], []
    for name, patch in modes.items():
        c = open_page(clipboard=True, settle=2.5)
        try:
            set_field(c, TA1, OBJ)
            c.js(patch)
            c.click_ref("#copy-prompt")
            time.sleep(1.4)
            statuses.append(c.js("document.getElementById('export-status').textContent.trim()"))
            states.append({"mode": name, **c.js("""
              (() => ({revealed: !document.getElementById('fallback').hasAttribute('hidden'),
                       focused: document.activeElement.id === 'fallback-field',
                       filled: document.getElementById('fallback-field').value.indexOf(%s) >= 0}))()
            """ % json.dumps(OBJ))})
            if name == "rejected promise":
                c.screenshot(os.path.join(SHOTS, "s2-03-fallback.png"))
        finally:
            c.close()
    R.eq("FR-030b", "all three refusal modes produce exactly one distinct message",
         len(set(statuses)), 1)
    R.check("SC-005", "the refusal message never claims success",
            all("Copied" not in s for s in statuses), statuses)
    R.check("FR-030b", "no message names the local-file scheme or guesses a cause",
            all("file:" not in s for s in statuses), statuses)
    R.check("SC-005", "every refusal reveals the text, fills it, and moves focus to it",
            all(s["revealed"] and s["focused"] and s["filled"] for s in states),
            json.dumps(states, indent=1))


# --------------------------------------------------------------- stage 6
@stage
def s6_race_both_directions():
    def race(first_fails):
        c = open_page(clipboard=True, settle=2.5)
        try:
            set_field(c, TA1, OBJ)
            c.js("""
              window.__seen = [];
              new MutationObserver(() => window.__seen.push(
                document.getElementById('export-status').textContent.trim()))
                .observe(document.getElementById('export-status'),
                         {childList:true, subtree:true, characterData:true});
              window.__n = 0;
              navigator.clipboard.writeText = function () {
                window.__n += 1; const first = (window.__n === 1);
                return new Promise((res, rej) => setTimeout(
                  () => { (first === %s) ? rej(new Error('slow')) : res(); }, first ? 700 : 0)); };
            """ % ("true" if first_fails else "false"))
            c.click_ref("#copy-prompt")
            time.sleep(0.15)
            c.click_ref("#copy-markdown")
            time.sleep(2.6)
            return c.js("""(() => ({status: document.getElementById('export-status').textContent.trim(),
                     hidden: document.getElementById('fallback').hasAttribute('hidden'),
                     focus: document.activeElement.id, seen: window.__seen}))()""")
        finally:
            c.close()

    a = race(first_fails=True)
    R.check("SC-007", "a superseded slow FAILURE never overwrites the later success",
            "Copied" in a["status"] and a["hidden"] and a["focus"] != "fallback-field", a)
    R.check("SC-007", "the superseded failure never reveals the fallback or steals focus",
            a["hidden"] and a["focus"] != "fallback-field", a)
    # Mirror: the LATER invocation fails fast, the earlier one succeeds slowly.
    # The correct outcome is the later one — failure — and the slow success that
    # lands afterwards must not flip it to "Copied".
    b = race(first_fails=False)
    R.check("FR-027", "the mirror race reports the later invocation's failure",
            b["status"].startswith("Copy failed."), b)
    R.check("FR-027", "a superseded slow SUCCESS never overwrites that failure",
            "Copied" not in b["status"] and b["seen"].count("Copied. 1 objection is on the clipboard.") == 0,
            b)


# --------------------------------------------------------------- stage 7
@stage
def s7_theme_and_motion():
    c = open_page()
    try:
        light = c.js("getComputedStyle(document.body).backgroundColor")
        c.click_ref("button.rc-theme-toggle")
        time.sleep(0.6)
        dark = c.js("""(() => ({theme: document.documentElement.getAttribute('data-theme'),
                                bg: getComputedStyle(document.body).backgroundColor}))()""")
        R.check("US1-AS8", "the theme control flips both themes",
                dark["theme"] == "dark" and dark["bg"] != light, {"light": light, **dark})
        c.screenshot(os.path.join(SHOTS, "s2-04-dark-full.png"), full=True)
        fails = c.js("""
          (() => { const lum=(cc)=>{const [r,g,b]=cc.match(/\\d+(\\.\\d+)?/g).slice(0,3).map(Number)
              .map(v=>{v/=255; return v<=0.03928? v/12.92 : Math.pow((v+0.055)/1.055,2.4);});
              return 0.2126*r+0.7152*g+0.0722*b;};
            const bgOf=(el)=>{let n=el; while(n){const b=getComputedStyle(n).backgroundColor;
              if(b && !/rgba\\(0, 0, 0, 0\\)|transparent/.test(b)) return b; n=n.parentElement;}
              return getComputedStyle(document.body).backgroundColor;};
            const out=[];
            document.querySelectorAll('h1,h2,h3,p,li,summary,button,label,code,.sev').forEach(el=>{
              if(!el.textContent.trim()) return;
              const r=el.getBoundingClientRect(); if(!r.width||!r.height) return;
              const cs=getComputedStyle(el); if(cs.visibility==='hidden'||cs.display==='none') return;
              const f=lum(cs.color), b=lum(bgOf(el));
              const hi=Math.max(f,b), lo=Math.min(f,b); const ratio=(hi+0.05)/(lo+0.05);
              const px=parseFloat(cs.fontSize);
              const need=(px>=24||(px>=18.66&&parseInt(cs.fontWeight,10)>=700))?3.0:4.5;
              if(ratio<need) out.push({tag:el.tagName, txt:el.textContent.trim().slice(0,34),
                                       ratio:+ratio.toFixed(2), need});
            });
            return out; })()
        """)
        R.check("US1-AS8", "dark theme: every text node meets WCAG AA contrast",
                fails == [], json.dumps(fails[:8], indent=1))

        c.call("Emulation.setEmulatedMedia",
               {"features": [{"name": "prefers-reduced-motion", "value": "reduce"}]})
        c.js("location.reload()")
        c.pump(2.2)
        # The kit answers a reduced-motion preference by collapsing durations to
        # 1e-05s rather than 0s, so "no motion" means effectively instantaneous,
        # not literally zero.
        R.check("FR-037", "reduced motion is honoured: the preference is seen",
                c.js("matchMedia('(prefers-reduced-motion: reduce)').matches"), "")
        R.eq("FR-037", "nothing animates perceptibly under reduced motion",
             c.js("""
               (() => [...document.querySelectorAll('.hunk,.diff,.diff-row,.ann,.sev,details.objection,summary')]
                 .filter(e => { const cs=getComputedStyle(e);
                   return cs.animationName !== 'none'
                          || parseFloat(cs.transitionDuration) > 0.02; }).length)()
             """), 0)
    finally:
        c.close()


# --------------------------------------------------------------- stage 8
@stage
def s8_scripting_disabled():
    c = Chrome()
    try:
        c.enable_all()
        c.call("Emulation.setScriptExecutionDisabled", {"value": True})
        c.clear_events()
        c.call("Page.navigate", {"url": URL})
        c.pump(2.5)
        doc = c.call("DOM.getDocument", {"depth": -1})
        html = c.call("DOM.getOuterHTML", {"nodeId": doc["root"]["nodeId"]})["outerHTML"]
        R.eq("FR-043", "scripting disabled: no objection control is mounted",
             html.count("details class=\"objection\"") + html.count("class=\"objection\""), 0)
        # Search the body with <style> stripped: the class name also appears in
        # the stylesheet, where it proves nothing about a rendered control.
        import re as _re
        body = html.split("<body", 1)[1] if "<body" in html else html
        body = _re.sub(r"<style.*?</style>", "", body, flags=_re.S)
        R.check("FR-043", "scripting disabled: no theme control is offered",
                "rc-theme-toggle" not in body, "")
        R.check("FR-043", "scripting disabled: the diff and its findings still render",
                html.count("diff-row") >= 13 and "finding-flush-guard" in html
                and "Severity: blocking" in html, "")
        seg = html.split('id="export"')[1][:80] if 'id="export"' in html else ""
        R.check("FR-043", "scripting disabled: the export panel is hidden, not dead",
                "hidden" in seg, seg or "no #export element")
    finally:
        c.close()


failed_stages = []
for fn in STAGES:
    try:
        fn()
    except Exception:
        failed_stages.append(fn.__name__)
        print("\n!! stage %s raised:" % fn.__name__)
        traceback.print_exc()

p, t = R.summary()
if failed_stages:
    print("stages that raised: %s" % ", ".join(failed_stages))
R.dump(os.path.join(os.path.dirname(os.path.abspath(__file__)), "slice2-results.json"))
sys.exit(0 if p == t and not failed_stages else 1)
