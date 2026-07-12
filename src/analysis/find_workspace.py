from matplotlib import patches
import numpy as np
import franka_ik
import matplotlib.pyplot as plt
import os

valid_points = []
z = 0.4  # fixed height
for x in np.linspace(0.0, 2.0, 1000):
    for y in np.linspace(-2.0, 2.0, 1000):
        O_T_EE = np.array([
            [1,  0,  0, x],
            [0, -0.9, 0, y],
            [0,  0, -1, z],
            [0,  0,  0, 1]
        ])
        q7 = 0.7
        q_actual_array = [0.0] * 7
        O_T_EE_array = O_T_EE.T.flatten().tolist()
        solutions = franka_ik.franka_IK_EE(O_T_EE_array, q7, q_actual_array)
        if any(not any(np.isnan(sol)) for sol in solutions):
            valid_points.append((x, y))

# Find min/max x/y from valid_points
workspace_x_min = min(p[0] for p in valid_points)
workspace_x_max = max(p[0] for p in valid_points)
workspace_y_min = min(p[1] for p in valid_points)
workspace_y_max = max(p[1] for p in valid_points)

print(f"Workspace boundaries:")
print(f"x: {workspace_x_min:.2f} to {workspace_x_max:.2f}")
print(f"y: {workspace_y_min:.2f} to {workspace_y_max:.2f}")

# Plot valid points
xs, ys = zip(*valid_points)
plt.scatter(xs, ys, s=2)
plt.xlabel('x')
plt.ylabel('y')
plt.title('Valid Workspace Points')

# Add canvas rectangle
canvas_center_x = 0.35
canvas_center_y = 0.0
canvas_half_width = 0.2
canvas_half_height = 0.2

rect = patches.Rectangle(
    (canvas_center_x - canvas_half_width, canvas_center_y - canvas_half_height),
    2 * canvas_half_width, 2 * canvas_half_height,
    linewidth=2, edgecolor='g', facecolor='none', label='Canvas'
)
plt.gca().add_patch(rect)
plt.gca().set_aspect('equal')
plt.legend()
os.makedirs(os.path.join('data', 'images'), exist_ok=True)
plt.savefig(os.path.join('data', 'images', 'workspace2.png'))