# Football Highlights Creator with Hand Gesture Recognition

This project uses hand gesture recognition to create football highlight videos. Based on hand gestures, the program identifies when each team scores and compiles highlights accordingly. The project utilizes OpenCV and MediaPipe for gesture recognition and produces a highlights video available on our [YouTube channel](https://www.youtube.com/@football_pune).

## Overview

The program processes recorded football games and recognizes specific hand gestures to track scoring events:
- **Index Finger Gesture (1)** - Indicates a goal for the **home team**.
- **V Sign Gesture (2)** - Indicates a goal for the **away team**.

Each recognized gesture is timestamped and stored, enabling automatic highlight generation.

## Features

1. **Gesture Recognition with OpenCV and MediaPipe**:
   - Uses MediaPipe’s hand tracking to detect specific hand gestures.
   - Each gesture corresponds to a scoring event for a team or a highlight mark.

2. **Highlight Compilation**:
   - Extracts clips based on detected gestures, generating short highlight videos.
   - Adds overlays for team names, scores, and time stamps.

3. **Slow Motion and Video Effects**:
   - Allows slow-motion effects to enhance key moments.
   - Adds text and background color overlays for visual clarity.

4. **CSV and Video Export**:
   - Exports timestamps and events in a CSV file.
   - Generates final highlight videos that can be shared directly on platforms.

## Code Summary

- **Hand Gesture Detection**: Detects index finger, V sign, and little finger gestures for scoring events.
- **Highlight Video Creation**: Combines clips based on event times into one video with optional slow motion.
- **Video Splitting for Mobile Format**: Uses `ffmpeg` to create mobile-friendly video segments for easy viewing.

## Getting Started

1. **Setup**:
   - Clone the repository and install required dependencies:
     ```bash
     git clone https://github.com/hellobharadwaj/football_highlights.git
     cd football_highlights
     pip install -r requirements.txt
     ```

2. **Run the Program**:
   - Place video files in the project directory.
   - Run the main script to process each video and generate highlights:
     ```bash
     python main.py
     ```

3. **View Results**:
   - Results are saved as video files in the same directory.

---

### License
This project is open-sourced under the [MIT License](LICENSE).
