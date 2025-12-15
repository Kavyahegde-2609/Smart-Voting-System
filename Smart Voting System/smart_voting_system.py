import tkinter as tk
import pandas as pd
import pyttsx3
import cv2
import mediapipe as mp
import os
import time

# ================= Text-to-Speech =================
engine = pyttsx3.init()

def speak(text):
    print("[Voice]:", text)
    engine.say(text)
    engine.runAndWait()

# ================= Load/Create Voter Database =================
csv_path = "voter_db.csv"

if not os.path.exists(csv_path):
    df = pd.DataFrame(columns=["aadhaar", "category", "iris_path", "face_path", "voted"])
    df.to_csv(csv_path, index=False)
else:
    df = pd.read_csv(csv_path)

# ================= Aadhaar Verification =================
def verify_aadhaar(aadhaar):
    return df[df["aadhaar"].astype(str) == str(aadhaar)]

# ================= Improved ORB Feature Matching =================
def compare_iris_similarity(img1, img2):
    try:
        # Resize images to same size for better comparison
        img1_resized = cv2.resize(img1, (300, 150))
        img2_resized = cv2.resize(img2, (300, 150))
        
        gray1 = cv2.cvtColor(img1_resized, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2_resized, cv2.COLOR_BGR2GRAY)

        # Use ORB for feature detection
        orb = cv2.ORB_create(nfeatures=1000)
        kp1, des1 = orb.detectAndCompute(gray1, None)
        kp2, des2 = orb.detectAndCompute(gray2, None)

        if des1 is None or des2 is None:
            return 0

        # Use BFMatcher for matching
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(des1, des2)
        
        # Sort matches by distance
        matches = sorted(matches, key=lambda x: x.distance)

        # Calculate match score
        if len(matches) > 0:
            good_matches = [m for m in matches if m.distance < 50]
            match_score = (len(good_matches) / max(len(kp1), len(kp2))) * 100
            return match_score
        
        return 0
    except Exception as e:
        print(f"Error in comparison: {e}")
        return 0

