import io
import qrcode
from fastapi.responses import StreamingResponse

from app.config import settings


def generate_qr_code(serial_number: str) -> StreamingResponse:
    """Generate a QR code PNG image for a device, linking to its detail page."""
    url = f"{settings.APP_URL}/devices/{serial_number}"

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    return StreamingResponse(buf, media_type="image/png",
                             headers={"Content-Disposition": f"inline; filename=qr_{serial_number}.png"})
