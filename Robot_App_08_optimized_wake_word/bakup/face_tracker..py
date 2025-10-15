# Import Libraries
import cv2
from cvzone.FaceDetectionModule import FaceDetector
from cvzone.PIDModule import PID
from cvzone.SerialModule import SerialObject
from Config import Config

import time
import random


config = Config()

camera_index = config.CAMERA_INDEX
camera_flip = config.CAMERA_FLIP

print(f"camera_index:{camera_index}")
print(f"camera_flip:{camera_flip}")

# Global variables
cap = None


def closeAllWindows(arduino=None):
	"""
	Function to close all windows and release resources
	
	Args:
		arduino: Arduino serial object (optional)
	"""
	global cap
	
	print("Closing all windows and releasing resources...")
	
	# Release camera
	if cap is not None and cap.isOpened():
		cap.release()
		print("Camera released")
	
	# Close Arduino connection if it exists
	if arduino is not None:
		try:
			# Send neutral position before closing
			arduino.sendData([0, 0, 90])
			print("Arduino reset to neutral position")
		except:
			print("Could not reset Arduino")
	
	# Close all OpenCV windows
	cv2.destroyAllWindows()
	print("All windows closed")


def naturalEyeMovement(enableArdunio=False):
	"""
	Move the eye naturally without camera tracking
	"""
	# Load images
	background_img = cv2.imread('Resources/Eye-Background.png', cv2.IMREAD_UNCHANGED)
	iris_img = cv2.imread('Resources/Eye-Ball.png', cv2.IMREAD_UNCHANGED)

	# Initialize Arduino serial communication
	arduino = None
	
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

	# Possible eye positions (x, y)
	positions = [
		(325, 225),  # Center
		(400, 225),  # Right
		(250, 225),  # Left
		(325, 200),  # Up
		(325, 250),  # Down
		(380, 210),  # Up-Right
		(270, 210),  # Up-Left
		(380, 240),  # Down-Right
		(270, 240),  # Down-Left
	]
	
	# Arduino angles for each position
	arduino_angles = [
		90,   # Center
		60,   # Right
		120,  # Left
		90,   # Up
		90,   # Down
		70,   # Up-Right
		110,  # Up-Left
		70,   # Down-Right
		110,  # Down-Left
	]
	
	current_position_index = 0  # Start at center
	iris_position = positions[current_position_index]
	xAngle = arduino_angles[current_position_index]
	
	# Timing variables
	last_movement_time = time.time()
	hold_duration = random.uniform(1.5, 4.0)  # Stay at position for 1.5-4 seconds
	
	if enableArdunio:
		try:
			arduino = SerialObject(digits=3)
			print("Arduino initialized successfully")
		except Exception as e:
			print(f"Could not initialize Arduino: {e}")
			arduino = None
	
	try:
		print("Natural eye movement started. Press 'q' or ESC to quit.")
		
		while True:
			current_time = time.time()
			
			# Check if it's time to move to a new position
			if current_time - last_movement_time >= hold_duration:
				# Choose a new random position
				# 60% chance to go to center, 40% chance to go to other positions
				if random.random() < 0.6 and current_position_index != 0:
					current_position_index = 0  # Go to center
				else:
					# Choose random position (avoid staying at same position)
					available_positions = [i for i in range(len(positions)) if i != current_position_index]
					current_position_index = random.choice(available_positions)
				
				iris_position = positions[current_position_index]
				xAngle = arduino_angles[current_position_index]
				
				print(f"Moving to position: {current_position_index} - {iris_position}")
				
				# Send to Arduino
				if enableArdunio and arduino is not None:
					arduino.sendData([0, 0, xAngle])
				
				# Reset timer with new random duration
				last_movement_time = current_time
				hold_duration = random.uniform(1.5, 4.0)
			
			# Overlay the iris on the background image
			background_with_iris = background_img.copy()
			overlay_iris(background_with_iris, iris_img, iris_position[0], iris_position[1])
			
			# Show the result
			cv2.imshow('Overlay Result', background_with_iris)
			cv2.moveWindow('Overlay Result', -1920, 0)
			
			# Wait and check for exit key
			key = cv2.waitKey(30) & 0xFF
			if key == ord('q') or key == 27:  # 'q' or ESC key
				break
	
	except KeyboardInterrupt:
		print("\nProgram interrupted by user")
	except Exception as e:
		print(f"An error occurred: {e}")
	finally:
		# Always close windows and release resources
		closeAllWindows(arduino)


def trackUserFace(enableArdunio=False):
	global cap
	
	# Load images
	background_img = cv2.imread('Resources/Eye-Background.png', cv2.IMREAD_UNCHANGED)
	iris_img = cv2.imread('Resources/Eye-Ball.png', cv2.IMREAD_UNCHANGED)

	# Initialize camera
	cap = cv2.VideoCapture(camera_index)

	# Initialize face detector and PID controller
	detector = FaceDetector(minDetectionCon=0.8)
	xPID = PID([0.03, 0, 0.06], 640 // 2, axis=0)
	xAngle = 90

	# Initialize Arduino serial communication
	arduino = None
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

	
	if enableArdunio:
		try:
			arduino = SerialObject(digits=3)
			print("Arduino initialized successfully")
		except Exception as e:
			print(f"Could not initialize Arduino: {e}")
			arduino = None
		
	try:
		while True:
			success, img = cap.read()
			if not success:
				print("Failed to read from camera")
				break
				
			if camera_flip:
				img = cv2.flip(img, 0)
			img, bboxs = detector.findFaces(img)
			
			if bboxs:
				cx = bboxs[0]['center'][0]
				print(f"cx:{cx}")
				resultX = int(xPID.update(cx))
				print(f"resultX:{resultX}")
		
				# Update iris position based on resultX and camera_flip
				if camera_flip:
					# Normal iris movement when camera is flipped
					if resultX > 1:
						iris_position = (400, 225)  # Move iris to the right
					elif resultX < -1:
						iris_position = (250, 225)  # Move iris to the left
					else:
						iris_position = (325, 225)  # Center
				else:
					# Reversed iris movement when camera is NOT flipped
					if resultX > 1:
						iris_position = (250, 225)  # Move iris to the left (reversed)
					elif resultX < -1:
						iris_position = (400, 225)  # Move iris to the right (reversed)
					else:
						iris_position = (325, 225)  # Center
		
				if enableArdunio and arduino is not None:
					# Control the servo based on xAngle
					if abs(resultX) > center_threshold:
						xAngle += resultX
		
					print(f"xAngle:{xAngle}")
					arduino.sendData([0, 0, xAngle])
		
			# Overlay the iris on the background image
			background_with_iris = background_img.copy()
			overlay_iris(background_with_iris, iris_img, iris_position[0], iris_position[1])
		
			cv2.imshow("img", img)
			# Show the result and move the window
			cv2.imshow('Overlay Result', background_with_iris)
			cv2.moveWindow('Overlay Result', -1920, 0)
		
			# Wait until a key is pressed to close the window
			key = cv2.waitKey(1) & 0xFF
			if key == ord('q') or key == 27:  # 'q' or ESC key
				break
	
	except KeyboardInterrupt:
		print("\nProgram interrupted by user")
	except Exception as e:
		print(f"An error occurred: {e}")
	finally:
		# Always close windows and release resources
		closeAllWindows(arduino)


# Example usage
if __name__ == "__main__":
	# Use this for natural eye movement without camera
	naturalEyeMovement(enableArdunio=False)
	
	# Or use this for face tracking when camera works
	# trackUserFace(enableArdunio=False)