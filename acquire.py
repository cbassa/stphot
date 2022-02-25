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
    parser.add_argument("-s", "--settings", help="JSON file with settings", default="settings.json")
    parser.add_argument("-p", "--path", help="Output path", default=None)
    parser.add_argument("-t", "--exptime", help="Exposure time [seconds]", type=float, default=None)
    parser.add_argument("-g", "--gain", help="Gain", type=int, default=None)
    parser.add_argument("-b", "--bin", help="Binning factor", type=int, default=None)
    parser.add_argument("-n", "--number", help="Number of images to acquire", type=int, default=None)
    parser.add_argument("-F", "--format", help="Data format [RAW8, RAW16, RGB24]", default=None)
    parser.add_argument("-l", "--live", action="store_true", help="Display live image while capturing")
    parser.add_argument("-w", "--wait", help="Wait time between exposures [seconds]", type=float, default=0)
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

    # Override settings
    if args.exptime is not None:
        settings["exposure"] = f"{int(float(args.exptime) * 1000)}"
    if args.gain is not None:
        settings["gain"] = f"{args.gain}"
    if args.bin is not None:
        settings["bin"] = f"{args.bin}"
    if args.format is not None:
        if args.format == "RAW8":
            settings["type"] = f"{asi.ASI_IMG_RAW8}"
        elif args.format == "RAW16":
            settings["type"] = f"{asi.ASI_IMG_RAW16}"
        elif args.format == "RGB24":
            settings["type"] = f"{asi.ASI_IMG_RGB24}"

    # Number of images
    if args.number is not None:
        nimg = args.number
    else:
        nimg = 6
    

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
    camera.set_control_value(asi.ASI_GAIN, gain, auto=False)
    camera.set_control_value(asi.ASI_WB_B, int(settings["wbb"]))
    camera.set_control_value(asi.ASI_WB_R, int(settings["wbr"]))
    camera.set_control_value(asi.ASI_GAMMA, int(settings["gamma"]))
    camera.set_control_value(asi.ASI_BRIGHTNESS, int(settings["brightness"]))
    camera.set_control_value(asi.ASI_FLIP, int(settings["flip"]))
    camera.set_control_value(asi.ASI_AUTO_MAX_BRIGHTNESS, 80)
    camera.disable_dark_subtract()
    camera.set_roi(bins=int(settings["bin"]))

    # Force any single exposure to be halted
    try:
        camera.stop_video_capture()
        camera.stop_exposure()
    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        pass
    
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
    for i in range(nimg):
        print(f"Capturing image {i} of {nimg}")
        # Capture frame
        t0 = time.time()
        img = camera.capture()
        
        # Display Frame
        if args.live is True:
            cv2.imshow("Capture", img)
            cv2.waitKey(1)
        
        # Get settings
        camera_settings = camera.get_control_values()
        
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

        #print(settings["type"], asi.ASI_IMG_RAW8, asi.ASI_IMG_RGB24, asi.ASI_IMG_RAW16)
        
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
        cv2.imwrite(os.path.join(path, "%s.jpg" % nfd), rgb_img)

        # Wait
        if args.wait > 0:
            time.sleep(args.wait)

    # Stop capture
    camera.stop_video_capture()

    # Release device
    if args.live is True:
        cv2.destroyAllWindows()
