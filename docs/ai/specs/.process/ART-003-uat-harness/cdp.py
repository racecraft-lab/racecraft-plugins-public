"""Minimal Chrome DevTools Protocol driver (stdlib only).

Drives a real Chrome against a file:// URL over CDP, so the manual UAT runs
against the actual scheme the artifacts ship for. No server, no scheme
substitution.

**This module never launches a browser, deliberately.** Launching one means
naming a Chrome binary, and no such path is correct for every contributor:
macOS, Linux and Windows disagree, and so do Chrome, Chromium and Chrome Beta.
A committed path would be wrong for most readers of this repository and would
also leave the Bash-confinement guard unable to prove the launch reaches a
browser rather than a shell.

So the operator starts Chrome, and this connects to it. See
`ART-003-uat-results.md` for the one command per platform.
"""

import base64
import json
import os
import socket
import struct
import time
import urllib.parse
import urllib.request

DEFAULT_ENDPOINT = "http://127.0.0.1:9222"

BRAND_FONT_HOST = "fonts.googleapis.com"


def is_brand_font_request(url):
    """True when `url`'s host IS the brand font host.

    Compare the parsed host, never a substring. `"fonts.googleapis.com" in url`
    also matches `https://example.com/fonts.googleapis.com`, so a console entry
    from an unrelated origin would be waved through as "just the webfont" and
    the offline assertions would pass while missing a real request.
    """
    try:
        return urllib.parse.urlsplit(url or "").hostname == BRAND_FONT_HOST
    except ValueError:
        return False


