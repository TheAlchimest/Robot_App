# Video Eye Player - Continuous Loop with Error Handling
import cv2
import os
import time

def checkVideoFile(video_path):
    """Check if video file exists and get info"""
    print("🔍 Checking file...")
    print(f"   Current path: {os.getcwd()}")
    print(f"   Required path: {video_path}")
    
    if not os.path.exists(video_path):
        print(f"❌ File not found: {video_path}")
        print("\n💡 Try these solutions:")
        print("   1. Make sure Resources folder exists")
        print("   2. Make sure file name is exactly eye_01.mp4")
        print("   3. Try using absolute path")
        
        # Search for the file
        print("\n🔎 Searching for mp4 files...")
        if os.path.exists('Resources'):
            files = os.listdir('Resources')
            mp4_files = [f for f in files if f.endswith('.mp4') or f.endswith('.MP4')]
            if mp4_files:
                print(f"   Found mp4 files: {mp4_files}")
            else:
                print("   No mp4 files found in Resources folder")
        else:
            print("   Resources folder does not exist!")
        return False
    
    print("✅ File found!")
    print(f"   File size: {os.path.getsize(video_path) / (1024*1024):.2f} MB")
    return True


def playEyeVideo(video_path='Resources/eye_videos/01.mp4', fullscreen=True):
    """
    Play eye video in continuous loop with detailed error checking
    
    Args:
        video_path: Path to video file
        fullscreen: Display in fullscreen mode
    """
    
    # Check if file exists
    if not checkVideoFile(video_path):
        return
    
    # Open video file
    print("\n📹 Attempting to open video...")
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print("❌ Failed to open video!")
        print("\n💡 Possible causes:")
        print("   1. Unsupported video format (try converting to H.264)")
        print("   2. Video is corrupted or incomplete")
        print("   3. OpenCV is not installed correctly")
        print("\n🔧 Quick fix: Use ffmpeg to convert video:")
        print(f"   ffmpeg -i {video_path} -c:v libx264 -c:a aac Resources/eye_fixed.mp4")
        return
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
    codec = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
    
    print("✅ Video opened successfully!")
    print(f"\n📊 Video Information:")
    print(f"   Resolution: {width}x{height}")
    print(f"   FPS: {fps}")
    print(f"   Total Frames: {total_frames}")
    print(f"   Duration: {total_frames/fps:.2f} seconds")
    print(f"   Codec: {codec}")
    
    # Create window
    window_name = 'Eye Video'
    cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
    
    if fullscreen:
        cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    
    # Calculate delay between frames for proper playback speed
    delay = int(1000 / fps) if fps > 0 else 30
    
    frame_count = 0
    loop_count = 0
    
    print(f"\n▶️ Starting continuous playback...")
    print(f"   Press 'q' or ESC to exit\n")
    
    try:
        while True:
            ret, frame = cap.read()
            
            # If video ended, restart from beginning
            if not ret:
                loop_count += 1
                print(f"🔄 Restarting - Loop #{loop_count}")
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                frame_count = 0
                continue
            
            # Display frame
            cv2.imshow(window_name, frame)
            frame_count += 1
            
            # Check for exit key
            key = cv2.waitKey(delay) & 0xFF
            if key == ord('q') or key == 27:  # 'q' or ESC
                print(f"\n⏹️ Stopped by user")
                print(f"   Total loops played: {loop_count}")
                break
    
    except KeyboardInterrupt:
        print(f"\n⚠️ Interrupted (Ctrl+C)")
        print(f"   Total loops played: {loop_count}")
    
    except Exception as e:
        print(f"\n❌ Error during playback: {e}")
    
    finally:
        # Clean up
        cap.release()
        cv2.destroyAllWindows()
        print("✅ Video player closed")


def playEyeVideoWithPosition(video_path='Resources/eye_videos/01.mp4', x_offset=-1920, y_offset=0):
    """
    Play eye video in continuous loop with custom window position
    
    Args:
        video_path: Path to video file
        x_offset: X position of window (use -1920 for second monitor)
        y_offset: Y position of window
    """
    
    if not checkVideoFile(video_path):
        return
    
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"❌ Failed to open video: {video_path}")
        return
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"\n▶️ Playing on second monitor...")
    print(f"   Position: X={x_offset}, Y={y_offset}")
    print(f"   Press 'q' or ESC to exit\n")
    
    window_name = 'Eye Video'
    cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    
    delay = int(1000 / fps) if fps > 0 else 30
    loop_count = 0
    
    try:
        while True:
            ret, frame = cap.read()
            
            if not ret:
                loop_count += 1
                print(f"🔄 Loop #{loop_count}")
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            
            cv2.imshow(window_name, frame)
            cv2.moveWindow(window_name, x_offset, y_offset)
            
            key = cv2.waitKey(delay) & 0xFF
            if key == ord('q') or key == 27:
                print(f"\n⏹️ Stopped")
                break
    
    except KeyboardInterrupt:
        print(f"\n⚠️ Interrupted")
    
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("✅ Closed")


