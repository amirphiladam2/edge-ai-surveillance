import cv2

coords = []

def click_event(event, x, y, flags, params):
    if event == cv2.EVENT_LBUTTONDOWN:
        # Prevent clicking more than 4 times
        if len(coords) < 4:
            print(f"[{x}, {y}],", end=" ")
            coords.append((x, y))

print("Starting live camera feed...")
cap = cv2.VideoCapture(0)

cv2.namedWindow("Live Feed - Click 4 Corners")
cv2.setMouseCallback("Live Feed - Click 4 Corners", click_event)

print("Look at the video window.")
print("Click the 4 corners of the area you want to protect.")
print("Press ESC when you are done.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame.")
        break

    # Draw the points and lines as the user clicks them
    for i, point in enumerate(coords):
        cv2.circle(frame, point, 5, (0, 0, 255), -1)
        if i > 0:
            cv2.line(frame, coords[i-1], coords[i], (255, 0, 0), 2)
    
    # Connect the last point to the first point if 4 points are clicked
    if len(coords) == 4:
        cv2.line(frame, coords[3], coords[0], (255, 0, 0), 2)
        cv2.putText(frame, "ZONE SAVED! Press ESC to exit.", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    cv2.imshow("Live Feed - Click 4 Corners", frame)

    # Press ESC to exit
    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()

if len(coords) == 4:
    print("\n\nSUCCESS! Copy this EXACT line into your app/main.py:")
    print(f"RESTRICTED_ZONE = np.array({coords}, np.int32)")
else:
    print("\nYou didn't click exactly 4 points. Please run the script again.")