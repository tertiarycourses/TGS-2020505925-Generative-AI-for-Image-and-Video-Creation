# Real prerecorded reference sequence

`vtest.avi` is a REAL recorded video sequence from the OpenCV sample data (https://github.com/opencv/opencv/blob/4.x/samples/data/vtest.avi), retrieved 6 September 2026. Its SHA-256 is recorded in `vtest-provenance.json` so the copy can be verified.

It is NOT generative-model output and NOT a rendered animation. It is included so the tracking measurements in this lab can be repeated on a real sequence as well as on the deterministic synthetic clip, and so the difference between the two is visible rather than asserted: the synthetic clip has exact per-frame ground truth, the real sequence does not.

OpenCV documentation for the mean shift / CAMShift tutorial that uses this file: https://docs.opencv.org/4.13.0/d7/d00/tutorial_meanshift.html
