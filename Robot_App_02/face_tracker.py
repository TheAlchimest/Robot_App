# Import Libraries
import cv2
from cvzone.FaceDetectionModule import FaceDetector
from cvzone.PIDModule import PID
from cvzone.SerialModule import SerialObject

import time


	
def trackUserFace(enableArdunio:False):
	# Load images
	background_img = cv2.imread('Resources/Eye-Background.png', cv2.IMREAD_UNCHANGED)
	iris_img = cv2.imread('Resources/Eye-Ball.png', cv2.IMREAD_UNCHANGED)

	# Initialize camera
	cap = cv2.VideoCapture(1)

	# Initialize face detector and PID controller
	detector = FaceDetector(minDetectionCon=0.8)
	xPID = PID([0.03, 0, 0.06], 640 // 2, axis=0)
	xAngle = 90

	# Initialize Arduino serial communication
	ardunioIntialized = False
	# Define the threshold value for the center
	center_threshold = 2  # Adjust this value as needed


	# Function to overlay the iris on the background
	def overlay_iris(background, iris, x, y):
		h, w = iris.shape[:2]
		if x + w > background.shape[1]:
			w = background.shape[1] - x
			iris = iris[:, :w]
		if y + h > background.shape[0]:
			h = background.shape[0] - y
			iris = iris[:h]

		alpha = iris[:, :, 3] / 255.0
		for c in range(3):
			background[y:y+h, x:x+w, c] = alpha * iris[:, :, c] + (1 - alpha) * background[y:y+h, x:x+w, c]

	# Create a named window and set it to full screen
	cv2.namedWindow('Overlay Result', cv2.WND_PROP_FULLSCREEN)
	cv2.setWindowProperty('Overlay Result', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

	# Initialize iris position in the center
	iris_position = (325, 225)  # (x, y) 


	
	if(enableArdunio and not ardunioIntialized):
		arduino = SerialObject(digits=3)
		
	while True:
		success, img = cap.read()
		img = cv2.flip(img, 0)
		img, bboxs = detector.findFaces(img)
		#time.sleep(3) # Sleep for 3 seconds
		if bboxs:
			cx = bboxs[0]['center'][0]
			print(f"cx:{cx}")
			resultX = int(xPID.update(cx))
			print(f"resultX:{resultX}")
	
			# Update iris position based on resultX
			if resultX > 1:
				iris_position = (400, 225)  # Move iris to the right
			elif resultX < -1:
				iris_position = (250, 225)  # Move iris to the left
			else:
				iris_position = (325,225)
	
			if(enableArdunio):
				# Control the servo based on xAngle
				if abs(resultX) > center_threshold:
					xAngle += resultX
	
				print(f"xAngle:{xAngle}")
				arduino.sendData([0, 0, xAngle])
	
		# Overlay the iris on the background image
		background_with_iris = background_img.copy()
		overlay_iris(background_with_iris, iris_img, iris_position[0], iris_position[1])
	
		cv2.imshow("img",img)
		# Show the result and move the window
		cv2.imshow('Overlay Result', background_with_iris)
		#[TODO]
		cv2.moveWindow('Overlay Result', -1920, 0)
	
		# Wait until a key is pressed to close the window
		if cv2.waitKey(1) & 0xFF == ord('q'):
			break
	
	
	cv2.destroyAllWindows()
