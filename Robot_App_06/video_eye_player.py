# video_eye_player.py
# -------------------------------------------------------------------
# Optional eye video player. Disabled by default (via Config.ENABLE_EYE_VIDEO).
# Safe on headless systems; exits quietly if OpenCV/windowing not available.
# -------------------------------------------------------------------

import os

def playEyeVideo():
    try:
        import cv2
    except Exception as e:
        print(f"[Eye] OpenCV not available: {e}")
        return

    video_path = os.getenv("EYE_VIDEO_PATH", "")
    if not video_path or not os.path.isfile(video_path):
        print("[Eye] No EYE_VIDEO_PATH set or file not found. Skipping.")
        return

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("[Eye] Cannot open video.")
        return

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            cv2.imshow("Eye", frame)
            # Exit on ESC
            if cv2.waitKey(10) & 0xFF == 27:
                break
    except Exception as e:
        print(f"[Eye] player error: {e}")
    finally:
        cap.release()
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass
