"""Check rendered reports and create contact sheets for visual inspection."""

import json
from pathlib import Path

import fitz
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent


def main():
    output = ROOT / "artifacts/reports/previews"
    output.mkdir(parents=True, exist_ok=True)
    summary = []
    for number in range(5, 9):
        pdf = fitz.open(ROOT / f"reports/Lab_{number}.pdf")
        thumbs = []
        sparse_pages = []
        for index, page in enumerate(pdf):
            text = page.get_text()
            if len(text.strip()) < 80 and not page.get_images():
                sparse_pages.append(index + 1)
            pixmap = page.get_pixmap(matrix=fitz.Matrix(0.6, 0.6), alpha=False)
            img = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
            img.thumbnail((300, 425))
            thumb = Image.new("RGB", (320, 455), "#dddddd")
            thumb.paste(img, ((320 - img.width) // 2, 20))
            ImageDraw.Draw(thumb).text((8, 3), f"Lab {number} / page {index + 1}", fill="black")
            thumbs.append(thumb)
        for offset in range(0, len(thumbs), 12):
            batch = thumbs[offset : offset + 12]
            sheet = Image.new("RGB", (320 * 4, 455 * ((len(batch) + 3) // 4)), "white")
            for index, thumb in enumerate(batch):
                sheet.paste(thumb, (index % 4 * 320, index // 4 * 455))
            sheet.save(output / f"Lab_{number}-{offset // 12 + 1}.png")
        summary.append({"lab": number, "pages": len(pdf), "sparse_pages": sparse_pages})
        pdf.close()
    (ROOT / "docs/evidence/report-validation.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
