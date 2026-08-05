import cv2
import numpy as np

# Create a black window
img = np.zeros((500, 900, 3), dtype=np.uint8)

# Title
cv2.putText(img, "Gesture-Based Presentation Control", (40, 60),
            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

cv2.putText(img, "Baseline Pipeline Test", (40, 100),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

# Group Members
cv2.putText(img, "Group Members:", (40, 170),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

cv2.putText(img, "1. Dhruv Pankhania 24001158", (60, 220),
            cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)

cv2.putText(img, "2. Krish Jadav 24000638", (60, 270),
            cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)

cv2.putText(img, "3. Dhairya Patel 24001142", (60, 320),
            cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)

# Status
cv2.putText(img, "Status : Pipeline OK", (40, 410),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

cv2.imshow("Pipeline Test", img)

cv2.waitKey(0)
cv2.destroyAllWindows()