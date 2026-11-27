#!/usr/bin/env python3
import json, sys, time, urllib.request

USAGE = "\n".join([
    'Reference cli driver for bench.py ("driver": "cli"): forwards one request to an OpenAI-compatible URL.',
    "",
    "  python3 examples/cli-driver.py --url http://127.0.0.1:8080 [--model default]",
    "",
    "Reads ONE JSON object on stdin:",
    '  {"messages": [...], "max_tokens": int, "temperature": float, "seed": int|null, "extra": {...}}',
    "Prints ONE JSON object on stdout:",
    '  {"text": str, "prompt_tokens": int, "completion_tokens": int, "ttft_ms": float, "decode_ms": float,',
    '   "finish_reason": str, "engine": {"usage": {...}, "timings": {...}, "logprobs": [[token, logprob, top], ...]}}',
    "Exits non-zero with a message on stderr on failure. To drive a native engine (a persistent process, a socket,",
    "a Python binding), replace request() and keep the stdin/stdout contract.",
])


def request(url, model, req):
    body = {"model": model, "messages": req["messages"], "max_tokens": req["max_tokens"],
            "temperature": req["temperature"], "stream": True, "stream_options": {"include_usage": True}}
    if req.get("seed") is not None:
        body["seed"] = req["seed"]
    body.update(req.get("extra") or {})
    r = urllib.request.Request(url.rstrip("/") + "/v1/chat/completions", data=json.dumps(body).encode(),
                               headers={"Content-Type": "application/json"})
    t0, t_first, text, usage, timings, finish, toks = time.monotonic(), None, [], {}, None, None, []
    with urllib.request.urlopen(r, timeout=3600) as resp:
        for raw in resp:
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            ev = json.loads(data)
            usage = ev.get("usage") or usage
            timings = ev.get("timings") or timings
            for ch in ev.get("choices") or []:
                finish = ch.get("finish_reason") or finish
                d = ch.get("delta") or {}
                piece = (d.get("content") or "") + (d.get("reasoning_content") or "")
                if piece:
                    t_first = t_first or time.monotonic()
                    text.append(piece)
                for t in (ch.get("logprobs") or {}).get("content") or []:
                    toks.append([t.get("token"), t.get("logprob"),
                                 [[x.get("token"), x.get("logprob")] for x in t.get("top_logprobs") or []]])
    t_end = time.monotonic()
    t_first = t_first or t_end
    engine = {"usage": usage}
    if timings:
        engine["timings"] = timings
    if toks:
        engine["logprobs"] = toks
    return {"text": "".join(text), "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"), "ttft_ms": (t_first - t0) * 1000,
            "decode_ms": (t_end - t_first) * 1000, "finish_reason": finish, "engine": engine}


def main(a):
    if "--url" not in a or a.index("--url") + 1 >= len(a):
        sys.exit(USAGE)
    url = a[a.index("--url") + 1]
    model = a[a.index("--model") + 1] if "--model" in a and a.index("--model") + 1 < len(a) else "default"
    try:
        print(json.dumps(request(url, model, json.load(sys.stdin))))
    except Exception as e:
        sys.exit(f"cli-driver: {e!r}")


if __name__ == "__main__":
    main(sys.argv[1:])
