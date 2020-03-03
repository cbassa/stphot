#!/usr/bin/env python3
import argparse
import os
import sys
import json
import time
import cv2
import zwoasi as asi
import numpy as np
from stphot.io import write_fits_file

if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Capture images with an ASI CMOS camera")
    parser.add_argument("-s", "--settings", help="JSON file with settings", default=None)
    parser.add_argument("-p", "--path", help="Output path", default=None)
    args = parser.parse_args()

    # Check arguments
    if args.settings == None or args.path == None:
        parser.print_help()
        sys.exit()
        
    # Read settings
    try:
        with open(args.settings, "r") as fp:
            settings = json.load(fp)
    except Exception as e:
        print(e)
        sys.exit(1)

    # Check path
    path = os.path.abspath(args.path)
    if not os.path.exists(path):
        os.makedirs(path)

    # Intialize SDK library
    try:
        asi.init(os.getenv("ZWO_ASI_LIB"))
    except Exception as e:
        print(e)
        sys.exit(1)

    # Find cameras
    ncam = asi.get_num_cameras()
    if ncam == 0:
        print("No ZWO ASI cameras found")
        sys.exit(1)

    # Decode settings
    texp_us = 1000 * int(settings["exposure"])
    gain = int(settings["gain"])

    # Initialize camera 0
    camera = asi.Camera(0)
    camera_info = camera.get_camera_property()

    # Set control values
    camera.set_control_value(asi.ASI_BANDWIDTHOVERLOAD, int(settings["usb"]))
    camera.set_control_value(asi.ASI_EXPOSURE, texp_us, auto=False)
    #camera.set_control_value(asi.ASI_AUTO_MAX_EXP, texp_us_max // 1000)
    camera.set_control_value(asi.ASI_GAIN, gain, auto=False)
    #camera.set_control_value(asi.ASI_AUTO_MAX_GAIN, gain_max)
    camera.set_control_value(asi.ASI_WB_B, int(settings["wbb"]))
    camera.set_control_value(asi.ASI_WB_R, int(settings["wbr"]))
    camera.set_control_value(asi.ASI_GAMMA, int(settings["gamma"]))
    camera.set_control_value(asi.ASI_BRIGHTNESS, int(settings["brightness"]))
    camera.set_control_value(asi.ASI_FLIP, int(settings["flip"]))
    camera.set_control_value(asi.ASI_AUTO_MAX_BRIGHTNESS, 80)
    camera.disable_dark_subtract()
    camera.set_roi(bins=int(settings["bin"]))

    # Start capture
    camera.start_video_capture()

    # Set image format
    if int(settings["type"]) == asi.ASI_IMG_RAW8:
        camera.set_image_type(asi.ASI_IMG_RAW8)
    elif int(settings["type"]) == asi.ASI_IMG_RGB24:
        camera.set_image_type(asi.ASI_IMG_RGB24)
    elif int(settings["type"]) == asi.ASI_IMG_RAW16:
        camera.set_image_type(asi.ASI_IMG_RAW16)
    else:
        camera.set_image_type(asi.ASI_IMG_RAW8)
    
    # Forever loop
    for i in range(12):
        # Capture frame
        t0 = time.time()
        img = camera.capture_video_frame()
        
        # Get settings
        camera_settings = camera.get_control_values()

        # Stability test
        if texp_us == camera_settings["Exposure"] and gain == camera_settings["Gain"]:
            stable = True

        # Extract settings
        texp_us = camera_settings["Exposure"]
        texp = float(texp_us) / 1000000
        gain = camera_settings["Gain"]
        temp = float(camera_settings["Temperature"]) / 10

        # Format start time
        nfd = "%s.%03d" % (time.strftime("%Y-%m-%dT%T",
                           time.gmtime(t0)), int((t0 - np.floor(t0)) * 1000))

        print(nfd, texp, gain, temp)
        
        # Store FITS file
        write_fits_file(os.path.join(path, "%s.fits" % nfd), np.flipud(img), nfd, texp, gain, temp)
            
        # Get RGB image
        if int(settings["type"]) == asi.ASI_IMG_RAW8:
            ny, nx = img.shape
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BAYER_BG2BGR)
        elif int(settings["type"]) == asi.ASI_IMG_RGB24:
            ny, nx, nc = img.shape
            rgb_img = img
        elif int(settings["type"]) == asi.ASI_IMG_RAW16:
            ny, nx = img.shape
            img_8bit = np.clip((img/256).astype("uint8"), 0, 255)
            rgb_img = cv2.cvtColor(img_8bit, cv2.COLOR_BAYER_BG2BGR)

        # Store image
        if stable:
            cv2.imwrite(os.path.join(path, "%s.jpg" % nfd), rgb_img)

    # Stop capture
    camera.stop_video_capture()

