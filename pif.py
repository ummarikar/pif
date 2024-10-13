import cv2
import pytesseract
import re
from PIL import Image

# Function to extract frames from video, using the video's own frame rate
def extract_frames(video_path):
    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    frames = []
    fps = cap.get(cv2.CAP_PROP_FPS)  # Capture frame rate from video metadata
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Capture frame at 1 frame per second (adjust according to frame rate)
        if frame_count % int(fps) == 0:
            frames.append((frame_count / fps, frame))  # Save timestamp and frame
        frame_count += 1
        
    cap.release()
    return frames  # Returns a list of (timestamp, frame) tuples

# Function to extract text from a frame using Tesseract OCR
def extract_text_from_frame(frame):
    pil_image = Image.fromarray(frame)  # Convert to PIL Image
    text = pytesseract.image_to_string(pil_image)  # Perform OCR
    return text

# Function to detect personal information (emails, passwords) using regex
def find_pii(text):
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+'    
    emails = re.findall(email_pattern, text)
    
    password_pattern = r'password:?\s*\S+'
    passwords = re.findall(password_pattern, text)
    
    return emails, passwords

# Main function to process the video and find timestamps with PII
def process_video_for_pii(video_path):
    frames = extract_frames(video_path)
    pii_timestamps = []

    for timestamp, frame in frames:
        text = extract_text_from_frame(frame)
        print("text: ", text)
        emails, passwords = find_pii(text)
        
        if emails or passwords:
            pii_timestamps.append({
                "timestamp": timestamp,
                "emails": emails,
                "passwords": passwords
            })
    
    return merge_consecutive_timestamps(pii_timestamps)

# Function to merge consecutive timestamps into time ranges
def merge_consecutive_timestamps(pii_timestamps, threshold=1):
    if not pii_timestamps:
        return []
    
    time_ranges = []
    current_range = {
        "start": pii_timestamps[0]["timestamp"],
        "end": pii_timestamps[0]["timestamp"],
        "emails": pii_timestamps[0]["emails"],
        "passwords": pii_timestamps[0]["passwords"]
    }
    
    for i in range(1, len(pii_timestamps)):
        current_timestamp = pii_timestamps[i]["timestamp"]
        prev_timestamp = pii_timestamps[i-1]["timestamp"]
        
        if current_timestamp - prev_timestamp <= threshold:  # If within 1 second, extend range
            current_range["end"] = current_timestamp
            current_range["emails"].extend(pii_timestamps[i]["emails"])
            current_range["passwords"].extend(pii_timestamps[i]["passwords"])
        else:
            time_ranges.append(current_range)
            current_range = {
                "start": current_timestamp,
                "end": current_timestamp,
                "emails": pii_timestamps[i]["emails"],
                "passwords": pii_timestamps[i]["passwords"]
            }
    
    time_ranges.append(current_range)  # Append the last range
    return time_ranges

# Example usage
if __name__ == "__main__":
    video_path = 'myclip.mov'
    result = process_video_for_pii(video_path)
    
    for entry in result:
        print(f"From {entry['start']} to {entry['end']} seconds, found:")
        if entry['emails']:
            print(f"  Emails: {', '.join(set(entry['emails']))}")
        if entry['passwords']:
            print(f"  Passwords: {', '.join(set(entry['passwords']))}")

