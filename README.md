# STPHOT

**stphot** is a set of *python* programs to detect and identify satellite tracks on photographic observations of the night sky, and measure the satellite positions to determine and/or update their orbits.

## Implementation

1. Capture sequences of images from
   * DSLRs using `gphoto2` or similar
   * CCD/CMOS cameras using `INDI` or camera specific SDKs (e.g. `zwo-asi`)
2. Calibrate images using `astrometry.net` or the `stvid` approach
3. Overplot satellite predictions
4. Measure satellite positions manually (preferably automatically)
5. Format the positions as IOD output
6. Use `INDI` to control a computer controlled mount