class WS:
    """Just enough RFC 6455 for CDP: text frames, fragmentation, ping/pong."""

    def __init__(self, url, timeout=60):
        assert url.startswith("ws://"), url
        rest = url[len("ws://"):]
        hostport, _, path = rest.partition("/")
        host, _, port = hostport.partition(":")
        # Bound the connect too, not only the reads. settimeout() applies after
        # the socket exists, so an unreachable endpoint would otherwise block for
        # the OS-level connect timeout regardless of what the caller asked for.
        self.sock = socket.create_connection((host, int(port or 80)), timeout=timeout)
        self.sock.settimeout(timeout)
        key = base64.b64encode(os.urandom(16)).decode()
        req = (
            "GET /%s HTTP/1.1\r\n"
            "Host: %s\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            "Sec-WebSocket-Key: %s\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n" % (path, hostport, key)
        )
        self.sock.sendall(req.encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise RuntimeError("handshake: connection closed")
            buf += chunk
        head, _, remainder = buf.partition(b"\r\n\r\n")
        if b" 101 " not in head.split(b"\r\n")[0]:
            raise RuntimeError("handshake failed: %r" % head[:200])
        self._buf = bytearray(remainder)

    def _exact(self, n):
        while len(self._buf) < n:
            chunk = self.sock.recv(1 << 20)
            if not chunk:
                raise RuntimeError("socket closed mid-frame")
            self._buf += chunk
        out = bytes(self._buf[:n])
        del self._buf[:n]
        return out

    def send(self, text):
        payload = text.encode()
        mask = os.urandom(4)
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        n = len(payload)
        header = bytearray([0x81])
        if n < 126:
            header.append(0x80 | n)
        elif n < 65536:
            header.append(0x80 | 126)
            header += struct.pack(">H", n)
        else:
            header.append(0x80 | 127)
            header += struct.pack(">Q", n)
        self.sock.sendall(bytes(header) + mask + masked)

    def _frame(self):
        b0, b1 = self._exact(2)
        fin = bool(b0 & 0x80)
        opcode = b0 & 0x0F
        masked = bool(b1 & 0x80)
        ln = b1 & 0x7F
        if ln == 126:
            ln = struct.unpack(">H", self._exact(2))[0]
        elif ln == 127:
            ln = struct.unpack(">Q", self._exact(8))[0]
        if masked:
            mk = self._exact(4)
            data = self._exact(ln)
            data = bytes(b ^ mk[i % 4] for i, b in enumerate(data))
        else:
            data = self._exact(ln)
        return fin, opcode, data

    def recv(self):
        parts = []
        while True:
            fin, opcode, data = self._frame()
            if opcode == 0x8:
                raise RuntimeError("peer closed websocket")
            if opcode == 0x9:  # ping -> pong
                self.sock.sendall(b"\x8a\x80" + os.urandom(4))
                continue
            if opcode == 0xA:
                continue
            parts.append(data)
            if fin:
                return b"".join(parts).decode("utf-8", "replace")

    def close(self):
        try:
            self.sock.close()
        except Exception:
            # Best effort. A socket the browser already dropped raises here, and
            # a failed close has nothing left to recover: the caller is done with
            # it either way.
            pass


class Chrome:
    """One isolated page in a Chrome the operator started.

    Every instance takes a fresh browser context, which is what keeps one
    stage's emulation state, storage and HTTP cache out of the next stage's.
    The cache matters: an offline reload in a reused context serves the brand
    webfont from cache and the offline assertions pass for the wrong reason.

    `headless` is accepted and ignored. Whether the browser is headless is
    decided when the operator launches it, not here.
    """

    def __init__(self, headless=True, width=1280, height=900, scale=2):
        self.endpoint = os.environ.get("CDP_ENDPOINT", DEFAULT_ENDPOINT).rstrip("/")
        # Retry rather than fail on the first timeout. The browser is shared
        # across every stage of a run, so a stage that opens while the previous
        # one is still tearing down can find it briefly unresponsive. Failing
        # there would zero a whole stage for a reason that has nothing to do
        # with the artifact under test.
        version = None
        last = None
        for _ in range(6):
            try:
                version = self._get("/json/version")
                break
            except Exception as exc:
                last = exc
                time.sleep(1.0)
        if version is None:
            raise RuntimeError(
                "no Chrome is answering at %s. Start one with "
                "--remote-debugging-port=9222 and a scratch --user-data-dir, or point "
                "CDP_ENDPOINT at an existing one. ART-003-uat-results.md has the "
                "command for each platform." % self.endpoint
            ) from last
        self.browser = WS(version["webSocketDebuggerUrl"])
        self._bid = 0
        self.context = self._browser_call(
            "Target.createBrowserContext", {"disposeOnDetach": False}
        )["browserContextId"]
        # No width/height here on purpose. Sizing is done by
        # Emulation.setDeviceMetricsOverride, which the width sweeps re-apply
        # per breakpoint; pinning the target window as well makes the renderer
        # stall on repeated overrides.
        self.target = self._browser_call(
            "Target.createTarget",
            {"url": "about:blank", "browserContextId": self.context},
        )["targetId"]
        ws_url = None
        deadline = time.time() + 20
        while time.time() < deadline and ws_url is None:
            for t in self._get("/json/list"):
                if t.get("id") == self.target:
                    ws_url = t.get("webSocketDebuggerUrl")
                    break
            if ws_url is None:
                time.sleep(0.1)
        if ws_url is None:
            raise RuntimeError("the new target never appeared on /json/list")
        self.ws = WS(ws_url)
        self._id = 0
        self.events = []
        self.width, self.height, self.scale = width, height, scale

    # ---- protocol ----

    def _get(self, path):
        # Close each response rather than leaving it to the collector: a full
        # sweep opens one of these per stage plus a polling loop per target, and
        # the descriptors accumulate.
        with urllib.request.urlopen(self.endpoint + path, timeout=10) as resp:
            return json.loads(resp.read())

    def grant(self, permissions):
        """Grant browser permissions to THIS page's context.

        `Browser.grantPermissions` is browser-scoped, and with no
        `browserContextId` it grants to the default context. Every page here
        lives in its own context, so omitting the id grants the permission
        somewhere the page cannot see it, and `readText` fails with
        NotAllowedError while every other assertion still passes.
        """
        self.call(
            "Browser.grantPermissions",
            {"permissions": list(permissions), "browserContextId": self.context},
        )

    def _browser_call(self, method, params=None, timeout=30):
        """Browser-scoped call, for the target and context lifecycle only."""
        self._bid += 1
        mid = self._bid
        self.browser.send(
            json.dumps({"id": mid, "method": method, "params": params or {}})
        )
        deadline = time.time() + timeout
        while time.time() < deadline:
            msg = json.loads(self.browser.recv())
            if msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError("%s -> %s" % (method, msg["error"]))
                return msg.get("result", {})
        raise RuntimeError("timeout waiting for %s" % method)

    def call(self, method, params=None, timeout=60):
        self._id += 1
        mid = self._id
        self.ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        deadline = time.time() + timeout
        while time.time() < deadline:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError("%s -> %s" % (method, msg["error"]))
                return msg.get("result", {})
            if "method" in msg:
                self.events.append(msg)
        raise RuntimeError("timeout waiting for %s" % method)

    def pump(self, seconds):
        """Collect events for a while without issuing a command."""
        end = time.time() + seconds
        self.ws.sock.settimeout(0.25)
        try:
            while time.time() < end:
                try:
                    msg = json.loads(self.ws.recv())
                except (socket.timeout, TimeoutError):
                    continue
                if "method" in msg:
                    self.events.append(msg)
        finally:
            self.ws.sock.settimeout(60)

    def take(self, *methods):
        """Drain and return events matching the given method names."""
        return [e for e in self.events if e["method"] in methods]

    def clear_events(self):
        self.events = []

    # ---- convenience ----

    def enable_all(self):
        for d in ("Page", "Runtime", "Log", "Network", "DOM", "Accessibility"):
            try:
                self.call(d + ".enable")
            except RuntimeError:
                # Not every domain exists on every target or Chrome build. A
                # domain that will not enable simply yields no events, and every
                # assertion that needs one fails loudly on its own.
                pass
        # Give every page focus, unconditionally.
        #
        # This harness dispatches real key events and reads the clipboard, and
        # both need a focused document. When each stage owned a whole browser its
        # single window was focused for free; sharing one browser means a new
        # target opens in the background, where Tab moves nothing and
        # `activeElement` never leaves `body`. A tab-order traversal then records
        # ZERO stops and reports it as a failed expectation, which reads exactly
        # like a broken artifact and is not one. `readText` fails the same way,
        # with "Document is not focused".
        for method, params in (
            ("Emulation.setFocusEmulationEnabled", {"enabled": True}),
            ("Page.bringToFront", None),
        ):
            try:
                self.call(method, params)
            except RuntimeError:
                # Older Chrome builds lack one or the other. Any assertion that
                # actually depends on focus fails on its own if this did nothing.
                pass
        self.call(
            "Emulation.setDeviceMetricsOverride",
            {
                "width": self.width,
                "height": self.height,
                "deviceScaleFactor": self.scale,
                "mobile": False,
            },
        )

    def viewport(self, width, height=None):
        """Resize the emulated viewport, keeping this session's scale factor.

        Changing `deviceScaleFactor` between overrides is what stalls the
        renderer: a breakpoint sweep that flips 2 to 1 and back leaves a later
        `Runtime.evaluate` waiting past any sane timeout. Width is the variable
        a breakpoint sweep actually cares about, so hold everything else fixed.
        """
        self.call(
            "Emulation.setDeviceMetricsOverride",
            {
                "width": width,
                "height": height if height is not None else self.height,
                "deviceScaleFactor": self.scale,
                "mobile": False,
            },
        )

    def offline(self, on=True):
        self.call(
            "Network.emulateNetworkConditions",
            {
                "offline": on,
                "latency": 0,
                "downloadThroughput": -1 if not on else 0,
                "uploadThroughput": -1 if not on else 0,
            },
        )

    def navigate(self, url, settle=2.5):
        self.call("Page.navigate", {"url": url})
        self.pump(settle)

    def js(self, expr, await_promise=False):
        r = self.call(
            "Runtime.evaluate",
            {
                "expression": expr,
                "returnByValue": True,
                "awaitPromise": await_promise,
                "userGesture": True,
            },
        )
        if "exceptionDetails" in r:
            raise RuntimeError(
                "JS threw: %s" % json.dumps(r["exceptionDetails"])[:600]
            )
        return r["result"].get("value")

    # Keys whose activation behaviour Chrome only applies when the keyDown
    # carries its text payload (Enter/Space activating a <summary>, etc).
    _KEY_TEXT = {"Enter": "\r", " ": " ", "Space": " "}

    def key(self, key, code=None, vk=None, text=None, modifiers=0, repeat=1):
        code = code or key
        if text is None:
            text = self._KEY_TEXT.get(key)
        for _ in range(repeat):
            base = {
                "key": key,
                "code": code,
                "windowsVirtualKeyCode": vk or 0,
                "nativeVirtualKeyCode": vk or 0,
                "modifiers": modifiers,
            }
            down = dict(base, type="keyDown")
            if text is not None:
                down["text"] = text
                down["unmodifiedText"] = text
            self.call("Input.dispatchKeyEvent", down)
            self.call("Input.dispatchKeyEvent", dict(base, type="keyUp"))

    def tab(self, n=1, shift=False):
        self.key("Tab", "Tab", 9, modifiers=8 if shift else 0, repeat=n)

    def type_text(self, s):
        for ch in s:
            self.call("Input.dispatchKeyEvent", {"type": "keyDown", "text": ch, "key": ch})
            self.call("Input.dispatchKeyEvent", {"type": "keyUp", "key": ch})

    def click_ref(self, selector):
        """Scroll the first match into view, then click its centre.

        The scroll is not cosmetic: getBoundingClientRect is viewport-relative,
        so clicking a control below the fold otherwise dispatches the press at
        an off-screen coordinate and silently hits nothing.
        """
        self.js(
            "(() => { const e = document.querySelector(%s);"
            " if (e) e.scrollIntoView({block: 'center'}); })()" % json.dumps(selector)
        )
        time.sleep(0.2)
        box = self.js(
            "(() => { const e = document.querySelector(%s);"
            " if (!e) return null; const r = e.getBoundingClientRect();"
            " return {x: r.left + r.width/2, y: r.top + r.height/2}; })()"
            % json.dumps(selector)
        )
        if not box:
            raise RuntimeError("no element for %s" % selector)
        for t in ("mousePressed", "mouseReleased"):
            self.call(
                "Input.dispatchMouseEvent",
                {
                    "type": t,
                    "x": box["x"],
                    "y": box["y"],
                    "button": "left",
                    "clickCount": 1,
                },
            )

    def vision(self, kind):
        """kind: none | achromatopsia | deuteranopia | protanopia | tritanopia | blurredVision"""
        self.call("Emulation.setEmulatedVisionDeficiency", {"type": kind})

    def screenshot(self, path, full=False):
        params = {"format": "png", "captureBeyondViewport": full}
        if full:
            m = self.call("Page.getLayoutMetrics")
            cs = m["cssContentSize"]
            params["clip"] = {
                "x": 0,
                "y": 0,
                "width": cs["width"],
                "height": cs["height"],
                "scale": 1,
            }
        data = self.call("Page.captureScreenshot", params)["data"]
        with open(path, "wb") as fh:
            fh.write(base64.b64decode(data))
        return path

    def console_report(self):
        """Everything the console would have shown, from load onward."""
        out = []
        for e in self.events:
            m = e["method"]
            p = e.get("params", {})
            if m == "Log.entryAdded":
                en = p["entry"]
                out.append(
                    {
                        "kind": "log." + en.get("level", "?"),
                        "source": en.get("source"),
                        "text": en.get("text"),
                        "url": en.get("url"),
                    }
                )
            elif m == "Runtime.consoleAPICalled":
                out.append(
                    {
                        "kind": "console." + p.get("type", "?"),
                        "text": " ".join(
                            str(a.get("value", a.get("description", "")))
                            for a in p.get("args", [])
                        ),
                    }
                )
            elif m == "Runtime.exceptionThrown":
                d = p.get("exceptionDetails", {})
                out.append({"kind": "exception", "text": d.get("text"), "url": d.get("url")})
        return out

    def requests(self):
        return [
            {
                "url": e["params"]["request"]["url"],
                "type": e["params"].get("type"),
            }
            for e in self.events
            if e["method"] == "Network.requestWillBeSent"
        ]

    def close(self):
        """Drop this instance's page and context. The browser keeps running.

        Every step here is best effort by design. This runs from a `finally` in
        each stage, including the ones reached because an assertion already
        failed, and a teardown that raises would replace the real failure with
        its own. Anything left behind is bounded: the operator ends the browser
        and the whole profile goes with it.
        """
        try:
            self.ws.close()
        except Exception:
            pass
        for method, params in (
            ("Target.closeTarget", {"targetId": self.target}),
            ("Target.disposeBrowserContext", {"browserContextId": self.context}),
        ):
            try:
                self._browser_call(method, params, timeout=10)
            except Exception:
                pass
        try:
            self.browser.close()
        except Exception:
            pass


# ---- tiny assertion recorder ----

class Report:
    def __init__(self, name):
        self.name = name
        self.rows = []

    def check(self, step, claim, ok, detail=""):
        self.rows.append(
            {"step": step, "claim": claim, "ok": bool(ok), "detail": str(detail)[:1200]}
        )
        print("%-6s %-4s %s" % (step, "PASS" if ok else "FAIL", claim))
        if detail and not ok:
            print("         detail: %s" % str(detail)[:1200])
        return bool(ok)

    def eq(self, step, claim, actual, expected):
        ok = actual == expected
        return self.check(
            step,
            claim,
            ok,
            "" if ok else "expected %r\n         actual   %r" % (expected, actual),
        )

    def summary(self):
        passed = sum(1 for r in self.rows if r["ok"])
        print("\n=== %s: %d/%d passed ===" % (self.name, passed, len(self.rows)))
        for r in self.rows:
            if not r["ok"]:
                print("  FAIL %s  %s" % (r["step"], r["claim"]))
        return passed, len(self.rows)

    def dump(self, path):
        with open(path, "w") as fh:
            json.dump({"name": self.name, "rows": self.rows}, fh, indent=2)
