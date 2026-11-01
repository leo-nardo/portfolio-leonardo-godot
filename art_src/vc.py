"""Cliente mínimo do servidor MCP do VectorCraft (stdio, headless), para desenhar por script.

Uso:
    from vc import VC
    with VC() as vc:
        vc.call("draw_shape", {...})
"""
import json
import subprocess

EXE = r"C:\Users\leona\Downloads\vectorcraft-0.18.0\app\vectorcraft-0.18.0-windows-x64-portable\vectorcraft-cli.exe"


class VC:
    def __init__(self, write_root=None):
        args = [EXE, "mcp", "--headless"]
        if write_root:
            args += ["--automation-read-root", write_root, "--automation-write-root", write_root]
        self.p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, encoding="utf-8")
        self._id = 0
        self._rpc("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "claude", "version": "1"}})
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def _send(self, msg):
        self.p.stdin.write(json.dumps(msg) + "\n")
        self.p.stdin.flush()

    def _rpc(self, method, params=None):
        self._id += 1
        self._send({"jsonrpc": "2.0", "id": self._id, "method": method, "params": params or {}})
        while True:
            line = self.p.stdout.readline()
            if not line:
                raise RuntimeError("servidor encerrou")
            msg = json.loads(line)
            if msg.get("id") == self._id:
                if "error" in msg:
                    raise RuntimeError(msg["error"])
                return msg["result"]

    def tools(self):
        return self._rpc("tools/list")["tools"]

    def call(self, name, args=None):
        res = self._rpc("tools/call", {"name": name, "arguments": args or {}})
        out = []
        self.images = []
        for c in res.get("content", []):
            if c.get("type") == "text":
                out.append(c["text"])
            elif c.get("type") == "image":
                self.images.append(c["data"])
        text = "\n".join(out)
        if res.get("isError"):
            raise RuntimeError(text)
        try:
            return json.loads(text)
        except Exception:
            return text

    def preview(self, path, max_side=1024):
        import base64
        self.call("render_preview", {"max_side": max_side})
        with open(path, "wb") as f:
            f.write(base64.b64decode(self.images[0]))

    def __enter__(self):
        return self

    def __exit__(self, *a):
        try:
            self.p.stdin.close()
            self.p.terminate()
        except Exception:
            pass
