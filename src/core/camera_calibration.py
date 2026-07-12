import cv2
import numpy as np

class CameraCalibration:
    '''This class handles the camera calibration process for a workspace. 
    It allows the user to click on the corners of the workspace in the camera feed, 
    computes the homography matrix, and estimates the camera's position and orientation relative to the workspace.
    '''

    def __init__(self):
        self.camera_width = None
        self.camera_height = None

        self.object_points = None
        self.camera_points = None

        self.H = None

    def calibrate_workspace(self, cap):
        '''Calibrates the workspace by allowing the user to click on the corners of the workspace in the camera feed.
        The method computes the homography matrix (H) that maps the camera coordinates to the workspace coordinates.
        '''
        # Define the workspace corners in the object coordinate system (in cm)
        self.object_points = np.array([
            [40, 40], # top-right
            [40, 0], # bottom-right
            [0, 40], # top-left
            [0, 0] # bottom-left
        ])

        # Get the corresponding camera coordinates
        self.camera_points = self._find_camera_coordinates(cap)

        # Compute the homography matrix (H) that maps the camera coordinates to the workspace coordinates
        self.H, _ = cv2.findHomography(np.array(self.camera_points, dtype=np.float32), 
                                        np.array(self.object_points, dtype=np.float32))
        
        return self.camera_width, self.camera_height, self.H
        
    def _find_camera_coordinates(self, cap):
        '''Captures the camera feed and allows the user to click on the corners of the workspace.'''
        cv2.namedWindow('Calibration', cv2.WINDOW_NORMAL)
        print("Click on the 4 corners of the workspace in the following order:")
        print("1. Top-left")
        print("2. Bottom-left")
        print("3. Top-right")
        print("4. Bottom-right")

        points = []

        def mouse_callback(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN and len(points) < 4:
                points.append((x, y))
        cv2.setMouseCallback('Calibration', mouse_callback)

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            img = frame.copy()

            if self.camera_height is None:
                self.camera_height, self.camera_width = frame.shape[:2]
            
            # Draw the clicked points and their indices on the image
            for i, pt in enumerate(points):
                cv2.circle(img, pt, 8, (0, 255, 0), -1)
                cv2.putText(img, f'{i+1}', (pt[0]+15, pt[1]-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
            cv2.imshow('Calibration', img)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                cv2.destroyWindow('Calibration')
                return points
            elif key == ord('r'):
                points.clear()
        
        return None
    
    def _find_K(self):
        '''Calculates the camera intrinsic matrix (K) based on the camera specifications.'''
        # Camera specs
        horizontal_fov = 70.42  # degrees
        vertical_fov = 43.3     # degrees
        # Calculate focal length in pixels
        fx = (self.camera_width / 2) / np.tan(np.radians(horizontal_fov / 2))
        fy = (self.camera_height / 2) / np.tan(np.radians(vertical_fov / 2))

        # Camera intrinsic matrix
        K = np.array([
            [fx, 0, self.camera_width/2],
            [0, fy, self.camera_height/2],
            [0, 0, 1]
        ], dtype=np.float32)

        return K
    
    def find_camera_offset(self):
        '''Estimates the camera's position and orientation relative to the workspace using the camera intrinsic matrix (K).'''
        K = self._find_K()

        object_points = np.hstack([
            self.object_points,
            np.zeros((4,1))
        ]).astype(np.float32)
        image_points = np.array(self.camera_points, dtype=np.float32)

        ok, rvec, tvec = cv2.solvePnP(object_points, image_points, K, None, flags=cv2.SOLVEPNP_ITERATIVE)
        if not ok:
            return []
        
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
                    'object points': self.object_points,
                    'camera points': self.camera_points,
                    'H': self.H,
                    'K': K,
                    'camera width': self.camera_width,
                    'camera height': self.camera_height,
                    'x_angle_deg': np.degrees(x_angle),
                    'y_angle_deg': np.degrees(y_angle),
                    'z_angle_deg': np.degrees(z_angle),
                    'translation': tvec.flatten()
                }