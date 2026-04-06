from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QColor, QGuiApplication, QImage, QLinearGradient, QPainter, QPainterPath, QPen


def draw_icon(size: int) -> QImage:
    image = QImage(size, size, QImage.Format_ARGB32)
    image.fill(0)

    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)

    margin = size * 0.08
    background_rect = QRectF(margin, margin, size - margin * 2, size - margin * 2)

    gradient = QLinearGradient(background_rect.topLeft(), background_rect.bottomRight())
    gradient.setColorAt(0.0, QColor("#16324f"))
    gradient.setColorAt(1.0, QColor("#0d1b2a"))

    painter.setPen(QPen(QColor("#244a6a"), max(2, int(size * 0.01))))
    painter.setBrush(gradient)
    painter.drawRoundedRect(background_rect, size * 0.12, size * 0.12)

    center = QPointF(size * 0.48, size * 0.50)
    ring_radius = size * 0.20
    painter.setPen(QPen(QColor("#f97316"), max(8, int(size * 0.03))))
    painter.setBrush(QColor(0, 0, 0, 0))
    painter.drawEllipse(center, ring_radius, ring_radius)

    painter.setPen(QPen(QColor("#fb923c"), max(5, int(size * 0.018))))
    painter.drawLine(QPointF(center.x(), center.y() - ring_radius - size * 0.05), QPointF(center.x(), center.y() - ring_radius * 0.55))
    painter.drawLine(QPointF(center.x(), center.y() + ring_radius * 0.55), QPointF(center.x(), center.y() + ring_radius + size * 0.05))
    painter.drawLine(QPointF(center.x() - ring_radius - size * 0.05, center.y()), QPointF(center.x() - ring_radius * 0.55, center.y()))
    painter.drawLine(QPointF(center.x() + ring_radius * 0.55, center.y()), QPointF(center.x() + ring_radius + size * 0.05, center.y()))

    painter.setPen(QPen(QColor("#fff7ed"), max(4, int(size * 0.014))))
    painter.setBrush(QColor("#fff7ed"))
    painter.drawEllipse(center, size * 0.045, size * 0.045)

    cursor = QPainterPath()
    cursor.moveTo(size * 0.52, size * 0.24)
    cursor.lineTo(size * 0.72, size * 0.66)
    cursor.lineTo(size * 0.62, size * 0.66)
    cursor.lineTo(size * 0.68, size * 0.82)
    cursor.lineTo(size * 0.59, size * 0.86)
    cursor.lineTo(size * 0.53, size * 0.70)
    cursor.lineTo(size * 0.45, size * 0.78)
    cursor.closeSubpath()

    painter.setPen(QPen(QColor("#fff7ed"), max(3, int(size * 0.01))))
    painter.setBrush(QColor("#fff7ed"))
    painter.drawPath(cursor)

    painter.setPen(QPen(QColor("#fdba74"), max(5, int(size * 0.016))))
    painter.drawArc(QRectF(size * 0.68, size * 0.16, size * 0.14, size * 0.14), 30 * 16, 120 * 16)
    painter.drawArc(QRectF(size * 0.73, size * 0.10, size * 0.18, size * 0.18), 30 * 16, 120 * 16)

    painter.end()
    return image


def main() -> int:
    app = QGuiApplication([])
    assets_dir = Path(__file__).resolve().parent.parent / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    icon_image = draw_icon(512)
    png_path = assets_dir / "app_icon.png"
    ico_path = assets_dir / "app_icon.ico"

    if not icon_image.save(str(png_path), "PNG"):
        raise SystemExit("Failed to save PNG icon.")
    if not icon_image.save(str(ico_path), "ICO"):
        raise SystemExit("Failed to save ICO icon.")

    app.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
