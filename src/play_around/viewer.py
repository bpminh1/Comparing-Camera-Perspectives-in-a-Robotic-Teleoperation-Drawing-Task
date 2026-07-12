import mujoco
import mediapy as media
import numpy as np
import mujoco.viewer

xml = 'third_party/franka_emika_panda/scene.xml'
model = mujoco.MjModel.from_xml_path(xml)
data = mujoco.MjData(model)
camera = mujoco.MjvCamera()
mujoco.mjv_defaultFreeCamera(model, camera)
camera.distance = 2.5

# mujoco.viewer.launch(model, data)

# Define target position
target_qpos = np.array([1, -0.785, 0, -2.356, 0, 1.571, 0.785, 0.23])

# Launch interactive viewer
with mujoco.viewer.launch_passive(model, data) as viewer:
    # Reset simulation
    mujoco.mj_resetData(model, data)
    
    # Run simulation
    while viewer.is_running():
        # Set control target
        data.ctrl[:] = target_qpos
        
        # Step simulation
        mujoco.mj_step(model, data)
        
        # Sync viewer
        viewer.sync()