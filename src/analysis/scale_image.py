import cv2
import os

def scale_image(image_folder):
    '''Scales and rotates images in the given folder, saving the processed images to the target directory.'''
    for path in os.listdir(image_folder):
        if path.endswith('.png'):
            image_path = os.path.join(image_folder, path)
            shape = os.path.basename(image_path)
            save_path = os.path.join('third_party', 'franka_emika_panda', 'assets', 'target_shapes', shape)

            # Load the image
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Failed to load image from {image_path}")

            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)

            # Save the processed image
            cv2.imwrite(save_path, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        
scale_image('/Users/minhbui/Desktop/Thesis/data/original_shapes')