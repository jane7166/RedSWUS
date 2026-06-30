# ORT: Unintended Text Recognition from Eyeglass Reflections in Video Conferencing Environments

🔗 ORT: [https://redswus-ort.vercel.app](https://redswus-ort.vercel.app)

## Abstract

ORT is a research demo that explores unintended text recognition from eyeglass reflections in video conferencing environments. The system accepts a video or image input, detects glasses regions, preprocesses reflected text areas, and applies scene text recognition to estimate visible text candidates.

This repository contains a Next.js frontend for the demo interface and a Flask backend for the analysis pipeline.

## Installation

### Prerequisites

- Python 3.9+ is recommended.
- Node.js 18+ is recommended.
- Model weights are required for local inference:
  - `RedSWUS-flask/pt/yolo.pt`
  - `RedSWUS-flask/pt/best_model.pth`

### Backend: Flask

```bash
cd RedSWUS-flask
python3 -m venv venv
source venv/bin/activate
pip install -r ../requirements.txt
```

The Flask server uses SQLite by default and creates `video_analysis.db` automatically when the app starts.

### Frontend: Next.js

```bash
cd RedSWUS-front
npm install
```

## Run demo

Start the Flask backend first:

```bash
cd RedSWUS-flask
source venv/bin/activate
python app.py
```

The backend runs at:

```text
http://localhost:5001
```

In a second terminal, start the Next.js frontend:

```bash
cd RedSWUS-front
npm run dev
```

Open the local demo page:

```text
http://localhost:3000
```

Upload a video or image from the demo page. The frontend sends the file to the Flask endpoint:

```text
POST http://localhost:5001/full_pipeline
```

## Result

The demo pipeline returns recognized text candidates from detected eyeglass reflection regions. During processing, the backend performs:

1. Video or image upload
2. Glasses detection with YOLO
3. Reflection-region preprocessing
4. Text-area detection with Detectron2
5. Scene text recognition with PARSeq

Generated intermediate files and outputs are stored by the Flask backend under local runtime folders such as `uploaded_videos/` and `mp4_to_img/`.

## Acknowledgements

This project builds on open-source tools and frameworks including Flask, Next.js, PyTorch, Detectron2, YOLOv9, PARSeq, OpenCV, and Vercel.
