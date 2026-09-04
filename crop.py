import cv2
import numpy as np

def warp_region(image, points):
    """
    Takes an image and a 4-point polygon (from PaddleOCR detection),
    and returns a straightened, cropped version of just that region.
    """
    points = np.array(points, dtype="float32")

    width = int(max(
        np.linalg.norm(points[0] - points[1]),
        np.linalg.norm(points[2] - points[3])
    ))
    height = int(max(
        np.linalg.norm(points[1] - points[2]),
        np.linalg.norm(points[3] - points[0])
    ))

    dst_points = np.array([
        [0, 0], [width, 0], [width, height], [0, height]
    ], dtype="float32")

    matrix = cv2.getPerspectiveTransform(points, dst_points)
    warped = cv2.warpPerspective(image, matrix, (width, height))
    return warped