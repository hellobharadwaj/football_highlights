

# import cv2
# import csv
# from datetime import datetime
# from moviepy.editor import VideoFileClip, concatenate_videoclips
# import os
# import subprocess

# highlight_duration = 10  # seconds

# def draw_text_with_background(image, text, font, scale, color, thickness, bg_color, x_offset, y_offset, padding=10):
#     text_size, _ = cv2.getTextSize(text, font, scale, thickness)
#     width, _ = image.shape[1], image.shape[0]
#     x = int((width - text_size[0] - padding) // 2 + x_offset)
#     y = int(y_offset)
#     bg_color = tuple(map(int, bg_color))
#     writable_image = image.copy()
#     cv2.rectangle(writable_image, (x, y - text_size[1] - padding), (x + text_size[0] + padding, y + padding), bg_color, -1)
#     cv2.putText(writable_image, text, (x + padding // 2, y - padding // 2), font, scale, color, thickness, cv2.LINE_AA)
#     return writable_image

# def get_team_colors(team_name, default_bg, default_fg):
#     colors = {
#         'red': ((255, 0, 0), (255, 255, 255)),
#         'yellow': ((255, 255, 0), (0, 0, 0)),
#         'black': ((0, 0, 0), (255, 255, 255)),
#         'blue': ((0, 0, 255), (255, 255, 255)),
#         'green': ((0, 255, 0), (255, 255, 255))
#     }
#     for color in colors:
#         if color in team_name.lower():
#             return colors[color]
#     return (default_bg, default_fg)

# def create_highlight_video(score_csv_file, highlight_duration=10, include_overlays=True):
#     print(f"Loading scores from CSV: {score_csv_file}...")
#     score_events = []
#     with open(score_csv_file, 'r') as csvfile:
#         reader = csv.reader(csvfile)
#         input_file = next(reader)[0]
#         fieldnames = next(reader)
#         starting_scores = next(reader)
#         team_one = fieldnames[1]
#         team_two = fieldnames[2]
#         starting_score_one = int(starting_scores[1])
#         starting_score_two = int(starting_scores[2])
#         for row in reader:
#             timestamp = datetime.strptime(row[0], '%H:%M:%S')
#             total_seconds = timestamp.hour * 3600 + timestamp.minute * 60 + timestamp.second
#             score_events.append((total_seconds, int(row[1]), int(row[2]), int(row[3])))

#     highlight_clips = []
#     current_team_one_score = starting_score_one
#     current_team_two_score = starting_score_two
#     team_one_bg, team_one_fg = get_team_colors(team_one, (255, 255, 0), (0, 0, 0))
#     team_two_bg, team_two_fg = get_team_colors(team_two, (0, 0, 255), (255, 255, 255))

#     for event in score_events:
#         event_time = event[0]
#         start_time = max(0, event_time - highlight_duration)
#         end_time = event_time

#         highlight_clip = VideoFileClip(input_file).subclip(start_time, end_time)

#         if include_overlays:
#             score_one = current_team_one_score
#             score_two = current_team_two_score
#             highlight_clip = highlight_clip.fl_image(lambda img, s1=score_one, s2=score_two: draw_text_with_background(
#                 draw_text_with_background(
#                     img, f'{team_one}: {s1}', cv2.FONT_HERSHEY_SIMPLEX, 1, team_one_fg, 2, team_one_bg, 0, 50
#                 ), f'{team_two}: {s2}', cv2.FONT_HERSHEY_SIMPLEX, 1, team_two_fg, 2, team_two_bg, 0, 100
#             ))

#         highlight_clips.append(highlight_clip)

#         current_team_one_score += event[1]
#         current_team_two_score += event[2]

#     print(f"Combining highlight clips into a final video for {score_csv_file}...")
#     combined_clip = concatenate_videoclips(highlight_clips)
#     output_filename = os.path.splitext(os.path.basename(input_file))[0] + '_highlights.mp4'
#     output_path = os.path.join(os.path.dirname(score_csv_file), output_filename)
#     print(f"Saving combined highlights video: {output_path}")
#     combined_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')

#     return output_path

