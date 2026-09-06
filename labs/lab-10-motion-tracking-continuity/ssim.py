#!/usr/bin/env python3
"""Lab 05 — structural similarity index, implemented in NumPy + OpenCV.

The base `opencv-python` wheel does not ship the `cv2.quality` module (it is in
`opencv-contrib-python`), so the course carries its own implementation rather
than adding a dependency for a single function.

SSIM(x, y) = ((2*mu_x*mu_y + C1)(2*sigma_xy + C2))
             / ((mu_x^2 + mu_y^2 + C1)(sigma_x^2 + sigma_y^2 + C2))

with C1 = (0.01 * L)^2, C2 = (0.03 * L)^2 and L = 255, computed over a sliding
Gaussian window (11x11, sigma 1.5 — the window from the original SSIM paper).
"""
import cv2
import numpy as np

C1 = (0.01 * 255.0) ** 2
C2 = (0.03 * 255.0) ** 2


def _ssim_gray(a, b, win=11, sigma=1.5):
    a = a.astype(np.float64)
    b = b.astype(np.float64)
    ksize = (win, win)

    mu_a = cv2.GaussianBlur(a, ksize, sigma)
    mu_b = cv2.GaussianBlur(b, ksize, sigma)
    mu_a2, mu_b2, mu_ab = mu_a * mu_a, mu_b * mu_b, mu_a * mu_b

    sigma_a2 = cv2.GaussianBlur(a * a, ksize, sigma) - mu_a2
    sigma_b2 = cv2.GaussianBlur(b * b, ksize, sigma) - mu_b2
    sigma_ab = cv2.GaussianBlur(a * b, ksize, sigma) - mu_ab

    num = (2 * mu_ab + C1) * (2 * sigma_ab + C2)
    den = (mu_a2 + mu_b2 + C1) * (sigma_a2 + sigma_b2 + C2)
    return float(np.mean((num / den)[5:-5,5:-5]))  # valid 11x11 windows; exclude padded border


def ssim(a, b):
    """Mean SSIM between two same-shape uint8 images (grayscale or BGR)."""
    if a.dtype != np.uint8 or b.dtype != np.uint8 or a.ndim not in (2,3) or min(a.shape[:2]) < 11:
        raise ValueError("require uint8 grayscale/BGR images at least 11x11")
    if a.shape != b.shape:
        raise ValueError(f"shape mismatch: {a.shape} vs {b.shape}")
    if a.ndim == 2:
        return _ssim_gray(a, b)
    return float(np.mean([_ssim_gray(a[:, :, c], b[:, :, c]) for c in range(a.shape[2])]))


def psnr(a, b):
    """PSNR in dB, computed from the formula (cross-check against cv2.PSNR)."""
    if a.shape != b.shape or a.dtype != np.uint8 or b.dtype != np.uint8:
        raise ValueError("PSNR requires same-shape uint8 images")
    mse = np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2)
    if mse == 0:
        return float("inf")
    return float(10.0 * np.log10(255.0 ** 2 / mse))


if __name__ == "__main__":
    # Self-test: an image against itself is SSIM 1.0 and PSNR inf.
    rng = np.random.default_rng(0)
    img = rng.integers(0, 256, (64, 64, 3), dtype=np.uint8)
    print("self SSIM", round(ssim(img, img), 6))
    print("self PSNR", psnr(img, img))
    blurred = cv2.GaussianBlur(img, (5, 5), 0)
    print("blur SSIM", round(ssim(img, blurred), 4),
          "PSNR", round(psnr(img, blurred), 2),
          "cv2.PSNR", round(cv2.PSNR(img, blurred), 2))
