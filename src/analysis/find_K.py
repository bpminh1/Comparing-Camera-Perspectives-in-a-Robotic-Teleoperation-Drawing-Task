import cv2
import numpy as np
import glob
import os
import json

def calibrate_camera(images_path, checkerboard_size=(9,6), square_size=0.6):
    """
    Calibrate camera using checkerboard images.
    Returns: K, dist, rvecs, tvecs
    """
    # 3D points in checkerboard coordinate system
    objp = np.zeros((checkerboard_size[0]*checkerboard_size[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:checkerboard_size[0], 0:checkerboard_size[1]].T.reshape(-1,2)
    objp *= square_size

    objpoints = []
    imgpoints = []

    images = glob.glob(f"{images_path}/*.jpg")
    first_gray = None

    for fname in images:
        img = cv2.imread(fname)
        if img is None:
            continue  # skip unreadable images
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        ret, corners = cv2.findChessboardCorners(gray, checkerboard_size, None)
        if ret:
            if first_gray is None:
                first_gray = gray  # store the first valid gray image
            objpoints.append(objp)
            corners2 = cv2.cornerSubPix(
                gray, corners, (11,11), (-1,-1),
                criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            )
            imgpoints.append(corners2)

    if not objpoints:
        raise RuntimeError(
            "No checkerboard corners found in any image! "
            "Check your images, checkerboard size, and square size."
        )

    ret, K, dist, rvecs, tvecs = cv2.calibrateCamera(
        objpoints, imgpoints, first_gray.shape[::-1], None, None
    )

    return K, dist, rvecs, tvecs

def find_camera_offset(K, dist, object_points, image_points):
    '''Estimates the camera's position and orientation relative to the workspace using the camera intrinsic matrix (K).'''
    ok, rvec, tvec = cv2.solvePnP(object_points, image_points, K, dist, flags=cv2.SOLVEPNP_IPPE)
    if not ok:
        return []
    
    proj, _ = cv2.projectPoints(object_points, rvec, tvec, K, dist)
    
    # Convert rotation vector to rotation matrix
    R, _ = cv2.Rodrigues(rvec)
    # Get the camera position relative to the workspace in real-world coordinates
    R = R.T
    tvec = -R @ tvec.reshape(3, 1)

    #Convert rotation to Euler angles
    sy = np.sqrt(R[0,0]**2 + R[1,0]**2)
    singular = sy < 1e-6
    if not singular:
        x_angle = np.arctan2(R[2,1], R[2,2])
        y_angle = np.arctan2(-R[2,0], sy)
        z_angle = np.arctan2(R[1,0], R[0,0])
    else:
        x_angle = np.arctan2(-R[1,2], R[1,1])
        y_angle = np.arctan2(-R[2,0], sy)
        z_angle = 0

    return {
                'object points': object_points,
                'camera points': image_points,
                'project points': proj,
                'K': K,
                'dist': dist,
                'x_angle_deg': np.degrees(x_angle),
                'y_angle_deg': np.degrees(y_angle),
                'z_angle_deg': np.degrees(z_angle),
                'translation': tvec.flatten()
            }

object_points = np.array([
    [40,40,0],
    [40,0,0],
    [0,40,0],
    [0,0,0]
  ], dtype=np.float32)

image_points = np.array([
    [230,164],
    [33,191],
    [278,318],
    [46,366]
  ], dtype=np.float32)

@staticmethod
def to_serializable(obj):
    '''Helper method to convert non-serializable objects (like numpy arrays) into serializable formats (like lists).'''
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.float32, np.float64)):
        return float(obj)
    if isinstance(obj, (np.int32, np.int64)):
        return int(obj)
    return obj

def save_camera_calibration(camera_positions):
    '''Saves the camera calibration data.'''
    calibration_folder = '/Users/minhbui/Desktop/Thesis/src/analysis/calibration_images'
    calibration_file = os.path.join(calibration_folder, 'calibration.json')
    with open(calibration_file, 'w') as f:
        json.dump(camera_positions, f, indent=2, default=to_serializable)

K, dist, _, _ = calibrate_camera('/Users/minhbui/Desktop/Thesis/src/analysis/calibration_images')
m = find_camera_offset(K, dist, object_points, image_points)
save_camera_calibration(m)