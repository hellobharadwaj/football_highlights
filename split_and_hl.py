import os
import csv
import time
from datetime import datetime, timedelta
import cv2
import mediapipe as mp
from tqdm import tqdm
from moviepy.editor import VideoFileClip, concatenate_videoclips, vfx
import re
import subprocess

# === ADDED FOR YOUTUBE UPLOAD ===
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
# === END SECTION ===


# === GoPro Sorting Function ===
def sort_gopro_filenames(filenames):
    def gopro_sort_key(name):
        base = os.path.splitext(name.strip())[0]  # e.g., 'GX011291'
        match = re.fullmatch(r'GX\d{6}', base)
        if not match:
            raise ValueError(f"Invalid GoPro file pattern in: {name!r} (base: {base})")
        gopro_base = match.group(0)
        chapter = int(gopro_base[2:4])  # e.g., '01'
        session = int(gopro_base[4:])   # e.g., '1291'
        return (session, chapter)
    return sorted(filenames, key=gopro_sort_key)

def sort_gopro_score_csvs(filenames):
    def gopro_csv_sort_key(name):
        base = os.path.splitext(name.strip())[0]  # 'GX011291_scores'
        base = base.split('_scores')[0]           # 'GX011291'
        match = re.fullmatch(r'GX\d{6,7}', base)
        if not match:
            raise ValueError(f"Invalid GoPro score file pattern in: {name!r} (base: {base})")
        gopro_base = match.group(0)
        chapter = int(gopro_base[2:4])             # '01'
        session = int(gopro_base[4:])              # '1291'
        return (session, chapter)
    return sorted(filenames, key=gopro_csv_sort_key)

# === Gesture Processing Setup ===
team_one = "Team Black"
team_two = "Team Orange"
starting_score_one = 0
starting_score_two = 0
fps_reduction_factor = 5

mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_drawing = mp.solutions.drawing_utils

# === Gesture Detection Functions ===
def is_index_finger(landmarks):
    return (landmarks.landmark[8].y < landmarks.landmark[6].y and
            landmarks.landmark[12].y > landmarks.landmark[10].y and
            landmarks.landmark[16].y > landmarks.landmark[14].y and
            landmarks.landmark[20].y > landmarks.landmark[18].y)

def is_v_sign(landmarks):
    return [landmarks.landmark[8].y < landmarks.landmark[6].y,
            landmarks.landmark[12].y < landmarks.landmark[10].y,
            landmarks.landmark[16].y > landmarks.landmark[14].y,
            landmarks.landmark[20].y > landmarks.landmark[18].y] == [True]*4

def is_little_finger(landmarks):
    return (landmarks.landmark[20].y < landmarks.landmark[18].y and
            landmarks.landmark[8].y > landmarks.landmark[6].y and
            landmarks.landmark[12].y > landmarks.landmark[10].y and
            landmarks.landmark[16].y > landmarks.landmark[14].y)