# ================= Improved Eye Capture for Voting =================
def capture_eye_for_voting():
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        speak("Webcam error.")
        return None

    speak("Please open your eyes clearly and look at the camera.")

    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True, min_detection_confidence=0.7)

    start_time = time.time()
    stable_frames = 0
    required_stable_frames = 5

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

        if results.multi_face_landmarks:
            for landmarks in results.multi_face_landmarks:
                h, w = frame.shape[:2]

                # Get eye region landmarks
                left = landmarks.landmark[33]
                right = landmarks.landmark[263]
                top = landmarks.landmark[159]
                bottom = landmarks.landmark[145]

                # Calculate eye region with padding
                x1 = int(min(left.x, right.x) * w) - 50
                x2 = int(max(left.x, right.x) * w) + 50
                y1 = int(top.y * h) - 60
                y2 = int(bottom.y * h) + 60

                # Ensure coordinates are within frame boundaries
                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(w, x2)
                y2 = min(h, y2)

                eye_frame = frame[y1:y2, x1:x2]

                if eye_frame.size == 0:
                    continue

                # Display eye region in separate window
                display_eye = cv2.resize(eye_frame, (400, 200))
                cv2.imshow("Eye Region View", display_eye)

                # Calculate eye openness
                eye_open_dist = abs(top.y - bottom.y)
                
                if eye_open_dist > 0.03 and eye_frame.shape[0] > 50 and eye_frame.shape[1] > 100:
                    stable_frames += 1
                    
                    # Draw green rectangle on main frame
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, f"Stable: {stable_frames}/{required_stable_frames}", 
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                    if stable_frames >= required_stable_frames:
                        captured = eye_frame.copy()
                        speak("Eye captured successfully.")
                        cv2.waitKey(500)
                        cap.release()
                        cv2.destroyAllWindows()
                        return captured
                else:
                    stable_frames = 0
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(frame, "Open eyes wider", (10, 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # Timeout after 10 seconds
        if time.time() - start_time > 10:
            speak("Capture timeout. Please try again.")
            break

        cv2.imshow("Adjust Your Eyes", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return None

# ================= Voting Logic with Duplicate Prevention =================
def process_voting(aadhaar):
    global df

    voter = verify_aadhaar(aadhaar)

    if voter.empty:
        speak("Aadhaar not found in database.")
        tk.messagebox.showerror("Error", "Aadhaar number not found in database!")
        return

    # Check if already voted (DUPLICATE PREVENTION)
    if voter.iloc[0]["voted"] == "yes":
        speak("You have already voted. Duplicate voting is not allowed.")
        tk.messagebox.showerror("Already Voted", "This Aadhaar has already voted!\nDuplicate voting is not allowed.")
        return

    category = voter.iloc[0]["category"]
    
    # Process based on category
    if category == "blind":
        # For blind voters, just verify Aadhaar and mark as voted
        speak("Blind voter verified. Proceeding to vote.")
        df.loc[df["aadhaar"].astype(str) == str(aadhaar), "voted"] = "yes"
        df.to_csv(csv_path, index=False)
        speak("Vote cast successfully.")
        tk.messagebox.showinfo("Success", "Vote cast successfully!")
        
    elif category == "normal":
        # For normal voters, verify with eye biometric
        iris_path = voter.iloc[0]["iris_path"]

        if not iris_path or iris_path == "" or not os.path.exists(iris_path):
            speak("No registered eye biometric found. Please register first.")
            tk.messagebox.showerror("Error", "No registered eye biometric found!\nPlease complete registration first.")
            return

        speak("Capturing eye for verification.")
        captured_eye = capture_eye_for_voting()

        if captured_eye is None:
            speak("Eye capture failed. Please try again.")
            tk.messagebox.showerror("Capture Failed", "Eye capture failed!\nPlease try again.")
            return

        # Load registered eye image
        registered_img = cv2.imread(iris_path)
        
        if registered_img is None:
            speak("Error loading registered biometric.")
            tk.messagebox.showerror("Error", "Error loading registered biometric!")
            return
        
        # Compare captured eye with registered eye
        match_score = compare_iris_similarity(registered_img, captured_eye)
        
        print(f"Match Score: {match_score}")

        # Threshold for matching (adjusted for better accuracy)
        if match_score >= 35:
            df.loc[df["aadhaar"].astype(str) == str(aadhaar), "voted"] = "yes"
            df.to_csv(csv_path, index=False)
            speak("Eye matched successfully. Vote cast successfully.")
            tk.messagebox.showinfo("Success", f"Eye Matched! (Score: {match_score:.1f}%)\n\nVote cast successfully!")
        else:
            speak("Eye biometric did not match. Voting denied.")
            tk.messagebox.showerror("Match Failed", f"Eye biometric did not match! (Score: {match_score:.1f}%)\n\nVoting denied for security reasons.")
    else:
        speak("Invalid category in database.")
        tk.messagebox.showerror("Error", "Invalid voter category in database!")

# ================= Start GUI =================
def start_voting_gui():
    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.configure(bg="light sky blue")
    root.title("Smart Voting System")

    speak("Welcome to the Smart Voting System")

    tk.Label(
        root,
        text="Welcome to the Smart Voting System",
        font=("Arial", 32, "bold"),
        bg="light sky blue",
        fg="black"
    ).pack(pady=40)

    frame = tk.Frame(root, bg="light sky blue")
    frame.pack(pady=50)

    tk.Label(
        frame,
        text="Enter Aadhaar Number:",
        font=("Arial", 20),
        bg="light sky blue"
    ).pack(pady=10)

    aadhaar_entry = tk.Entry(frame, font=("Arial", 20), width=25)
    aadhaar_entry.pack(pady=10)

    def on_submit():
        aadhaar = aadhaar_entry.get().strip()
        if not aadhaar:
            speak("Please enter Aadhaar number.")
            tk.messagebox.showerror("Error", "Please enter Aadhaar number!")
            return
        process_voting(aadhaar)

    tk.Button(
        frame,
        text="Submit",
        font=("Arial", 18),
        bg="#4CAF50",
        fg="white",
        command=on_submit,
        width=20
    ).pack(pady=20)

    tk.Button(
        frame,
        text="Exit",
        font=("Arial", 16),
        bg="red",
        fg="white",
        command=root.destroy,
        width=20
    ).pack(pady=10)

    # ================= Admin Panel Button =================
    def open_admin_login():
        try:
            from admin_panel import admin_login
            admin_login()
        except Exception as e:
            print("Error opening admin panel:", e)
            tk.messagebox.showerror("Error", "Could not open admin panel!")

    tk.Button(
        frame,
        text="Admin Panel",
        font=("Arial", 16),
        bg="#2980B9",
        fg="white",
        command=open_admin_login,
        width=20
    ).pack(pady=10)

    root.mainloop()

# ================= Run =================
if __name__ == "__main__":
    start_voting_gui()
