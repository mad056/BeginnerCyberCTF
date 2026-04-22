"""Generate binary challenge assets: JPEG with EXIF, XLSX with hidden sheet, QR code."""
import os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
CHALLENGES = os.path.join(BASE, "..", "challenges")


def make_jpeg():
    """Create a JPEG with flag in EXIF UserComment."""
    from PIL import Image
    import piexif

    path = os.path.join(CHALLENGES, "07-metadata", "assets", "photo.jpg")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img = Image.new("RGB", (400, 300), color=(15, 23, 42))
    img.save(path, "JPEG")

    exif_dict = piexif.load(path)
    exif_dict["Exif"][piexif.ExifIFD.UserComment] = piexif.helper.UserComment.dump(
        "flag{metadata_tells_the_truth}", encoding="unicode"
    )
    piexif.insert(piexif.dump(exif_dict), path)
    print(f"  ✓ {path}")


def make_jpeg_simple():
    """Fallback: embed flag in JPEG comment via Pillow only."""
    from PIL import Image
    path = os.path.join(CHALLENGES, "07-metadata", "assets", "photo.jpg")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img = Image.new("RGB", (400, 300), color=(15, 23, 42))
    from PIL.JpegImagePlugin import JpegImageFile
    img.save(path, "JPEG")

    # Write JPEG COM marker manually
    flag = b"flag{metadata_tells_the_truth}"
    with open(path, "rb") as f:
        data = f.read()
    # Insert COM marker (0xFFFE) after SOI (0xFFD8)
    com = b"\xff\xfe" + len(flag + b"\x00").to_bytes(2, "big") + flag + b"\x00"
    data = data[:2] + com + data[2:]
    with open(path, "wb") as f:
        f.write(data)
    print(f"  ✓ {path} (COM marker)")


def make_xlsx():
    """Create an Excel file with a hidden worksheet containing the flag."""
    from openpyxl import Workbook
    from openpyxl.worksheet.worksheet import Worksheet

    path = os.path.join(CHALLENGES, "08-hidden-sheet", "assets", "budget.xlsx")
    os.makedirs(os.path.dirname(path), exist_ok=True)

    wb = Workbook()
    ws1 = wb.active
    ws1.title = "Q1 Budget"
    ws1["A1"] = "Department"
    ws1["B1"] = "Budget"
    ws1["A2"] = "Marketing"
    ws1["B2"] = 50000
    ws1["A3"] = "Engineering"
    ws1["B3"] = 120000
    ws1["A4"] = "HR"
    ws1["B4"] = 30000

    ws_hidden = wb.create_sheet("Secret")
    ws_hidden["A1"] = "flag{always_check_hidden_sheets}"
    ws_hidden.sheet_state = "hidden"

    wb.save(path)
    print(f"  ✓ {path}")


def make_qr():
    """Create a QR code decoy and place it where challenge routes can serve it."""
    import qrcode

    assets_path = os.path.join(CHALLENGES, "10-qr-osint", "assets", "qr.png")
    static_path = os.path.join(
        BASE, "..", "plugins", "challenge_routes", "static", "challenges", "10", "qr.png"
    )
    os.makedirs(os.path.dirname(assets_path), exist_ok=True)
    os.makedirs(os.path.dirname(static_path), exist_ok=True)

    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    qr = qrcode.make(url)
    qr.save(assets_path)
    qr.save(static_path)
    print(f"  ✓ {assets_path}")
    print(f"  ✓ {static_path}")


if __name__ == "__main__":
    print("Generating challenge assets...")

    # JPEG
    try:
        make_jpeg()
    except ImportError:
        make_jpeg_simple()

    # XLSX
    make_xlsx()

    # QR
    make_qr()

    print("Done.")