# === Video Processor ===
def process_video(input_file):
    cap = cv2.VideoCapture(input_file)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    reduced_fps = fps / fps_reduction_factor
    frame_interval = int(fps / reduced_fps)

    index_finger_count = v_sign_count = little_finger_count = 0
    gesture_cooldown = datetime.min
    cooldown_duration = timedelta(seconds=5)
    required_duration = 0.1
    states = {'index': [False, None], 'v': [False, None], 'little': [False, None]}
    score_events = []

    with tqdm(total=frame_count, desc=f"Processing {os.path.basename(input_file)}") as pbar:
        while cap.isOpened():
            success, image = cap.read()
            if not success:
                break
            frame_number = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            pbar.update(1)
            if frame_number % frame_interval != 0:
                continue

            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = hands.process(image_rgb)
            timestamp = frame_number / fps
            event_time = datetime(1, 1, 1) + timedelta(seconds=timestamp)
            formatted_time = event_time.strftime('%H:%M:%S')

            if results.multi_hand_landmarks and datetime.now() > gesture_cooldown:
                for landmarks in results.multi_hand_landmarks:
                    if is_index_finger(landmarks):
                        if not states['index'][0]:
                            states['index'] = [True, timestamp]
                        elif timestamp - states['index'][1] >= required_duration:
                            index_finger_count += 1
                            score_events.append([formatted_time, 1, 0, 0])
                            states['index'] = [False, None]
                            gesture_cooldown = datetime.now() + cooldown_duration
                    else:
                        states['index'] = [False, None]

                    if is_v_sign(landmarks):
                        if not states['v'][0]:
                            states['v'] = [True, timestamp]
                        elif timestamp - states['v'][1] >= required_duration:
                            v_sign_count += 1
                            score_events.append([formatted_time, 0, 1, 0])
                            states['v'] = [False, None]
                            gesture_cooldown = datetime.now() + cooldown_duration
                    else:
                        states['v'] = [False, None]

                    if is_little_finger(landmarks):
                        if not states['little'][0]:
                            states['little'] = [True, timestamp]
                        elif timestamp - states['little'][1] >= required_duration:
                            little_finger_count += 1
                            score_events.append([formatted_time, 0, 0, 1])
                            states['little'] = [False, None]
                            gesture_cooldown = datetime.now() + cooldown_duration
                    else:
                        states['little'] = [False, None]

    cap.release()
    output_csv = input_file.rsplit('.', 1)[0] + '_scores.csv'
    with open(output_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([input_file])
        writer.writerow(['Timestamp', team_one, team_two, 'Highlights'])
        writer.writerow(['Starting Scores', starting_score_one, starting_score_two, 0])
        writer.writerows(score_events)

# === Highlight Video Generation ===
def draw_text_with_background(image, text, font, scale, color, thickness, bg_color, x_offset, y_offset, padding=10):
    text_size, _ = cv2.getTextSize(text, font, scale, thickness)
    x = int((image.shape[1] - text_size[0] - padding) / 2 + x_offset)
    y = int(y_offset)
    cv2.rectangle(image, (x, y - text_size[1] - padding), (x + text_size[0] + padding, y + padding), bg_color, -1)
    cv2.putText(image, text, (x + padding // 2, y - padding // 2), font, scale, color, thickness, cv2.LINE_AA)
    return image

def get_team_colors(name, default_bg, default_fg):
    colors = {
        'red': ((255, 0, 0), (255, 255, 255)),
        'yellow': ((255, 255, 0), (0, 0, 0)),
        'black': ((0, 0, 0), (255, 255, 255)),
        'blue': ((0, 0, 255), (255, 255, 255)),
        'green': ((0, 255, 0), (0, 0, 0))
    }
    for c in colors:
        if c in name.lower():
            return colors[c]
    return default_bg, default_fg

def create_highlight_video(score_csv_file, highlight_duration=7, include_overlays=False, slow_motion_factor=1):
    with open(score_csv_file) as f:
        reader = csv.reader(f)
        input_file = next(reader)[0]
        _, team_one, team_two, _ = next(reader)
        _, start1, start2, _ = next(reader)
        events = [(datetime.strptime(r[0], '%H:%M:%S'), int(r[1]), int(r[2]), int(r[3])) for r in reader]

    if not events:
        return None

    start1, start2 = int(start1), int(start2)
    cur1, cur2 = start1, start2
    clips, team1_bg, team1_fg = [], *get_team_colors(team_one, (255, 255, 0), (0, 0, 0))
    team2_bg, team2_fg = get_team_colors(team_two, (0, 0, 255), (255, 255, 255))

    for t, s1, s2, _ in events:
        t_sec = t.hour * 3600 + t.minute * 60 + t.second
        start = max(0, t_sec - highlight_duration)
        clip = VideoFileClip(input_file).subclip(start, t_sec).fx(vfx.speedx, 1 / slow_motion_factor)
        if include_overlays:
            clip = clip.fl_image(lambda img: draw_text_with_background(
                draw_text_with_background(img, f'{team_one}: {cur1}', cv2.FONT_HERSHEY_SIMPLEX, 1, team1_fg, 2, team1_bg, 0, 50),
                f'{team_two}: {cur2}', cv2.FONT_HERSHEY_SIMPLEX, 1, team2_fg, 2, team2_bg, 0, 100
            ))
        clips.append(clip)
        cur1 += s1
        cur2 += s2

    final = concatenate_videoclips(clips)
    output_file = score_csv_file.replace('_scores.csv', '_highlights.mp4')
    final.write_videofile(output_file, codec='libx264', audio_codec='aac')
    return output_file

def split_video(video_path, segment_length=7):
    file_name, ext = os.path.splitext(os.path.basename(video_path))
    output_dir = f"{file_name}_clips"
    os.makedirs(output_dir, exist_ok=True)
    
    command_square = [
        'ffmpeg', '-i', video_path, '-vf', 'crop=ih:ih', '-force_key_frames', f"expr:gte(t,n_forced*{segment_length})",
        '-c:v', 'libx264', '-c:a', 'copy', '-map', '0', '-f', 'segment', 
        '-segment_time', str(segment_length), '-reset_timestamps', '1',
        f"{output_dir}/{file_name}_square_%03d{ext}"
    ]
    
    subprocess.run(command_square, check=True)

# === ADDED FOR YOUTUBE UPLOAD ===
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CREDENTIALS_PICKLE = "youtube_credentials.pkl"

def authenticate_youtube():
    client_secrets = os.getenv("YOUTUBE_CLIENT_SECRET_FILE")
    if not client_secrets or not os.path.exists(client_secrets):
        raise FileNotFoundError("Missing or invalid YOUTUBE_CLIENT_SECRET_FILE env variable")
    if os.path.exists(CREDENTIALS_PICKLE):
        with open(CREDENTIALS_PICKLE, "rb") as f:
            credentials = pickle.load(f)
    else:
        flow = InstalledAppFlow.from_client_secrets_file(client_secrets, SCOPES)
        credentials = flow.run_console()
        with open(CREDENTIALS_PICKLE, "wb") as f:
            pickle.dump(credentials, f)
    return build("youtube", "v3", credentials=credentials)

def upload_video_to_youtube(file_path, title, description, privacy="public"):
    youtube = authenticate_youtube()
    media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
    request_body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": ["football", "pune", "highlights"],
            "categoryId": "17"
        },
        "status": {
            "privacyStatus": privacy
        }
    }
    print(f"📤 Uploading {file_path} to YouTube...")
    request = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media
    )
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploading... {int(status.progress() * 100)}%")
    print(f"✅ Upload complete. Video ID: {response['id']}")

