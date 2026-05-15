import qrcode
import os
from ..config import settings


def generate_qr_code(slug: str, output_dir: str = "uploads/qr") -> str:
    os.makedirs(output_dir, exist_ok=True)
    url = f"{settings.base_url}/memorial/{slug}"
    img = qrcode.make(url)
    path = os.path.join(output_dir, f"{slug}.png")
    img.save(path)
    return path
