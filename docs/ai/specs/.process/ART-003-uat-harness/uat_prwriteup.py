"""ART-003 slice 1 (#435) manual UAT — executes ART-003-uat-runbook.md Steps 1-12
against real Chrome on a real file:// URL, network emulated offline.
"""

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
URL = os.environ.get("UAT_URL") or ("file://" + ROOT + "/speckit-pro/artifact-gallery/templates/pr-writeup.html")
# Screenshots land outside the tree by default: a run must not leave untracked
# files in the repository.
SHOTS = os.environ.get("ART003_SHOTS") or os.path.join(tempfile.gettempdir(), "art003-uat-shots")
os.makedirs(SHOTS, exist_ok=True)

R = Report("slice1 / pr-writeup")

RECORDER = """
window.__clip = [];
(() => {
  const real = navigator.clipboard.writeText.bind(navigator.clipboard);
  navigator.clipboard.writeText = function (t) { window.__clip.push(t); return real(t); };
})();
"""

EXPECT_HEADINGS = [
    "Why this change was made",
    "How it behaved, and how it behaves now",
    "What each changed file does",
    "What this change deliberately leaves out",
    "How it was checked",
    "What happened while it was built",
]

c = Chrome()
try:
    c.enable_all()
    c.offline(True)          # Setup step 2 — offline BEFORE the file is opened
    c.clear_events()         # Setup step 1 — console open first

    # ---------------- Step 1 : load + console ----------------
    c.navigate(URL, settle=3.5)
    # Runbook Step 1, as corrected: offline, exactly one line is expected and it
    # is the shared header's font request. Anything else is still a finding.
    console = c.console_report()
    R.eq("1", "console carries exactly one line offline", len(console), 1)
    R.check("1", "that one line is the shared header's font request, nothing else",
            len(console) == 1
            and "fonts.googleapis.com" in (console[0].get("url") or "")
            and "ERR_INTERNET_DISCONNECTED" in (console[0].get("text") or ""),
            json.dumps(console, indent=2))
    R.check("1", "the page itself adds no console message",
            [m for m in console if "fonts.googleapis.com" not in (m.get("url") or "")] == [],
            json.dumps(console, indent=2))
    # The corrected step also promises silence once the network is back. Fresh
    # browser, because this one has already failed the font fetch.
    on_c = Chrome()
    try:
        on_c.enable_all()
        on_c.clear_events()
        on_c.navigate(URL, settle=3.5)
        on_console = on_c.console_report()
        R.check("1", "with the network back, the console is completely silent",
                on_console == [], json.dumps(on_console, indent=2))
    finally:
        on_c.close()
    R.eq("1", "tab title", c.js("document.title"),
         "Pull Request Write-up — NIMBUS-101 Offline Draft Sync")
    R.eq("1", "eyebrow artifact title", c.js("document.getElementById('artifact-title').textContent.trim()"),
         "Pull Request Write-up")
    R.eq("1", "feature id", c.js("document.getElementById('feature-id').textContent.trim()"), "NIMBUS-101")
    R.eq("1", "page heading", c.js("document.querySelector('h1').textContent.trim()"), "Offline Draft Sync")

    heads = c.js("[...document.querySelectorAll('section h2')].map(h=>h.textContent.trim())")
    R.eq("1", "six sections in runbook order", heads[:6], EXPECT_HEADINGS)

    empties = c.js("""
      [...document.querySelectorAll('section')].filter(s => s.textContent.trim().length < 40)
        .map(s => (s.querySelector('h2')||{}).textContent || '(no h2)')
    """)
    R.check("1", "no section is blank", empties == [], empties)

    notes = c.js("""
      (() => {
        const sec = [...document.querySelectorAll('section')].find(s => {
          const h = s.querySelector('h2');
          return h && h.textContent.trim() === 'What happened while it was built';
        });
        if (!sec) return {err: 'section not found'};
        const lead = (sec.querySelector('p') || {}).textContent || '';
        const labels = [...sec.querySelectorAll('li')]
          .map(e => (e.textContent.match(/T0\\d\\d/) || [null])[0]).filter(Boolean);
        return {lead: lead.replace(/\\s+/g, ' ').trim(), labels: labels,
                adjacent: labels.some((v, i) => i > 0 && v === labels[i - 1])};
      })()
    """)
    R.eq("1", "implementation notes render in record order T007, T009, T007",
         notes.get("labels", [])[:3], ["T007", "T009", "T007"])
    R.check("1", "the two T007 entries are not adjacent", notes.get("adjacent") is False, notes)
    lead = notes.get("lead", "").lower()
    R.check("1", "notes lead sentence explains ordering and repetition",
            "order" in lead and ("more than once" in lead or "twice" in lead), notes.get("lead"))

    labels = c.js("[...document.querySelectorAll('#export button')].map(b=>b.textContent.trim())")
    R.eq("1", "export buttons named by destination", labels, ["Copy as prompt", "Copy as Markdown"])

    c.js(RECORDER)
    c.screenshot(os.path.join(SHOTS, "s1-01-light-full.png"), full=True)

    # ---------------- Step 2 : offline behaviour ----------------
    font = c.js("""
      (() => {
        const cs = getComputedStyle(document.querySelector('h1'));
        return {family: cs.fontFamily,
                loaded: [...document.fonts].filter(f=>f.status==='loaded').map(f=>f.family)};
      })()
    """)
    R.check("2", "no webfont loaded while offline (generic fallback in use)",
            font["loaded"] == [], font)
    ok = c.js("""
      (() => {
        const d = [...document.querySelectorAll('details')]
          .find(x => (x.querySelector('summary')||{}).textContent
                     .startsWith('Question on What this change deliberately leaves out'));
        const before = d.open; d.open = true; const opened = d.open && !!d.querySelector('textarea');
        d.open = false; return {before, opened, closed: !d.open};
      })()
    """)
    R.check("2", "disclosure opens and closes with no network",
            ok["opened"] and ok["closed"] and not ok["before"], ok)
    R.check("2", "no horizontal page scroll",
            c.js("document.documentElement.scrollWidth <= window.innerWidth + 1"),
            c.js("[document.documentElement.scrollWidth, window.innerWidth]"))

    # ---------------- Step 3 : themes ----------------
    def contrast_probe():
        return c.js("""
          (() => {
            const lum = (c) => { const [r,g,b]=c.match(/\\d+(\\.\\d+)?/g).slice(0,3).map(Number)
                .map(v=>{v/=255; return v<=0.03928? v/12.92 : Math.pow((v+0.055)/1.055,2.4);});
              return 0.2126*r+0.7152*g+0.0722*b; };
            const bgOf = (el) => { let n=el; while(n){ const b=getComputedStyle(n).backgroundColor;
              if(b && !/rgba\\(0, 0, 0, 0\\)|transparent/.test(b)) return b; n=n.parentElement; }
              return getComputedStyle(document.body).backgroundColor; };
            const ratio = (el) => { const f=lum(getComputedStyle(el).color), b=lum(bgOf(el));
              const hi=Math.max(f,b), lo=Math.min(f,b); return (hi+0.05)/(lo+0.05); };
            const out=[];
            document.querySelectorAll('h1,h2,h3,p,li,summary,button,label').forEach(el=>{
              if(!el.textContent.trim()) return;
              const r = el.getBoundingClientRect(); if(!r.width||!r.height) return;
              const cs=getComputedStyle(el); if(cs.visibility==='hidden'||cs.display==='none') return;
              const px=parseFloat(cs.fontSize);
              const large = px>=24 || (px>=18.66 && parseInt(cs.fontWeight,10)>=700);
              out.push({tag:el.tagName, txt:el.textContent.trim().slice(0,40),
                        ratio:+ratio(el).toFixed(2), need: large?3.0:4.5});
            });
            return out.filter(o=>o.ratio < o.need);
          })()
        """)

    fails_light = contrast_probe()
    R.check("3", "light theme: every text node meets WCAG AA contrast",
            fails_light == [], json.dumps(fails_light[:10], indent=1))

    c.click_ref("button")  # the theme toggle is the first button
    time.sleep(0.4)
    theme = c.js("document.documentElement.getAttribute('data-theme') || document.documentElement.className")
    R.check("3", "toggle switches theme", bool(theme) and "dark" in str(theme).lower(), theme)
    R.eq("3", "toggle label is stable (names the action)",
         c.js("document.querySelector('button').textContent.trim()"), "Dark theme")
    fails_dark = contrast_probe()
    R.check("3", "dark theme: every text node meets WCAG AA contrast",
            fails_dark == [], json.dumps(fails_dark[:10], indent=1))
    c.screenshot(os.path.join(SHOTS, "s1-02-dark-full.png"), full=True)

    boxes = c.js("""
      (() => {
        const sec=[...document.querySelectorAll('section')][1];
        return [...sec.querySelectorAll('div,aside,figure')].filter(e=>{
          const cs=getComputedStyle(e); return cs.borderTopWidth!=='0px' || cs.backgroundColor!=='rgba(0, 0, 0, 0)';
        }).length;
      })()
    """)
    R.check("3", "before/after boxes stay outlined in dark theme", boxes >= 2, boxes)
    c.click_ref("button")
    time.sleep(0.3)

    # ---------------- Step 4 : achromatopsia ----------------
    c.vision("achromatopsia")
    time.sleep(0.3)
    carriers = c.js("""
      (() => {
        const bolds = [...document.querySelectorAll('strong,b')].map(e=>e.textContent.trim());
        return {before: bolds.includes('Before.'), after: bolds.includes('After.'),
                passed: bolds.some(t=>t==='Passed.'), pending: bolds.some(t=>t==='Pending.'),
                t007: bolds.filter(t=>t.indexOf('T007')>=0).length, sample: bolds.slice(0,14)};
      })()
    """)
    R.check("4", "before/after carried by the words 'Before.' and 'After.'",
            carriers["before"] and carriers["after"], carriers)
    R.check("4", "pass/pending carried by the words 'Passed.' and 'Pending.'",
            carriers["passed"] and carriers["pending"], carriers)
    R.check("4", "repeated T007 label legible twice with identical bold text",
            carriers["t007"] >= 2, carriers)
    c.screenshot(os.path.join(SHOTS, "s1-03-achromatopsia-full.png"), full=True)
    c.vision("none")

    # ---------------- Step 5 : tab order ----------------
    # Reload first. Step 3 clicked the theme toggle, and blur() does not reset
    # the sequential focus navigation starting point — Tab would resume from
    # that button and silently drop the first stop from the traversal.
    c.js("location.reload()")
    c.pump(2.5)
    c.js("window.scrollTo(0,0);")
    order = []
    for _ in range(16):
        c.tab()
        cur = c.js("""
          (() => { const a=document.activeElement; if(!a || a===document.body) return null;
            return {tag:a.tagName, id:a.id||null, txt:(a.textContent||a.getAttribute('aria-label')||'').trim().slice(0,70),
                    outline: (() => { const cs=getComputedStyle(a);
                      return cs.outlineStyle!=='none' && parseFloat(cs.outlineWidth)>0
                             ? 'outline' : (cs.boxShadow!=='none' ? 'boxShadow' : 'NONE'); })()};
          })()
        """)
        if cur is None:
            break
        order.append(cur)

    # The runbook enumerates ten bullets, but bullet 4 covers the three
    # file-item controls, so twelve stops is the enumeration, not a surplus.
    seq = [(o["tag"], o["txt"][:48]) for o in order]
    cycle = seq[:12]
    R.eq("5", "tab visits exactly the 12 enumerated controls, in order",
         [t for t, _ in cycle],
         ["BUTTON"] + ["SUMMARY"] * 9 + ["BUTTON", "BUTTON"])
    R.eq("5", "the first stop is the theme toggle", cycle[0][1], "Dark theme")
    R.eq("5", "the last two stops are the export buttons",
         [cycle[10][1], cycle[11][1]], ["Copy as prompt", "Copy as Markdown"])
    R.check("5", "no closed disclosure leaks its textarea into the tab ring",
            all(t != "TEXTAREA" for t, _ in cycle), cycle)
    noind = [o for o in order[:12] if o["outline"] == "NONE"]
    R.check("5", "every stop shows a visible focus indicator", noind == [],
            json.dumps(noind, indent=1))

    back = []
    c.js("document.getElementById('copy-markdown').focus()")
    for _ in range(11):
        c.tab(shift=True)
        cur = c.js("(()=>{const a=document.activeElement; return a&&a!==document.body?{tag:a.tagName,txt:(a.textContent||'').trim().slice(0,48)}:null;})()")
        if cur is None:
            break
        back.append((cur["tag"], cur["txt"]))
    R.eq("5", "shift+tab retraces the same controls in reverse, nothing skipped",
         back, list(reversed(cycle))[1:])

    # ---------------- Step 6 : keyboard question control ----------------
    c.js("location.reload()")
    c.pump(2.5)
    c.js(RECORDER)
    lbl = c.js("""(()=>{const s=[...document.querySelectorAll('summary')]
       .find(s=>s.textContent.startsWith('Question on Why this change was made')); return s.textContent.trim();})()""")
    R.eq("6", "unfilled control states 'no question recorded'", lbl,
         "Question on Why this change was made: no question recorded")

    c.js("(document.activeElement||{}).blur&&document.activeElement.blur(); window.scrollTo(0,0);")
    c.tab(2)                       # theme button, then first question summary
    R.check("6", "keyboard reaches the first question control",
            c.js("document.activeElement.tagName") == "SUMMARY",
            c.js("document.activeElement.tagName + ' / ' + document.activeElement.textContent.trim().slice(0,60)"))
    c.key("Enter", "Enter", 13)
    time.sleep(0.25)
    R.check("6", "Enter opens the control",
            c.js("document.activeElement.closest('details').open"), "")
    c.tab()
    R.check("6", "Tab lands inside the textarea",
            c.js("document.activeElement.id") == "question-motivation",
            c.js("document.activeElement.tagName + '#' + document.activeElement.id"))
    R.eq("6", "textarea has a real label",
         c.js("""(()=>{const t=document.getElementById('question-motivation');
                 const l=document.querySelector('label[for=\\'question-motivation\\']');
                 return l?l.textContent.trim():'(none)';})()"""),
         "Your question about Why this change was made")

    Q1 = "Why not queue on the server side instead?"
    c.type_text(Q1)
    R.eq("6", "typed text landed in the field",
         c.js("document.getElementById('question-motivation').value"), Q1)
    R.eq("6", "summary label updates the instant you type",
         c.js("""(()=>document.getElementById('question-motivation')
                 .closest('details').querySelector('summary').textContent.trim())()"""),
         "Question on Why this change was made: question recorded")

    # ---------------- Step 7 : two questions, prompt export ----------------
    Q2 = "What is the plan if the staging soak fails?"
    c.js("""(() => { const t=document.getElementById('question-verification');
            t.focus(); t.value=%s; t.dispatchEvent(new Event('input',{bubbles:true})); })()""" % json.dumps(Q2))
    c.js("window.__clip = []")
    c.click_ref("#copy-prompt")
    time.sleep(0.8)
    status = c.js("document.getElementById('export-status').textContent.trim()")
    clip = c.js("window.__clip.slice(-1)[0] || null")
    R.eq("7", "status counts both questions", status, "Copied. 2 questions are on the clipboard.")
    EXPECT_PROMPT = (
        "Artifact: Pull Request Write-up\n"
        "Feature: NIMBUS-101 Offline Draft Sync\n"
        "\n"
        "Act on each question recorded below. The value in parentheses is the anchor of the section it attaches to.\n"
        "\n"
        "motivation / Why this change was made  (#sec-motivation)\n"
        "Why not queue on the server side instead?\n"
        "\n"
        "verification / How it was checked  (#sec-verification)\n"
        "What is the plan if the staging soak fails?"
    )
    R.eq("7", "prompt export text is exactly as specified", (clip or "").strip(), EXPECT_PROMPT)
    R.check("7", "reference lines carry exactly two spaces before '('",
            (clip or "").count("was made  (#sec-motivation)") == 1
            and (clip or "").count("was checked  (#sec-verification)") == 1, clip)
    R.check("7", "empty sections contribute nothing",
            "non-goals" not in (clip or "") and "before-after" not in (clip or ""), clip)

    # ---------------- Step 8 : markdown export ----------------
    c.js("window.__clip = []")
    c.click_ref("#copy-markdown")
    time.sleep(0.8)
    md = c.js("window.__clip.slice(-1)[0] || null")
    diff = [(a, b) for a, b in zip((clip or "").split("\n"), (md or "").split("\n")) if a != b]
    R.eq("8", "markdown export differs in exactly one line", len(diff), 1)
    R.eq("8", "the differing line is the markdown lead", diff[0][1] if diff else None,
         "Questions recorded while reading this pull-request write-up.")
    R.check("8", "no markdown syntax in the payload",
            not any(t in (md or "") for t in ["**", "`", "# ", "- "]), md)

    # ---------------- Step 9 : edit then export immediately ----------------
    SUFFIX = " — and is it too late to change that?"
    c.js("""(() => { const t=document.getElementById('question-motivation');
            t.focus(); t.value = t.value + %s; t.dispatchEvent(new Event('input',{bubbles:true})); })()""" % json.dumps(SUFFIX))
    c.js("window.__clip = []")
    c.click_ref("#copy-prompt")
    time.sleep(0.8)
    live = c.js("window.__clip.slice(-1)[0] || null")
    R.check("9", "export reflects the edit made a moment earlier",
            SUFFIX.strip() in (live or ""), live)

    # ---------------- Step 10 : empty export ----------------
    c.js("""(() => { ['question-motivation','question-verification'].forEach(id => {
            const t=document.getElementById(id); t.value=''; t.dispatchEvent(new Event('input',{bubbles:true})); }); })()""")
    c.js("window.__clip = []")
    c.click_ref("#copy-prompt")
    time.sleep(0.8)
    R.eq("10", "empty prompt status", c.js("document.getElementById('export-status').textContent.trim()"),
         "Copied. The text says no question was recorded.")
    R.eq("10", "empty prompt payload", (c.js("window.__clip.slice(-1)[0] || ''") or "").strip(),
         "Artifact: Pull Request Write-up\n"
         "Feature: NIMBUS-101 Offline Draft Sync\n"
         "\n"
         "No question was recorded. There is nothing here to act on. Do not treat this as approval.")
    c.js("window.__clip = []")
    c.click_ref("#copy-markdown")
    time.sleep(0.8)
    R.eq("10", "empty markdown payload", (c.js("window.__clip.slice(-1)[0] || ''") or "").strip(),
         "Artifact: Pull Request Write-up\n"
         "Feature: NIMBUS-101 Offline Draft Sync\n"
         "\n"
         "No question was recorded. This record is not an approval.")

    # ---------------- Step 11 : forced clipboard refusal ----------------
    c.js("""(() => { const t=document.getElementById('question-motivation');
            t.value=%s; t.dispatchEvent(new Event('input',{bubbles:true}));
            const v=document.getElementById('question-verification');
            v.value=%s; v.dispatchEvent(new Event('input',{bubbles:true})); })()"""
         % (json.dumps(Q1), json.dumps(Q2)))
    c.js("""navigator.clipboard.writeText = function () {
              return Promise.reject(new Error('simulated refusal')); };""")
    c.click_ref("#copy-prompt")
    time.sleep(1.2)
    R.eq("11", "failure is reported in words, never as success",
         c.js("document.getElementById('export-status').textContent.trim()"),
         "Copy failed. The text is in the field below. Select it and copy it by hand.")
    R.check("11", "fallback field is revealed",
            not c.js("document.getElementById('fallback').hasAttribute('hidden')"), "")
    R.eq("11", "fallback holds the full export text",
         c.js("document.getElementById('fallback-field').value").strip(), EXPECT_PROMPT)
    R.check("11", "focus moves into the fallback field",
            c.js("document.activeElement.id") == "fallback-field",
            c.js("document.activeElement.tagName + '#' + document.activeElement.id"))
    c.click_ref("#copy-markdown")
    time.sleep(1.2)
    R.check("11", "markdown refusal reveals the markdown-lead text",
            "Questions recorded while reading this pull-request write-up."
            in c.js("document.getElementById('fallback-field').value"),
            c.js("document.getElementById('fallback-field').value")[:200])
    c.screenshot(os.path.join(SHOTS, "s1-04-fallback.png"))

    # ---------------- Step 12 : invocation currency ----------------
    c.js("""
      window.__race = 0;
      navigator.clipboard.writeText = function () {
        window.__race += 1;
        const isFirst = (window.__race === 1);
        return new Promise(function (resolve, reject) {
          window.setTimeout(function () {
            if (isFirst) { reject(new Error('simulated slow refusal')); } else { resolve(); }
          }, isFirst ? 1000 : 0);
        });
      };
      document.getElementById('fallback').setAttribute('hidden','');
      document.getElementById('export-status').textContent = '';
    """)
    c.click_ref("#copy-prompt")
    time.sleep(0.15)
    c.click_ref("#copy-markdown")
    time.sleep(0.4)
    early = c.js("document.getElementById('export-status').textContent.trim()")
    R.eq("12", "the later click reports success immediately", early,
         "Copied. 2 questions are on the clipboard.")
    time.sleep(3.0)
    late = c.js("document.getElementById('export-status').textContent.trim()")
    R.eq("12", "the superseded failure never overwrites the status", late,
         "Copied. 2 questions are on the clipboard.")
    R.check("12", "the superseded failure never reveals the fallback",
            c.js("document.getElementById('fallback').hasAttribute('hidden')"), "")
    R.check("12", "the superseded failure never steals focus",
            c.js("document.activeElement.id") != "fallback-field",
            c.js("document.activeElement.tagName + '#' + document.activeElement.id"))

    print("\n--- console at end of run (cumulative) ---")
    print(json.dumps(c.console_report(), indent=1))

finally:
    p, t = R.summary()
    R.dump(os.path.join(os.path.dirname(os.path.abspath(__file__)), "slice1-results.json"))
    c.close()
    sys.exit(0 if p == t else 1)
