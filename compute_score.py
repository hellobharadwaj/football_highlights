import cv2
import mediapipe as mp
import csv
from datetime import datetime, timedelta
from tqdm import tqdm
import time
import os

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_drawing = mp.solutions.drawing_utils

# Global variables for team names and starting scores
team_one = "Team Black"
team_two = "Team Orange"
starting_score_one = 0
starting_score_two = 0
fps_reduction_factor = 5  # FPS 50, use 1.5 for FPS 30

# Function to detect index finger gesture
def is_index_finger(hand_landmarks):
    return (hand_landmarks.landmark[8].y < hand_landmarks.landmark[6].y and
            hand_landmarks.landmark[12].y > hand_landmarks.landmark[10].y and
            hand_landmarks.landmark[16].y > hand_landmarks.landmark[14].y and
            hand_landmarks.landmark[20].y > hand_landmarks.landmark[18].y)

# Function to detect V sign gesture
def is_v_sign(hand_landmarks):
    fingers = [
        hand_landmarks.landmark[8].y < hand_landmarks.landmark[6].y,
        hand_landmarks.landmark[12].y < hand_landmarks.landmark[10].y,
        hand_landmarks.landmark[16].y > hand_landmarks.landmark[14].y,
        hand_landmarks.landmark[20].y > hand_landmarks.landmark[18].y
    ]
    return fingers == [True, True, True, True]

# Function to detect little finger gesture
def is_little_finger(hand_landmarks):
    return (hand_landmarks.landmark[20].y < hand_landmarks.landmark[18].y and
            hand_landmarks.landmark[8].y > hand_landmarks.landmark[6].y and
            hand_landmarks.landmark[12].y > hand_landmarks.landmark[10].y and
            hand_landmarks.landmark[16].y > hand_landmarks.landmark[14].y)

# Function to process a single video file
def process_video(input_file):
    # Initialize counters for gestures
    index_finger_count = 0
    v_sign_count = 0
    little_finger_count = 0

    # States to track gestures
    index_finger_active = False
    v_sign_active = False
    little_finger_active = False
    index_finger_start_time = None
    v_sign_start_time = None
    little_finger_start_time = None
    gesture_cooldown = datetime.min
    cooldown_duration = timedelta(seconds=5)
    required_duration = 0.1

    cap = cv2.VideoCapture(input_file)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    reduced_fps = fps / fps_reduction_factor
    frame_interval = int(fps / reduced_fps)

    score_events = []

    start_time = time.time()

    with tqdm(total=frame_count, desc="Processing Frames") as pbar:
        while cap.isOpened():
            success, image = cap.read()
            if not success:
                break

            frame_number = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            pbar.update(1)

            if frame_number % frame_interval != 0:
                continue

            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = hands.process(image)
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            timestamp = frame_number / fps
            video_start_time = datetime(1, 1, 1)
            event_time = video_start_time + timedelta(seconds=timestamp)
            formatted_time = event_time.strftime('%H:%M:%S')

            gesture_detected = None

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    
                    if datetime.now() > gesture_cooldown:
                        if is_index_finger(hand_landmarks):
                            if not index_finger_active:
                                index_finger_start_time = timestamp
                                index_finger_active = True
                            elif index_finger_active and (timestamp - index_finger_start_time >= required_duration):
                                index_finger_count += 1
                                score_events.append([formatted_time, 1, 0, 0])
                                gesture_detected = 'Index Finger Gesture'
                                index_finger_active = False
                                index_finger_start_time = None
                                gesture_cooldown = datetime.now() + cooldown_duration
                        else:
                            index_finger_active = False
                            index_finger_start_time = None

                        if is_v_sign(hand_landmarks):
                            if not v_sign_active:
                                v_sign_start_time = timestamp
                                v_sign_active = True
                            elif v_sign_active and (timestamp - v_sign_start_time >= required_duration):
                                v_sign_count += 1
                                score_events.append([formatted_time, 0, 1, 0])
                                gesture_detected = 'V Sign Gesture'
                                v_sign_active = False
                                v_sign_start_time = None
                                gesture_cooldown = datetime.now() + cooldown_duration
                        else:
                            v_sign_active = False
                            v_sign_start_time = None

                        if is_little_finger(hand_landmarks):
                            if not little_finger_active:
                                little_finger_start_time = timestamp
                                little_finger_active = True
                            elif little_finger_active and (timestamp - little_finger_start_time >= required_duration):
                                little_finger_count += 1
                                score_events.append([formatted_time, 0, 0, 1])
                                gesture_detected = 'Little Finger Gesture'
                                little_finger_active = False
                                little_finger_start_time = None
                                gesture_cooldown = datetime.now() + cooldown_duration
                        else:
                            little_finger_active = False
                            little_finger_start_time = None

            if gesture_detected:
                print(f'{gesture_detected} detected at {formatted_time}')

    cap.release()

    output_csv_file = input_file.rsplit('.', 1)[0] + '_scores.csv'
    with open(output_csv_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([input_file])
        fieldnames = ['Timestamp', team_one, team_two, 'Highlights']
        writer.writerow(fieldnames)
        writer.writerow(['Starting Scores', starting_score_one, starting_score_two, 0])
        for event in score_events:
            writer.writerow(event)

    print(f'{team_one} Count: {index_finger_count}')
    print(f'{team_two} Count: {v_sign_count}')
    print(f'Highlights Count: {little_finger_count}')

    end_time = time.time()
    print(f"Time taken: {end_time - start_time:.2f} seconds")

# Set directory containing video files
input_dir = os.getcwd()

# Iterate over all files in the directory
for filename in os.listdir(input_dir):
    if filename.lower().endswith('.mp4'):
        # Process each video file
        input_file = os.path.join(input_dir, filename)
        process_video(input_file)