def ensure_youtube_credentials_valid():
    """Ensure valid YouTube credentials exist; refresh or regenerate if necessary."""
    try:
        youtube = authenticate_youtube()

        # Test the credentials with a harmless API call
        youtube.channels().list(part="id", mine=True).execute()
        print("✅ YouTube credentials are valid.")
        return youtube
    except Exception as e:
        print(f"⚠️ YouTube credentials invalid or expired: {e}")
        print("🔄 Regenerating OAuth token...")
        if os.path.exists(CREDENTIALS_PICKLE):
            os.remove(CREDENTIALS_PICKLE)  # Remove corrupted/expired credentials
        youtube = authenticate_youtube()
        print("✅ New YouTube credentials obtained.")
        return youtube

# === END SECTION ===

# # === MAIN EXECUTION ===
# input_dir = os.getcwd()

# # Step 1: Get and sort video files
# video_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.mp4')]
# video_files = sort_gopro_filenames(video_files)
# print("Sorted video files:", video_files)

# # # Step 2: Process each video
# for file in video_files:
#     process_video(os.path.join(input_dir, file))

# # Step 3: Find and sort score CSVs (based on matching video name)
# csv_files = [f for f in os.listdir(input_dir) if f.endswith('_scores.csv')]
# csv_files = sort_gopro_score_csvs(csv_files)
# print("Sorted CSV files:", csv_files)

# # Step 4: Generate and combine highlight videos
# highlight_paths = []
# for csv_file in csv_files:
#     highlight_path = create_highlight_video(os.path.join(input_dir, csv_file))
#     split_video(highlight_path)
#     highlight_paths.append(highlight_path)

# # # Optional: Combine the original (unsplit) highlight videos if needed
# final_clip = concatenate_videoclips([VideoFileClip(p) for p in highlight_paths])
# final_path = "combined_highlights.mp4"  # ✅ define this first
# final_clip.write_videofile("combined_highlights.mp4", codec='libx264', audio_codec='aac')
# # === ADDED FOR YOUTUBE UPLOAD ===
# today_str = datetime.now().strftime("%b %d")
# title = f"{today_str} - Highlights"
# description = f"Highlights of the game played in Pune on {today_str} by local Pune footballers."
# upload_video_to_youtube(final_path, title, description)
# # === END SECTION ===
# === MAIN EXECUTION ===
input_dir = os.getcwd()

# Step 0: Validate YouTube credentials before doing anything else
youtube = ensure_youtube_credentials_valid()

# Step 1: Get and sort video files
video_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.mp4')]
video_files = sort_gopro_filenames(video_files)
print("Sorted video files:", video_files)

# Step 2: Process each video
for file in video_files:
    process_video(os.path.join(input_dir, file))

# Step 3: Find and sort score CSVs
csv_files = [f for f in os.listdir(input_dir) if f.endswith('_scores.csv')]
csv_files = sort_gopro_score_csvs(csv_files)
print("Sorted CSV files:", csv_files)

# Step 4: Generate and combine highlight videos
highlight_paths = []
for csv_file in csv_files:
    highlight_path = create_highlight_video(os.path.join(input_dir, csv_file))
    if highlight_path is None:
        continue
    split_video(highlight_path)
    highlight_paths.append(highlight_path)

# Step 5: Combine highlights
if highlight_paths:
    final_clip = concatenate_videoclips([VideoFileClip(p) for p in highlight_paths])
    final_path = "combined_highlights.mp4"
    final_clip.write_videofile(final_path, codec='libx264', audio_codec='aac')

    # Step 6: Upload to YouTube
    today_str = datetime.now().strftime("%b %d")
    title = f"{today_str} - Highlights"
    description = f"Highlights of the game played in Pune on {today_str} by local Pune footballers."
    upload_video_to_youtube(final_path, title, description)
else:
    print("No highlight videos generated; skipping combination and upload.")
