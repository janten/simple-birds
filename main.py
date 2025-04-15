import os
import shutil
import hashlib
import logging
import requests
import subprocess
from datetime import datetime
from threading import Thread  # Changed from multiprocessing.Process
from birdnetlib.analyzer import Analyzer
from birdnetlib.species import SpeciesList
from birdnetlib import Recording
from prometheus_client import start_http_server, Histogram, Counter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Read the AUDIO_STREAMS environment variable
audio_streams = os.getenv(
    "AUDIO_STREAMS",
    "rtsp://admin:pass@cam-url.com/Preview_01_main",
)

lat = os.getenv("LATITUDE", "51.7749")
lon = os.getenv("LONGITUDE", "7.2229")
locale = os.getenv("LOCALE", "en")

c = Counter(
    "audio_analyzed_duration_seconds",
    "Seconds of audio data analyzed",
)

# Directory to save the audio files
temp_dir = "temp"
# Empty temp dir
if os.path.exists(temp_dir):
    shutil.rmtree(temp_dir)
os.makedirs(temp_dir, exist_ok=True)
output_dir = "incoming"
os.makedirs(output_dir, exist_ok=True)


# Function to start an ffmpeg process for a stream
def record_stream(stream_url):
    hash = hashlib.sha1(stream_url.encode()).hexdigest()[:8]
    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        output_file = os.path.join(temp_dir, f"stream_{hash}_{timestamp}.mp3")
        command = [
            "ffmpeg",
            "-i",
            stream_url,
            "-t",
            "15",
            "-acodec",
            "libmp3lame",
            "-y",
            output_file,
        ]
        logging.info(f"Running command: {' '.join(command)}")
        subprocess.run(command, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        logging.info(f"Recorded 15 seconds of audio from {stream_url} to {output_file}")
        if os.path.exists(output_file):
            # Move the file to the incoming directory
            new_file_name = f"{hash}_{timestamp}.mp3"
            new_file_path = os.path.join(output_dir, new_file_name)
            os.rename(output_file, new_file_path)
            logging.info(f"Moved {output_file} to {new_file_path}")
            c.inc(15.0) # Increment the counter by 15 seconds


if __name__ == "__main__":
    h = Histogram(
        "detection_confidence",
        "Detection confidence by bird species",
        labelnames=["common_name", "scientific_name"],
        buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
    )

    # Download species translations
    url = f"https://raw.githubusercontent.com/birdnet-team/BirdNET-Analyzer/refs/heads/main/birdnet_analyzer/labels/V2.4/BirdNET_GLOBAL_6K_V2.4_Labels_{locale}.txt"
    r = requests.get(url)
    species_names = {}
    if r.status_code == 200:
        species_names = {line.split("_")[0]: line.split("_")[1] for line in r.text.splitlines() if "_" in line}

    start_http_server(8000)

    streams = [x.strip() for x in audio_streams.split(",")]
    logging.info("Audio streams: %s", streams)

    # Check if any stream is provided
    if not streams or all(stream.strip() == "" for stream in streams):
        logging.error("No audio streams provided.")
        exit(1)

    # Start recording for each stream
    threads = []  # Changed from processes to threads
    for stream in streams:
        thread = Thread(target=record_stream, args=(stream,))  # Changed to Thread
        thread.start()
        threads.append(thread)
        logging.info(f"Started recording thread for stream: {stream}")

    # In the main thread, process the incoming files
    analyzer = Analyzer(version="2.4.1")
    while True:
        # List all files in the incoming directory
        for filename in os.listdir(output_dir):
            file_path = os.path.join(output_dir, filename)
            logging.info(f"Processing file: {file_path}")
            recording = Recording(
                analyzer,
                file_path,
                lat=lat,
                lon=lon,
                date=datetime.now(),  # use date or week_48
                return_all_detections=True,
            )
            try:
                recording.analyze()
            except Exception as e:
                logging.error(f"Error analyzing {file_path}: {e}")
                pass

            # Save detections to the database
            for detection in recording.detections:
                h.labels(
                    common_name=species_names.get(detection["scientific_name"], ""),
                    scientific_name=detection["scientific_name"],
                ).observe(detection["confidence"])

            logging.info(f"Detected {len(recording.detections)} birds in {filename}")
            os.remove(file_path)  # Uncomment to delete the file after processing
