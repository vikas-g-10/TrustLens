"""
Generates clean, lightweight H.264 MP4 videos for the 10 demo shorts in public/demo-videos.
Each video is ~50-80 KB, decodable by any modern browser and OpenCV.
"""
import os
import cv2
import numpy as np

def generate_all():
    os.makedirs('public/demo-videos', exist_ok=True)
    W, H = 360, 640
    FPS = 10
    N_FRAMES = 30  # 3.0 seconds

    demos = [
        {
            'id': 'legit-1',
            'title': 'Street market ambience',
            'sub': 'Fresh Produce & Fruit Stalls',
            'bg': (25, 45, 30),
            'accent': (40, 180, 100),
        },
        {
            'id': 'legit-2',
            'title': 'Local cricket match',
            'sub': 'Amateur Cricket Match - Over 14',
            'bg': (20, 40, 20),
            'accent': (60, 220, 120),
        },
        {
            'id': 'legit-3',
            'title': 'Rain on a city road',
            'sub': 'Monsoon Downpour - MG Road',
            'bg': (35, 30, 20),
            'accent': (220, 180, 80),
        },
        {
            'id': 'legit-4',
            'title': 'Campus cultural event',
            'sub': 'University Annual Fest 2026',
            'bg': (30, 15, 40),
            'accent': (200, 100, 220),
        },
        {
            'id': 'legit-5',
            'title': 'Traffic jam timelapse',
            'sub': 'Ring Road Rush Hour Traffic',
            'bg': (20, 25, 45),
            'accent': (80, 140, 240),
        },
        {
            'id': 'ai-1',
            'title': 'Synthetic city flood',
            'sub': 'CGI Flood Simulation - Flash Alert',
            'bg': (45, 20, 20),
            'accent': (80, 80, 240),
        },
        {
            'id': 'ai-2',
            'title': 'Synthetic celebrity speech',
            'sub': 'Deepfake Voice & Video Simulation',
            'bg': (40, 15, 35),
            'accent': (120, 60, 230),
        },
        {
            'id': 'ai-3',
            'title': 'Synthetic wildlife encounter',
            'sub': 'AI-Rendered Leopard in Suburbs',
            'bg': (35, 25, 15),
            'accent': (60, 160, 230),
        },
        {
            'id': 'false-1',
            'title': 'Old clip, new claim',
            'sub': 'Recycled 2018 Archive Footage',
            'bg': (40, 30, 10),
            'accent': (50, 180, 220),
        },
        {
            'id': 'false-2',
            'title': 'Misattributed location',
            'sub': 'Rotterdam Port (Claimed: Mumbai)',
            'bg': (40, 20, 30),
            'accent': (70, 100, 240),
        },
    ]

    fourcc = cv2.VideoWriter_fourcc(*'avc1')

    for d in demos:
        out_path = f"public/demo-videos/{d['id']}.mp4"
        w = cv2.VideoWriter(out_path, fourcc, FPS, (W, H))
        if not w.isOpened():
            w = cv2.VideoWriter(out_path, cv2.VideoWriter_fourcc(*'mp4v'), FPS, (W, H))

        for f in range(N_FRAMES):
            img = np.zeros((H, W, 3), dtype=np.uint8)
            # Vertical gradient
            for y in range(H):
                ratio = y / float(H)
                c = [int(d['bg'][i] * (1.0 - ratio * 0.6) + 12 * ratio) for i in range(3)]
                img[y, :] = c

            # Subtle grid
            offset = int((f / float(N_FRAMES)) * 40)
            for y_line in range(0, H, 40):
                cv2.line(img, (0, (y_line + offset) % H), (W, (y_line + offset) % H), (30, 40, 50), 1)

            # Central card banner
            cv2.rectangle(img, (18, 170), (W - 18, 470), (14, 20, 32), -1)
            cv2.rectangle(img, (18, 170), (W - 18, 470), d['accent'], 2)

            # Dynamic pulse circle
            radius = int(32 + 6 * np.sin(f * 0.45))
            cv2.circle(img, (W // 2, 250), radius, d['accent'], -1)
            cv2.circle(img, (W // 2, 250), radius + 6, (255, 255, 255), 1)

            # Tag
            is_ai = 'ai' in d['id']
            is_false = 'false' in d['id']
            tag = 'AI-GENERATED DEMO' if is_ai else ('MISATTRIBUTED DEMO' if is_false else 'AUTHENTIC CLIP DEMO')
            tag_color = (90, 90, 240) if is_ai else ((60, 180, 240) if is_false else (70, 220, 120))
            cv2.putText(img, tag, (28, 205), cv2.FONT_HERSHEY_SIMPLEX, 0.42, tag_color, 1, cv2.LINE_AA)

            # Title
            cv2.putText(img, d['title'], (28, 330), cv2.FONT_HERSHEY_SIMPLEX, 0.60, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(img, d['sub'], (28, 365), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (170, 185, 200), 1, cv2.LINE_AA)

            # Counter
            cv2.putText(img, f"TrustLens Demo Clip - Frame {f+1}/{N_FRAMES}", (28, 420), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (110, 130, 150), 1, cv2.LINE_AA)
            cv2.putText(img, "Verification Sample - 3.0s @ 10fps", (28, 445), cv2.FONT_HERSHEY_SIMPLEX, 0.32, (90, 110, 130), 1, cv2.LINE_AA)

            # Top branding
            cv2.putText(img, "TRUSTLENS FORENSICS", (20, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 230, 255), 2, cv2.LINE_AA)
            cv2.putText(img, f"SOURCE: {d['id']}.mp4", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (120, 140, 160), 1, cv2.LINE_AA)

            w.write(img)
        w.release()
        size_kb = os.path.getsize(out_path) / 1024
        print(f"Generated {out_path}: {size_kb:.1f} KB")

if __name__ == '__main__':
    generate_all()
