# Binary mask conventions

## The convention used in this lab

A mask is a **single-channel 8-bit image** (`CV_8UC1`, `dtype=uint8`) the same
height and width as the image it applies to.

| Value | Meaning |
|---|---|
| **255 (white)** | **EDITABLE** — the model or filter may rewrite these pixels |
| **0 (black)** | **PRESERVED** — these pixels must survive unchanged |

`cv2.inpaint` follows this convention: it repairs where the mask is non-zero.

## Why this is worth stating explicitly

Mask semantics are not universal across tools. Some editors ship an "inverted"
selection by default, and some APIs describe the mask as the *retain* region
rather than the *edit* region. An inverted mask does not error — it produces a
confidently wrong image, and the failure is only visible on inspection.

**Rule:** every edit specification in this course records its mask semantics as
an explicit field, and every edit is verified by measuring change inside and
outside the mask rather than by assuming containment.

## Building a good mask

1. **Threshold on a property that survives the variation you expect.** Hue can remain stable under synthetic V scaling, but thresholds, noise, clipping and white balance can still invalidate segmentation.
2. **Close before you dilate.** `cv2.MORPH_CLOSE` fills pinholes left by
   compression noise; dilation then grows the mask a few pixels past the object
   boundary so the fill can blend.
3. **A mask cut exactly on the boundary leaves a halo.** Two or three pixels of
   dilation is usually enough; more starts eating the surroundings.
4. **Check coverage.** A price-tag mask should be a low single-digit percentage
   of the frame. If it is 30%, the threshold band is catching the product.

## Verifying an edit

    inside  = mean |original - result| over mask > 0     # should be clearly non-zero
    outside = mean |original - result| over mask == 0    # should be effectively zero

An outside value above about 0.5/255 means the edit was not contained.