def playEyeVideoResized(video_path='Resources/eye_videos/01.mp4', scale=1.0):
    """
    Play eye video with custom size scaling
    
    Args:
        video_path: Path to video file
        scale: Scaling factor (1.0 = original size, 0.5 = half size, 2.0 = double size)
    """
    
    if not checkVideoFile(video_path):
        return
    
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"❌ Failed to open video: {video_path}")
        return
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) * scale)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) * scale)
    
    print(f"\n▶️ Playing at {int(scale*100)}% size ({width}x{height})")
    print(f"   Press 'q' or ESC to exit\n")
    
    window_name = 'Eye Video'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, width, height)
    
    delay = int(1000 / fps) if fps > 0 else 30
    
    try:
        while True:
            ret, frame = cap.read()
            
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            
            # Resize frame
            resized_frame = cv2.resize(frame, (width, height))
            
            cv2.imshow(window_name, resized_frame)
            
            key = cv2.waitKey(delay) & 0xFF
            if key == ord('q') or key == 27:
                break
    
    except KeyboardInterrupt:
        print(f"\n⚠️ Interrupted")
    
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("✅ Closed")


def simplePlay(video_path='Resources/eye_videos/01.mp4'):
    """Simple and fast video player"""
    
    if not os.path.exists(video_path):
        print(f"❌ File not found: {video_path}")
        
        # Try to find mp4 files
        if os.path.exists('Resources'):
            files = [f for f in os.listdir('Resources') if f.endswith(('.mp4', '.MP4'))]
            if files:
                print(f"\n🔎 Available files in Resources:")
                for i, f in enumerate(files, 1):
                    print(f"   {i}. {f}")
                
                choice = input("\nSelect file number (or Enter to exit): ").strip()
                if choice.isdigit() and 1 <= int(choice) <= len(files):
                    video_path = f"Resources/{files[int(choice)-1]}"
                else:
                    return
            else:
                print("   No video files found in Resources")
                return
        else:
            print("   Resources folder does not exist!")
            return
    
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"❌ Failed to open: {video_path}")
        print("\n💡 Try converting the video using:")
        print("   ffmpeg -i [input] -c:v libx264 -c:a aac [output]")
        return
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    delay = int(1000 / fps) if fps > 0 else 30
    
    cv2.namedWindow('Eye', cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty('Eye', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    
    print(f"▶️ Playing: {video_path}")
    print("   Press 'q' to exit\n")
    
    loop_count = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                loop_count += 1
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            
            cv2.imshow('Eye', frame)
            
            if cv2.waitKey(delay) & 0xFF == ord('q'):
                break
    except:
        pass
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print(f"✅ Closed (looped {loop_count} times)")


# Main execution
if __name__ == "__main__":
    print("\n" + "="*60)
    print("👁️  Eye Video Player - Continuous Loop")
    print("="*60)
    print("\nChoose playback mode:")
    print("1. Fullscreen (default)")
    print("2. Fullscreen on second monitor")
    print("3. Windowed mode with custom size")
    print("4. Simple and fast playback")
    
    choice = input("\nEnter choice (1-4) [default: 4]: ").strip()
    
    if choice in ["1", "2", "3"]:
        video_file = input("Enter video filename [default: Resources/eye_videos/01.mp4]: ").strip()
        if not video_file:
            video_file = "Resources/eye_videos/01.mp4"
    else:
        video_file = "Resources/eye_videos/01.mp4"
    
    print("\n")
    
    if choice == "1":
        playEyeVideo(video_file, fullscreen=True)
    elif choice == "2":
        x = input("Enter X offset [-1920 for second monitor]: ").strip()
        x_offset = int(x) if x else -1920
        playEyeVideoWithPosition(video_file, x_offset=x_offset)
    elif choice == "3":
        scale = input("Enter scale (0.5 = half, 2.0 = double) [1.0]: ").strip()
        scale = float(scale) if scale else 1.0
        playEyeVideoResized(video_file, scale=scale)
    else:
        # Default: Simple and fast
        simplePlay(video_file)