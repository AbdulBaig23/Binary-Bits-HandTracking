# IMPORTS ####################################
import cv2
import mediapipe as mp
import time
from picamera2 import Picamera2
from gpiozero import LED, Button
import random

#define leds and buttons
game_running = False
led_pins = [LED(23), LED(22), LED(27), LED(17)]
button = Button(16)
red_light = LED(24)
green_light = LED(25)

picam2 = Picamera2()
picam2.preview_configuration.main.size = (640, 480)
picam2.preview_configuration.main.format = "RGB888"
picam2.configure("preview")
picam2.start()  # Starts camera preview (your Pi5 works with this)

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2)
mp_drawing = mp.solutions.drawing_utils

# Variables
cTime, pTime = 0, 0
fingertips = [4, 8, 12, 16, 20]
final_finger_count = 0
left_hand_sum = 0
right_hand_sum = 0

def show_binary(number):
    binary_nums = []
    binary_str = format(number, "04b")
    for b in binary_str:
        binary_nums.append(int(b))
    for led, val in zip(led_pins, binary_nums):
        led.value = val

def clear_led():
    for led in led_pins:
        led.off()
def start_game():
    global game_running
    global final_finger_count
    game_running = True
    randnumber = random.randint(0,5)
    show_binary(randnumber)
    time.sleep(3)

    if final_finger_count == randnumber:
        green_light.on()
        time.sleep(3)
        green_light.off()
        print("correct")
    else:
        red_light.on()
        time.sleep(3)
        red_light.off()
        print("incorrect")

    time.sleep(1)
    clear_led()
    game_running = False

button.when_pressed = start_game

# Initialize PiCamera2


# Main loop
while True:
    frame = picam2.capture_array()  # Grab frame from camera
    image = cv2.flip(frame, 1)  # Flip and convert to BGR
    #image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # Convert for MediaPipe
    results = hands.process(image)  # Process hand landmarks
    left_hand_sum = 0
    right_hand_sum = 0


    if results.multi_hand_landmarks:
        for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
            handedness_info = results.multi_handedness[idx]
            classification = handedness_info.classification[0]
            label = classification.label

            fingers = []
            if label == "Right":
                # Thumb
                if hand_landmarks.landmark[fingertips[0]].x < hand_landmarks.landmark[fingertips[0] - 1].x:
                    fingers.append(1)
                else:
                    fingers.append(0)
            else:
                if hand_landmarks.landmark[fingertips[0]].x > hand_landmarks.landmark[fingertips[0] - 1].x:
                    fingers.append(1)
                else:
                    fingers.append(0)

            # Other 4 fingers
            if label == "Right":
                for id in range(1, 5):
                    if hand_landmarks.landmark[fingertips[id]].y < hand_landmarks.landmark[fingertips[id] - 2].y:
                        fingers.append(1)
                    else:
                        fingers.append(0)
                right_hand_sum = sum(fingers)
            else:
                for id in range(1, 5):
                    if hand_landmarks.landmark[fingertips[id]].y < hand_landmarks.landmark[fingertips[id] - 2].y:
                        fingers.append(1)
                    else:
                        fingers.append(0)
                left_hand_sum = sum(fingers)



            final_finger_count = left_hand_sum + right_hand_sum
            print(f"Fingers Up: {final_finger_count}")

            # Draw landmarks
            mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
    else:
        final_finger_count = 0

    if not game_running:
        show_binary(final_finger_count)

    # FPS calculation
    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime

    # Overlay text
    cv2.putText(image, f'FPS: {int(fps)}', (10, 70),
                cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)
    cv2.putText(image, f'Fingers: {final_finger_count}', (450, 70),
                cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)

    # Show the processed image
    cv2.imshow("Hand Tracking", image)

    # Exit on 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
clear_led()