# def split_video(video_path, segment_length=10):
#     file_name, ext = os.path.splitext(os.path.basename(video_path))
#     output_dir = f"{file_name}_clips"
#     os.makedirs(output_dir, exist_ok=True)
    
#     command_square = [
#         'ffmpeg', '-i', video_path, '-vf', 'crop=ih:ih', '-force_key_frames', f"expr:gte(t,n_forced*{segment_length})",
#         '-c:v', 'libx264', '-c:a', 'copy', '-map', '0', '-f', 'segment', 
#         '-segment_time', str(segment_length), '-reset_timestamps', '1',
#         f"{output_dir}/{file_name}_square_%03d{ext}"
#     ]
    
#     subprocess.run(command_square, check=True)
    
#     probe = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', video_path], capture_output=True, text=True)
#     width, height = map(int, probe.stdout.strip().split(','))

#     new_height = int(width * 16 / 9)
#     pad_top_bottom = (new_height - height) // 2

#     command_mobile = [
#         'ffmpeg', '-i', video_path, '-vf', f'pad={width}:{new_height}:0:{pad_top_bottom}', '-force_key_frames', f"expr:gte(t,n_forced*{segment_length})",
#         '-c:v', 'libx264', '-c:a', 'copy', '-map', '0', '-f', 'segment', 
#         '-segment_time', str(segment_length), '-reset_timestamps', '1',
#         f"{output_dir}/{file_name}_mobile_%03d{ext}"
#     ]
    
#     subprocess.run(command_mobile, check=True)

# def process_multiple_csvs(csv_files, highlight_duration=10, include_overlays=True):
#     all_videos = []
#     for csv_file in csv_files:
#         video_path = create_highlight_video(csv_file, highlight_duration, include_overlays)
#         all_videos.append(video_path)
#         split_video(video_path, highlight_duration)
    
#     print("Combining all individual highlight videos into a single final video...")
#     final_clips = [VideoFileClip(video) for video in all_videos]
#     final_combined_clip = concatenate_videoclips(final_clips)
#     final_output_filename = 'combined_highlights.mp4'
#     final_output_path = os.path.join(os.path.dirname(csv_files[0]), final_output_filename)
#     print(f"Saving the final combined highlights video: {final_output_path}")
#     final_combined_clip.write_videofile(final_output_path, codec='libx264', audio_codec='aac')

#     return final_output_path


# # Example usage
# csv_files = [  'GX010835_scores.csv', 'GX020835_scores.csv', 'GX010836_scores.csv', 'GX010837_scores.csv']
# process_multiple_csvs(csv_files, highlight_duration=7, include_overlays=True)

import cv2
import csv
from datetime import datetime
from moviepy.editor import VideoFileClip, concatenate_videoclips, vfx
import os
import subprocess

