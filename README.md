# Simple BirdNET Integration

This project provides a simple and straightforward way to use BirdNET with existing cameras or other audio sources. It is designed to record audio streams, analyze them for bird species using BirdNET, and expose the results via a Prometheus endpoint. This allows the data to be consumed, saved, and analyzed elsewhere.

## Features

- Records audio from one or more streams (e.g., RTSP streams from cameras).
- Analyzes the audio using BirdNET to detect bird species.
- Exposes detection results as Prometheus metrics for easy integration with monitoring and analysis tools.

## Requirements

- Python 3.8 or higher
- FFmpeg installed and available in the system's PATH
- Prometheus server (optional, for consuming metrics)

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/your-repo/simple-birdnet.git
   cd simple-birdnet
   ```

2. Install the required Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Ensure FFmpeg is installed:
   ```bash
   sudo apt-get install ffmpeg
   ```

## Configuration

The application is configured using environment variables:

- `AUDIO_STREAMS`: A comma-separated list of audio stream URLs (e.g., RTSP streams).
- `LATITUDE`: The latitude of the recording location (default: `51.7749`).
- `LONGITUDE`: The longitude of the recording location (default: `7.2229`).
- `LOCALE`: The locale for species translations (default: `en`).

Example:
```bash
export AUDIO_STREAMS="rtsp://camera1/stream,rtsp://camera2/stream"
export LATITUDE="40.7128"
export LONGITUDE="-74.0060"
export LOCALE="en"
```

## Usage

1. Start the application:
   ```bash
   python main.py
   ```

2. The application will:
   - Record 15-second audio clips from the configured streams.
   - Analyze the audio for bird species using BirdNET.
   - Expose detection results as Prometheus metrics on port `8000`.

3. Configure your Prometheus server to scrape metrics from `http://<host>:8000/metrics`.

## Prometheus Metrics

The following metrics are exposed:

- `audio_analyzed_duration_seconds`: Total seconds of audio analyzed.
- `detection_confidence`: Detection confidence by bird species, labeled with `common_name` and `scientific_name`.

## Notes

- This project is intended for simple use cases and does not include advanced features like database storage or web interfaces.
- Audio files are temporarily stored in the `temp` and `incoming` directories and are deleted after processing.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
