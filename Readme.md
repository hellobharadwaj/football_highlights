# Football Highlights Creator with Hand Gesture Recognition

This project uses hand gesture recognition to create football highlight videos. Based on hand gestures, the program identifies when each team scores and compiles highlights accordingly. The project utilizes OpenCV and MediaPipe for gesture recognition and produces a highlights video available on our [YouTube channel](https://www.youtube.com/@football_pune).

## Overview

The project is divided into two scripts:
1. **`compute_score.py`**: Processes video files to detect hand gestures and generate a CSV file with timestamps and scores.
2. **`hl_overlay.py`**: Uses the generated CSV file to create a highlights video with overlays, displaying team scores, event timestamps, and more.

The program identifies specific hand gestures to track scoring events:
- **Index Finger Gesture (1)** - Indicates a goal for the **home team**.
- **V Sign Gesture (2)** - Indicates a goal for the **away team**.

## Features

1. **Gesture Recognition with OpenCV and MediaPipe**:
   - Detects specific hand gestures from video frames.
   - Each gesture represents a scoring event or highlight mark.

2. **Highlight Compilation with Overlays**:
   - Extracts and compiles video clips based on detected gestures, with overlays showing team names, scores, and timestamps.

3. **Slow Motion and Video Effects**:
   - Includes options for slow-motion effects to enhance key moments in highlights.
   - Adds text and background color overlays for clarity.

4. **CSV and Video Export**:
   - Exports timestamps and scores in a CSV file.
   - Generates a final highlight video based on CSV data, ready to share on platforms.

## Code Summary

### `compute_score.py`
- **Gesture Detection**: Detects index finger, V sign, and little finger gestures for scoring events in each video file.
- **CSV Export**: Generates a CSV file with timestamps and scores for both teams.
- **Review Process**: Before generating highlights, review the generated CSV files, correct any errors, and update the starting scores if needed.

### `hl_overlay.py`
- **Overlay Generation**: Uses CSV data to create highlight clips with overlays for team scores and timestamps.
- **Highlight Video Creation**: Combines clips into a single video with optional slow motion and overlays.
- **Video Splitting for Mobile Format**: Utilizes `ffmpeg` to create mobile-friendly video segments.

## Getting Started

1. **Setup**:
   - Clone the repository and install required dependencies:
     ```bash
     git clone https://github.com/hellobharadwaj/football_highlights.git
     cd football_highlights
     pip install -r requirements.txt
     ```

2. **Run the Score Computation**:
   - Place video files in the project directory.
   - Run `compute_score.py` to process each video and generate scores:
     ```bash
     python compute_score.py
     ```

3. **Review and Update Scores**:
   - Open the generated CSV files to review timestamps and scores.
   - Make any necessary corrections and update the starting scores for each team if needed.

4. **Create Highlights with Overlays**:
   - Update the filenames in `hl_overlay.py` to match the CSV files in the order they were created.
   - Run `hl_overlay.py` to generate the final highlight videos:
     ```bash
     python hl_overlay.py
     ```

5. **View Results**:
   - Final highlights videos are saved in the same directory.

---

### License
This project is open-sourced under the [MIT License](LICENSE).