def draw_text_with_background(image, text, font, scale, color, thickness, bg_color, x_offset, y_offset, padding=10):
    text_size, _ = cv2.getTextSize(text, font, scale, thickness)
    width, _ = image.shape[1], image.shape[0]
    x = int((width - text_size[0] - padding) // 2 + x_offset)
    y = int(y_offset)
    bg_color = tuple(map(int, bg_color))
    writable_image = image.copy()
    cv2.rectangle(writable_image, (x, y - text_size[1] - padding), (x + text_size[0] + padding, y + padding), bg_color, -1)
    cv2.putText(writable_image, text, (x + padding // 2, y - padding // 2), font, scale, color, thickness, cv2.LINE_AA)
    return writable_image

def get_team_colors(team_name, default_bg, default_fg):
    colors = {
        'red': ((255, 0, 0), (255, 255, 255)),
        'yellow': ((255, 255, 0), (0, 0, 0)),
        'black': ((0, 0, 0), (255, 255, 255)),
        'blue': ((0, 0, 255), (255, 255, 255)),
        'green': ((0, 255, 0), (255, 255, 255))
    }
    for color in colors:
        if color in team_name.lower():
            return colors[color]
    return (default_bg, default_fg)

def create_highlight_video(score_csv_file, highlight_duration=7, include_overlays=True, slow_motion_factor=0.5):
    print(f"Loading scores from CSV: {score_csv_file}...")
    score_events = []
    with open(score_csv_file, 'r') as csvfile:
        reader = csv.reader(csvfile)
        input_file = next(reader)[0]
        fieldnames = next(reader)
        starting_scores = next(reader)
        team_one = fieldnames[1]
        team_two = fieldnames[2]
        starting_score_one = int(starting_scores[1])
        starting_score_two = int(starting_scores[2])
        for row in reader:
            timestamp = datetime.strptime(row[0], '%H:%M:%S')
            total_seconds = timestamp.hour * 3600 + timestamp.minute * 60 + timestamp.second
            score_events.append((total_seconds, int(row[1]), int(row[2]), int(row[3])))

    highlight_clips = []
    current_team_one_score = starting_score_one
    current_team_two_score = starting_score_two
    team_one_bg, team_one_fg = get_team_colors(team_one, (255, 255, 0), (0, 0, 0))
    team_two_bg, team_two_fg = get_team_colors(team_two, (0, 0, 255), (255, 255, 255))

    for event in score_events:
        event_time = event[0]
        start_time = max(0, event_time - highlight_duration)
        end_time = event_time

        highlight_clip = VideoFileClip(input_file).subclip(start_time, end_time).fx(vfx.speedx, 1/slow_motion_factor)

        if include_overlays:
            score_one = current_team_one_score
            score_two = current_team_two_score
            highlight_clip = highlight_clip.fl_image(lambda img, s1=score_one, s2=score_two: draw_text_with_background(
                draw_text_with_background(
                    img, f'{team_one}: {s1}', cv2.FONT_HERSHEY_SIMPLEX, 1, team_one_fg, 2, team_one_bg, 0, 50
                ), f'{team_two}: {s2}', cv2.FONT_HERSHEY_SIMPLEX, 1, team_two_fg, 2, team_two_bg, 0, 100
            ))

        highlight_clips.append(highlight_clip)

        current_team_one_score += event[1]
        current_team_two_score += event[2]

    print(f"Combining highlight clips into a final video for {score_csv_file}...")
    combined_clip = concatenate_videoclips(highlight_clips)
    output_filename = os.path.splitext(os.path.basename(input_file))[0] + '_highlights.mp4'
    output_path = os.path.join(os.path.dirname(score_csv_file), output_filename)
    print(f"Saving combined highlights video: {output_path}")
    combined_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')

    return output_path

def split_video(video_path, segment_length=14):
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
    
    probe = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', video_path], capture_output=True, text=True)
    width, height = map(int, probe.stdout.strip().split(','))

    new_height = int(width * 16 / 9)
    pad_top_bottom = (new_height - height) // 2

    command_mobile = [
        'ffmpeg', '-i', video_path, '-vf', f'pad={width}:{new_height}:0:{pad_top_bottom}', '-force_key_frames', f"expr:gte(t,n_forced*{segment_length})",
        '-c:v', 'libx264', '-c:a', 'copy', '-map', '0', '-f', 'segment', 
        '-segment_time', str(segment_length), '-reset_timestamps', '1',
        f"{output_dir}/{file_name}_mobile_%03d{ext}"
    ]
    
    subprocess.run(command_mobile, check=True)

def process_multiple_csvs(csv_files, highlight_duration=7, include_overlays=True, slow_motion_factor=2):
    all_videos = []
    for csv_file in csv_files:
        video_path = create_highlight_video(csv_file, highlight_duration, include_overlays, slow_motion_factor)
        all_videos.append(video_path)
        split_video(video_path, highlight_duration*slow_motion_factor)
    
    print("Combining all individual highlight videos into a single final video...")
    final_clips = [VideoFileClip(video) for video in all_videos]
    final_combined_clip = concatenate_videoclips(final_clips)
    final_output_filename = 'combined_highlights.mp4'
    final_output_path = os.path.join(os.path.dirname(csv_files[0]), final_output_filename)
    print(f"Saving the final combined highlights video: {final_output_path}")
    final_combined_clip.write_videofile(final_output_path, codec='libx264', audio_codec='aac')

    return final_output_path

# Example usage
csv_files = ['GX010883_scores.csv', 'GX020883_scores.csv']
process_multiple_csvs(csv_files, include_overlays=True)  # Default values: highlight_duration=7, include_overlays=True, slow_motion_factor=2
