"""HTTP routes: JSON API under /api plus a small web form at /."""
import csv
import io

from flask import Blueprint, Response, jsonify, render_template, request

from .db import get_db
from .sentiment import analyze
from .validators import CHANNELS, validate_feedback

bp = Blueprint("feedback", __name__)

COLUMNS = ("id", "name", "email", "channel", "rating", "message", "sentiment", "score", "created_at")
SENTIMENTS = ("positive", "neutral", "negative")


def _row_to_dict(row):
    return {key: row[key] for key in COLUMNS}


def _error(message, status, details=None):
    body = {"error": message}
    if details:
        body["details"] = details
    return jsonify(body), status


def _positive_int(name, default, maximum=None):
    raw = request.args.get(name, default)
    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be an integer")
    if value < 1:
        raise ValueError(f"{name} must be >= 1")
    if maximum is not None:
        value = min(value, maximum)
    return value


def _filters():
    """Build a WHERE clause from validated query params. Values are always bound."""
    clauses, params = [], []
    channel = request.args.get("channel")
    sentiment = request.args.get("sentiment")
    if channel:
        if channel not in CHANNELS:
            raise ValueError(f"channel must be one of: {', '.join(CHANNELS)}")
        clauses.append("channel = ?")
        params.append(channel)
    if sentiment:
        if sentiment not in SENTIMENTS:
            raise ValueError(f"sentiment must be one of: {', '.join(SENTIMENTS)}")
        clauses.append("sentiment = ?")
        params.append(sentiment)
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    return where, params


@bp.get("/")
def index():
    return render_template("index.html", channels=CHANNELS)


@bp.get("/health")
def health():
    get_db().execute("SELECT 1")
    return jsonify({"status": "ok"})


@bp.post("/api/feedback")
def create_feedback():
    payload = request.get_json(silent=True)
    clean, errors = validate_feedback(payload)
    if errors:
        return _error("validation failed", 400, errors)

    score, label = analyze(clean["message"])
    db = get_db()
    cur = db.execute(
        "INSERT INTO feedback (name, email, channel, rating, message, sentiment, score) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (clean["name"], clean["email"], clean["channel"], clean["rating"],
         clean["message"], label, score),
    )
    db.commit()
    row = db.execute("SELECT * FROM feedback WHERE id = ?", (cur.lastrowid,)).fetchone()
    response = jsonify(_row_to_dict(row))
    response.status_code = 201
    response.headers["Location"] = f"/api/feedback/{cur.lastrowid}"
    return response


@bp.get("/api/feedback")
def list_feedback():
    try:
        page = _positive_int("page", 1)
        per_page = _positive_int("per_page", 20, maximum=100)
        where, params = _filters()
    except ValueError as exc:
        return _error(str(exc), 400)

    db = get_db()
    total = db.execute(f"SELECT COUNT(*) FROM feedback{where}", params).fetchone()[0]
    rows = db.execute(
        f"SELECT * FROM feedback{where} ORDER BY id DESC LIMIT ? OFFSET ?",
        [*params, per_page, (page - 1) * per_page],
    ).fetchall()
    return jsonify({
        "items": [_row_to_dict(r) for r in rows],
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": (total + per_page - 1) // per_page,
    })


@bp.get("/api/feedback/<int:feedback_id>")
def get_feedback(feedback_id):
    row = get_db().execute("SELECT * FROM feedback WHERE id = ?", (feedback_id,)).fetchone()
    if row is None:
        return _error("feedback not found", 404)
    return jsonify(_row_to_dict(row))


@bp.delete("/api/feedback/<int:feedback_id>")
def delete_feedback(feedback_id):
    db = get_db()
    cur = db.execute("DELETE FROM feedback WHERE id = ?", (feedback_id,))
    db.commit()
    if cur.rowcount == 0:
        return _error("feedback not found", 404)
    return "", 204


@bp.get("/api/feedback/export")
def export_csv():
    try:
        where, params = _filters()
    except ValueError as exc:
        return _error(str(exc), 400)
    rows = get_db().execute(f"SELECT * FROM feedback{where} ORDER BY id", params).fetchall()

    def cell(value):
        # Prefix text starting with formula characters to prevent CSV injection in spreadsheets
        if isinstance(value, str) and value[:1] in ("=", "+", "-", "@"):
            return "'" + value
        return value

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(COLUMNS)
    for row in rows:
        writer.writerow([cell(row[c]) for c in COLUMNS])
    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=feedback.csv"},
    )


@bp.get("/api/analytics/summary")
def summary():
    db = get_db()
    total, avg_rating, avg_score = db.execute(
        "SELECT COUNT(*), AVG(rating), AVG(score) FROM feedback"
    ).fetchone()

    def grouped(column, keys):
        counts = {str(k): 0 for k in keys}
        for row in db.execute(f"SELECT {column} AS k, COUNT(*) AS n FROM feedback GROUP BY {column}"):
            counts[str(row["k"])] = row["n"]
        return counts

    return jsonify({
        "total": total,
        "average_rating": round(avg_rating, 2) if avg_rating is not None else None,
        "average_sentiment_score": round(avg_score, 3) if avg_score is not None else None,
        "by_sentiment": grouped("sentiment", SENTIMENTS),
        "by_channel": grouped("channel", CHANNELS),
        "rating_distribution": grouped("rating", range(1, 6)),
    })
