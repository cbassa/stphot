#!/usr/bin/env python3
import numpy as np
from astropy.time import Time
from astropy.io import fits

def write_fits_file(fname, img, nfd, texp, gain, temp):
    # Extract image shape and reorder in case of RGB24
    if len(img.shape)==3:
        ny, nx, nc = img.shape
        img = np.moveaxis(img, 2, 0)
    elif len(img.shape)==2:
        ny, nx = img.shape
        
    # FITS header
    hdr = fits.Header()
    hdr['DATE-OBS'] = "%s" % nfd
    hdr['MJD-OBS'] = Time(nfd, format="isot").mjd
    hdr['EXPTIME'] = texp
    hdr['GAIN'] = gain
    hdr['TEMP'] = temp
    hdr['CRPIX1'] = float(nx) / 2
    hdr['CRPIX2'] = float(ny) / 2
    hdr['CRVAL1'] = 0.0
    hdr['CRVAL2'] = 0.0
    hdr['CD1_1'] = 1.0 / 3600.0
    hdr['CD1_2'] = 0.0
    hdr['CD2_1'] = 0.0
    hdr['CD2_2'] = 1.0 / 3600.0
    hdr['CTYPE1'] = "RA---TAN"
    hdr['CTYPE2'] = "DEC--TAN"
    hdr['CUNIT1'] = "deg"
    hdr['CUNIT2'] = "deg"
    hdr['CRRES1'] = 0.0
    hdr['CRRES2'] = 0.0
    hdr['EQUINOX'] = 2000.0
    hdr['RADECSYS'] = "ICRS"
    hdr['COSPAR'] = 4171
    hdr['TRACKED'] = 0
    hdr['OBSERVER'] = "Cees Bassa"
    
    # Write FITS file
    hdu = fits.PrimaryHDU(data=img,
                          header=hdr)
    hdu.writeto(fname, overwrite=True)

    return
