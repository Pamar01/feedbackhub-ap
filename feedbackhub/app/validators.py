"""Input validation for feedback submissions."""
import re

CHANNELS = ("web", "mobile", "email", "social")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

MAX_NAME = 100
MAX_EMAIL = 254
MIN_MESSAGE = 5
MAX_MESSAGE = 1000


def validate_feedback(payload):
    """Return (clean_data, errors). `errors` maps field name -> message."""
    errors = {}
    if not isinstance(payload, dict):
        return None, {"body": "JSON object expected"}

    name = payload.get("name")
    if not isinstance(name, str) or not name.strip():
        errors["name"] = "name is required"
    elif len(name.strip()) > MAX_NAME:
        errors["name"] = f"name must be at most {MAX_NAME} characters"

    email = payload.get("email")
    if not isinstance(email, str) or not EMAIL_RE.match(email.strip()):
        errors["email"] = "a valid email is required"
    elif len(email.strip()) > MAX_EMAIL:
        errors["email"] = f"email must be at most {MAX_EMAIL} characters"

    channel = payload.get("channel", "web")
    if channel not in CHANNELS:
        errors["channel"] = f"channel must be one of: {', '.join(CHANNELS)}"

    rating = payload.get("rating")
    # bool is a subclass of int in Python, so reject it explicitly
    if isinstance(rating, bool) or not isinstance(rating, int) or not 1 <= rating <= 5:
        errors["rating"] = "rating must be an integer between 1 and 5"

    message = payload.get("message")
    if not isinstance(message, str) or len(message.strip()) < MIN_MESSAGE:
        errors["message"] = f"message must be at least {MIN_MESSAGE} characters"
    elif len(message.strip()) > MAX_MESSAGE:
        errors["message"] = f"message must be at most {MAX_MESSAGE} characters"

    if errors:
        return None, errors

    return {
        "name": name.strip(),
        "email": email.strip().lower(),
        "channel": channel,
        "rating": rating,
        "message": message.strip(),
    }, {}
