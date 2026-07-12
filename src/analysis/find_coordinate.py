import cv2

def find_canvas_coordinates(image_path):
    """Interactive tool to find canvas pixel coordinates"""
    img = cv2.imread(image_path)
    points = []
    
    def mouse_callback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            points.append((x, y))
            cv2.circle(img, (x, y), 5, (0, 255, 0), -1)
            cv2.putText(img, f"{len(points)}", (x+10, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            cv2.imshow('Find Canvas', img)
            print(f"Point {len(points)}: ({x}, {y})")
            
            if len(points) == 4:
                print("\nCanvas corners (top-left, top-right, bottom-right, bottom-left):")
                print(f"Top-left: {points[0]}")
                print(f"Top-right: {points[1]}")
                print(f"Bottom-right: {points[2]}")
                print(f"Bottom-left: {points[3]}")
    
    cv2.imshow('Find Canvas', img)
    cv2.setMouseCallback('Find Canvas', mouse_callback)
    print("Click on the 4 corners of the canvas: top-left, top-right, bottom-right, bottom-left")
    print("Press any key when done")
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    if len(points) == 4:
        # Calculate bounding box
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        print(f"\nBounding box: x=[{x_min}, {x_max}], y=[{y_min}, {y_max}]")
        return (x_min, y_min, x_max, y_max)
    
    return None

find_canvas_coordinates('/Users/minhbui/Desktop/Thesis/data/target_shapes/circle_full.png')