import os
import re
import requests
from flask import Flask, request, jsonify
from functools import wraps

app = Flask(__name__)

# ============ CONFIG ============
API_KEY        = os.environ.get("API_KEY", "TITANKING")
UPSTREAM_URL   = os.environ.get("UPSTREAM_URL", "https://rtf-api-server.onrender.com/api")
UPSTREAM_KEY   = os.environ.get("UPSTREAM_KEY", "demo2")
OWNER          = os.environ.get("OWNER", "@TITANCONTACT @g0zig")
CHANNEL        = os.environ.get("CHANNEL", "@titankeng")
CHANNEL_LINK   = os.environ.get("CHANNEL_LINK", "https://t.me/titankeng")
API_BY         = os.environ.get("API_BY", "TITAN API")
VERSION        = "1.0.0"
# ================================


# ─── Key Middleware ─────────────────────────────────────────
def require_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.args.get("key") or request.headers.get("X-Api-Key")
        if not key:
            return jsonify({
                "error": True,
                "message": "API key required. Use ?key=KEY&spell=USERNAME",
                "owner": OWNER, "channel": CHANNEL, "channel_url": CHANNEL_LINK,
                "get_free_key": f"Join {CHANNEL} for free API key"
            }), 401
        if key != API_KEY:
            return jsonify({
                "error": True,
                "message": "Invalid API key.",
                "owner": OWNER, "channel": CHANNEL, "channel_url": CHANNEL_LINK,
                "get_free_key": f"Join {CHANNEL} for free API key"
            }), 403
        return f(*args, **kwargs)
    return decorated


# ─── Clean RTF developer tags ──────────────────────────────
REMOVE_KEYS = {"DM FOR BUY", "Developer", "developer", "dm_for_buy"}

def clean_result(result):
    if isinstance(result, dict):
        cleaned = {}
        for k, v in result.items():
            if k in REMOVE_KEYS:
                continue
            if isinstance(v, str):
                v = re.sub(r'\s*@\w+', '', v).strip()
            cleaned[k] = v
        return cleaned
    return result


# ─── Inject credits ───────────────────────────────────────
def inject_credits(data):
    data["owner"] = OWNER
    data["channel"] = CHANNEL
    data["channel_url"] = CHANNEL_LINK
    data["api_by"] = API_BY
    data["get_free_api_key"] = f"Join {CHANNEL} for free API key"
    return data


# ─── Home ─────────────────────────────────────────────────
@app.route("/")
def home():
    return jsonify({
        "name": "Spell Info API",
        "version": VERSION,
        "owner": OWNER,
        "channel": CHANNEL,
        "channel_url": CHANNEL_LINK,
        "endpoints": {"search": "/api?key=YOUR_KEY&types=telegram&spell=@USERNAME"},
        "get_free_key": f"Join {CHANNEL} for free API key"
    })


# ─── Main Endpoint ────────────────────────────────────────
@app.route("/api", methods=["GET"])
@require_key
def spell_lookup():
    spell = request.args.get("spell")
    types = request.args.get("types", "telegram")

    if not spell:
        return jsonify({
            "error": True,
            "message": 'Missing "spell" parameter',
            "owner": OWNER, "channel": CHANNEL, "channel_url": CHANNEL_LINK
        }), 400

    try:
        resp = requests.get(
            UPSTREAM_URL,
            params={"types": types, "key": UPSTREAM_KEY, "spell": spell},
            timeout=30,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        if resp.status_code != 200:
            return jsonify({
                "error": True,
                "message": f"Upstream returned {resp.status_code}",
                "owner": OWNER, "channel": CHANNEL, "channel_url": CHANNEL_LINK
            }), resp.status_code

        data = resp.json()

        if "result" in data:
            data["result"] = clean_result(data["result"])

        data = inject_credits(data)
        return jsonify(data)

    except requests.exceptions.Timeout:
        return jsonify({"error": True, "message": "Upstream timeout", "owner": OWNER, "channel": CHANNEL, "channel_url": CHANNEL_LINK}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({"error": True, "message": "Upstream error", "detail": str(e), "owner": OWNER, "channel": CHANNEL, "channel_url": CHANNEL_LINK}), 502
    except Exception as e:
        return jsonify({"error": True, "message": "Internal error", "detail": str(e), "owner": OWNER, "channel": CHANNEL, "channel_url": CHANNEL_LINK}), 500


# Vercel serverless entry point
app = app
