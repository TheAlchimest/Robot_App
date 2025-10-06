# Import Libraries
import cv2
from cvzone.FaceDetectionModule import FaceDetector
from cvzone.PIDModule import PID
from cvzone.SerialModule import SerialObject
from Config import Config

import time
import random
import numpy as np


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
	Move the eye naturally without camera tracking with realistic features
	"""
	# Load images
	background_img = cv2.imread('Resources/Eye-Background.png', cv2.IMREAD_UNCHANGED)
	iris_img = cv2.imread('Resources/Eye-Ball.png', cv2.IMREAD_UNCHANGED)

	# Initialize Arduino serial communication
	arduino = None
	
	# Function to overlay the iris on the background
	def overlay_iris(background, iris, x, y, opacity=1.0):
		h, w = iris.shape[:2]
		if x + w > background.shape[1]:
			w = background.shape[1] - x
			iris = iris[:, :w]
		if y + h > background.shape[0]:
			h = background.shape[0] - y
			iris = iris[:h]

		alpha = (iris[:, :, 3] / 255.0) * opacity
		for c in range(3):
			background[y:y+h, x:x+w, c] = alpha * iris[:, :, c] + (1 - alpha) * background[y:y+h, x:x+w, c]
	
	# Function to create blink effect
	def create_blink_overlay(background, blink_amount):
		"""
		Create a blinking effect by darkening from top and bottom
		blink_amount: 0 (open) to 1 (closed)
		"""
		overlay = background.copy()
		h, w = overlay.shape[:2]
		
		# Calculate how much to close
		close_height = int(h * blink_amount * 0.5)
		
		if close_height > 0:
			# Darken from top
			overlay[:close_height, :] = overlay[:close_height, :] * 0.3
			# Darken from bottom
			overlay[h-close_height:, :] = overlay[h-close_height:, :] * 0.3
		
		return overlay
	
	# Function for smooth transition between positions
	def lerp(start, end, t):
		"""Linear interpolation"""
		return start + (end - start) * t

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
	
	current_position_index = 0
	target_position_index = 0
	current_iris_x = float(positions[0][0])
	current_iris_y = float(positions[0][1])
	target_iris_x = float(positions[0][0])
	target_iris_y = float(positions[0][1])
	xAngle = arduino_angles[current_position_index]
	
	# Timing variables
	last_movement_time = time.time()
	hold_duration = random.uniform(2.0, 4.0)
	
	# Blinking variables
	last_blink_time = time.time()
	blink_interval = random.uniform(2.5, 5.0)  # Blink every 2.5-5 seconds
	is_blinking = False
	blink_progress = 0.0
	blink_speed = 0.15  # Speed of blink animation
	
	# Micro-movement variables
	micro_movement_x = 0
	micro_movement_y = 0
	micro_movement_time = time.time()
	
	# Transition variables
	is_transitioning = False
	transition_progress = 0.0
	transition_speed = 0.08  # Speed of smooth movement
	
	if enableArdunio:
		try:
			arduino = SerialObject(digits=3)
			print("Arduino initialized successfully")
		except Exception as e:
			print(f"Could not initialize Arduino: {e}")
			arduino = None
	
	try:
		print("Realistic eye movement started. Press 'q' or ESC to quit.")
		
		while True:
			current_time = time.time()
			
			# === Blinking Logic ===
			if not is_blinking and current_time - last_blink_time >= blink_interval:
				is_blinking = True
				blink_progress = 0.0
			
			if is_blinking:
				blink_progress += blink_speed
				if blink_progress >= 2.0:  # Complete blink cycle
					is_blinking = False
					blink_progress = 0.0
					last_blink_time = current_time
					blink_interval = random.uniform(2.5, 5.0)
			
			# Calculate blink amount (0 to 1)
			if blink_progress < 1.0:
				blink_amount = blink_progress  # Closing
			else:
				blink_amount = 2.0 - blink_progress  # Opening
			
			# === Micro-movements (subtle eye tremor) ===
			if current_time - micro_movement_time > 0.1:  # Update every 100ms
				micro_movement_x = random.uniform(-2, 2)
				micro_movement_y = random.uniform(-1, 1)
				micro_movement_time = current_time
			
			# === Movement Logic ===
			if not is_transitioning and current_time - last_movement_time >= hold_duration:
				# Start new transition
				is_transitioning = True
				transition_progress = 0.0
				current_position_index = target_position_index
				
				# Choose new target position
				if random.random() < 0.6 and current_position_index != 0:
					target_position_index = 0  # Go to center
				else:
					available_positions = [i for i in range(len(positions)) if i != current_position_index]
					target_position_index = random.choice(available_positions)
				
				target_iris_x = float(positions[target_position_index][0])
				target_iris_y = float(positions[target_position_index][1])
				xAngle = arduino_angles[target_position_index]
				
				print(f"Moving to position: {target_position_index}")
				
				if enableArdunio and arduino is not None:
					arduino.sendData([0, 0, xAngle])
				
				last_movement_time = current_time
				hold_duration = random.uniform(2.0, 4.0)
			
			# === Smooth Transition ===
			if is_transitioning:
				transition_progress += transition_speed
				if transition_progress >= 1.0:
					is_transitioning = False
					transition_progress = 1.0
					current_iris_x = target_iris_x
					current_iris_y = target_iris_y
				else:
					# Smooth interpolation
					current_iris_x = lerp(current_iris_x, target_iris_x, transition_progress)
					current_iris_y = lerp(current_iris_y, target_iris_y, transition_progress)
			
			# Calculate final position with micro-movements
			final_x = int(current_iris_x + micro_movement_x)
			final_y = int(current_iris_y + micro_movement_y)
			
			# Create the eye frame
			background_with_iris = background_img.copy()
			overlay_iris(background_with_iris, iris_img, final_x, final_y)
			
			# Apply blink effect
			if is_blinking:
				background_with_iris = create_blink_overlay(background_with_iris, blink_amount)
			
			# Show the result
			cv2.imshow('Overlay Result', background_with_iris)
			cv2.moveWindow('Overlay Result', -1920, 0)
			
			# Wait and check for exit key
			key = cv2.waitKey(30) & 0xFF
			if key == ord('q') or key == 27:
				break
	
	except KeyboardInterrupt:
		print("\nProgram interrupted by user")
	except Exception as e:
		print(f"An error occurred: {e}")
	finally:
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
	center_threshold = 2

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

	cv2.namedWindow('Overlay Result', cv2.WND_PROP_FULLSCREEN)
	cv2.setWindowProperty('Overlay Result', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

	iris_position = (325, 225)

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
		
				if camera_flip:
					if resultX > 1:
						iris_position = (400, 225)
					elif resultX < -1:
						iris_position = (250, 225)
					else:
						iris_position = (325, 225)
				else:
					if resultX > 1:
						iris_position = (250, 225)
					elif resultX < -1:
						iris_position = (400, 225)
					else:
						iris_position = (325, 225)
		
				if enableArdunio and arduino is not None:
					if abs(resultX) > center_threshold:
						xAngle += resultX
					print(f"xAngle:{xAngle}")
					arduino.sendData([0, 0, xAngle])
		
			background_with_iris = background_img.copy()
			overlay_iris(background_with_iris, iris_img, iris_position[0], iris_position[1])
		
			cv2.imshow("img", img)
			cv2.imshow('Overlay Result', background_with_iris)
			cv2.moveWindow('Overlay Result', -1920, 0)
		
			key = cv2.waitKey(1) & 0xFF
			if key == ord('q') or key == 27:
				break
	
	except KeyboardInterrupt:
		print("\nProgram interrupted by user")
	except Exception as e:
		print(f"An error occurred: {e}")
	finally:
		closeAllWindows(arduino)


# Example usage
if __name__ == "__main__":
	naturalEyeMovement(enableArdunio=False)