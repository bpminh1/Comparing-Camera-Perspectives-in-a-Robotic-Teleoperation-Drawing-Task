import numpy as np
import franka_ik

class RobotController:
    '''This class handles the control of the robot arm in the mujoco simulation.
    It takes the detected hand positions from the HandTracker, calculates the corresponding end-effector position in the workspace, and uses inverse kinematics to compute the joint angles for the robot arm.
    '''

    def __init__(self, data, workspace_bounds):
        self.data = data
        self.workspace_x_min, self.workspace_x_max, self.workspace_y_min, self.workspace_y_max = workspace_bounds

        # Define the input for the IK solver (O_T_EE, q7 and q_actual_array)
        self.O_T_EE = np.array([
            [1,  0,  0, 0],
            [0, -0.9, 0, 0],
            [0,  0, -1, 0],
            [0,  0,  0, 1]
        ])
        self.q7 = 0.7
        self.q_actual_array = [0.0] * 7

    def calculate_ik(self, target_x, target_y, z):
        '''Calculates the inverse kinematics for the robot arm based on the target end-effector position derived from the detected hand position.'''
        # Validate input positions
        if not (self.workspace_x_min <= target_x <= self.workspace_x_max):
            return False
        if not (self.workspace_y_min <= target_y <= self.workspace_y_max):
            return False
        if not (0.1 <= z <= 0.8):  # Reasonable z bounds
            return False
        
        try:
            # Set target position from finger position
            self.O_T_EE[:3, 3] = [target_x, target_y, z]
            O_T_EE_array = self.O_T_EE.T.flatten().tolist()

            # Compute IK
            solutions = franka_ik.franka_IK_EE(O_T_EE_array, self.q7, self.q_actual_array)
            valid_solution = next((sol for sol in solutions if not any(np.isnan(sol))), None)
            
            if valid_solution is not None:
                # Validate solution before applying
                if len(valid_solution) >= 7:
                    # Update arm's positions
                    self.data.qpos[:7] = valid_solution[:7]
                    self.data.qpos[7:] = [0.0, 0.0]  # Gripper closed
                    return True
        except Exception as e:
            print(f"IK calculation error: {e}")
            return False
        
        return False