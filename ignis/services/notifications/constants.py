import ignis

NOTIFICATIONS_CACHE_DIR = f"{ignis.CACHE_DIR}/notifications"
NOTIFICATIONS_CACHE_FILE = f"{NOTIFICATIONS_CACHE_DIR}/notifications.json"
NOTIFICATIONS_IMAGE_DATA = f"{NOTIFICATIONS_CACHE_DIR}/images"
NOTIFICATIONS_EMPTY_CACHE_FILE: dict = {"id": 0, "notifications": []}