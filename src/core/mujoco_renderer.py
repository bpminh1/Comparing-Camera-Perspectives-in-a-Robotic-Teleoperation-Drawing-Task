import numpy as np
import mujoco
import mujoco.viewer
import cv2

class MujocoRenderer:
    '''This class handles rendering of the mujoco simulation. 
    It can render the scene in a window or offscreen, and allows for drawing lines and setting images/text in the viewer.
    '''

    def __init__(self, spec, model, width=2560, height=1920, show_window=True):
        self.spec = spec
        self.model = model
        self.width = width
        self.height = height
        self.current_key_handler = None

        self.show_window = show_window
        if show_window:
            self.viewer = None
            self.data = None
        else:
            self.renderer = mujoco.Renderer(model, width=width, height=height)
    
    def close(self):
        '''Closes the viewer or renderer to free up resources.'''
        if self.show_window and self.viewer is not None:
            self.viewer.close()
            self.viewer = None
        elif not self.show_window and hasattr(self, 'renderer') and self.renderer is not None:
            self.renderer.close()

    def add_visual_marker(self, scn, point1, point2, radius, rgba):
        '''Adds a visual marker (capsule) between two points in the scene.'''
        if scn.ngeom >= scn.maxgeom:
            return
        
        scn.ngeom += 1
        geom = scn.geoms[scn.ngeom-1]

        # Initialize the geometry as a capsule between point1 and point2
        mujoco.mjv_initGeom(
            geom,
            mujoco.mjtGeom.mjGEOM_CAPSULE,
            np.zeros(3), 
            np.zeros(3),  
            np.zeros(9), 
            rgba.astype(np.float32)
        )
        # Set the capsule parameters (radius and endpoints)
        mujoco.mjv_connector(
            geom,
            mujoco.mjtGeom.mjGEOM_CAPSULE,
            radius,
            point1.astype(np.float32),
            point2.astype(np.float32)
        )

        geom.emission = 1.0   # full brightness
        geom.specular = 0.0   # no specular highlights
        geom.shininess = 0.0  # no shininess for a matte look

    def draw_line(self, scn, points, radius=0.002, rgba=np.array([1, 0, 0, 1])):
        '''Draws a line connecting the given points in the scene using visual markers (capsules).'''
        if not points:
            return
        for line in points:
            if len(line) < 2:
                if len(line) == 1:
                    self.add_visual_marker(scn, np.array(line[0]), np.array(line[0]), radius, rgba)
            else:
                for i in range(len(line) - 1):
                    self.add_visual_marker(scn, np.array(line[i]), np.array(line[i+1]), radius, rgba)
    
    def prepare_trial_conditions(self, material_name, camera, key_callback):
        '''Prepares the trial conditions by setting the material, camera, and key callback for the viewer.'''
        self.set_material(material_name)
        self.set_camera(camera)
        self.set_key_callback(key_callback)

        if self.viewer is not None:
            self.viewer.user_scn.ngeom = 0
            self.viewer.sync()

    def set_material(self, material_name):
        '''Sets the material of the target shape on the canvas in the mujoco scene.'''
        geom_id = mujoco.mj_name2id(
            self.model, mujoco.mjtObj.mjOBJ_GEOM, "canvas"
        )

        mat_id = mujoco.mj_name2id(
            self.model, mujoco.mjtObj.mjOBJ_MATERIAL, material_name
        )

        self.model.geom_matid[geom_id] = mat_id

    def set_camera(self, camera):
        '''Sets the camera view in the mujoco viewer.'''
        if self.viewer is not None:
            self.viewer.cam.type = mujoco.mjtCamera.mjCAMERA_FIXED
            self.viewer.cam.fixedcamid = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_CAMERA, camera)

    def launch_viewer(self, data, key_callback=None):
        '''Launches the mujoco viewer with the given data and key callback. If a viewer is already running, it will be closed first.'''
        # Always close existing viewer first
        self.close()
        
        self.data = data
        self.current_key_handler = key_callback
        self.viewer = mujoco.viewer.launch_passive(
            self.model, self.data, 
            key_callback=self._key_callback_wrapper, 
            show_left_ui=True, show_right_ui=False
        ).__enter__()

    def is_viewer_running(self):
        '''Checks if the viewer is currently running.'''
        return self.viewer is not None and self.viewer.is_running()
    
    def render_offscreen(self, data, drawn_points, moved_points=None):
        '''Renders the scene offscreen and returns the image.'''
        self.data = data
        mujoco.mj_forward(self.model, self.data)

        # Reset user scene geometry
        self.renderer.update_scene(data, camera='top')
        self.renderer.scene.ngeom = self.model.ngeom
        
        # Add drawn lines and moved points to the scene
        self.draw_line(self.renderer.scene, drawn_points)
        if moved_points is not None:
            self.draw_line(self.renderer.scene, moved_points, radius=0.002, rgba=np.array([0, 0, 0, 1]))

        # Render the scene
        img = self.renderer.render()
        img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        return img_bgr

    def render_scene(self, data, drawn_points):
        '''Renders the scene in the viewer window.'''
        if self.show_window and self.viewer is None:
            raise RuntimeError("Viewer not launched. Call launch_viewer() first.")
        
        try:
            self.data = data
            mujoco.mj_forward(self.model, self.data)

            # Reset user scene geometry and add drawn lines
            self.viewer.user_scn.ngeom = 0
            self.draw_line(self.viewer.user_scn, drawn_points)
            
            # Sync viewer
            self.viewer.sync()
            
        except Exception as e:
            print(f"Rendering error: {e}")

    def set_image(self, img_path):
        '''Sets an image in the viewer window. 
        The image is resized to fit the viewport. 
        This can be used to display the instruction slides.
        '''
        img = cv2.imread(img_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        viewport = self.viewer.viewport
        img = cv2.resize(img, (viewport.width, viewport.height)) 

        self.viewer.set_images((viewport, img))

    def clear_image(self):
        '''Clears the image from the viewer window.'''
        self.viewer.clear_images()

    def set_text(self, text1, text2=None):
        '''Sets text in the viewer window.'''
        self.viewer.set_texts((None, None, text1, text2))

    def clear_text(self):
        '''Clears text from the viewer window.'''
        self.viewer.clear_texts()

    def _key_callback_wrapper(self, keycode):
        '''Internal wrapper for key callbacks. 
        This allows us to delegate key events to a custom handler later.
        '''
        if self.current_key_handler is not None:
            self.current_key_handler(keycode)

    def set_key_callback(self, new_callback):
        '''Sets a new key callback function for the viewer. 
        This allows us to change the key handling behavior dynamically during the experiment.
        '''
        self.current_key_handler = new_callback