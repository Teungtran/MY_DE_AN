import uuid
import base64

def generate_short_id():
    uid = uuid.uuid4()
    short_id = base64.urlsafe_b64encode(uid.bytes).decode('utf-8').rstrip('=')
    return short_id[:9] 