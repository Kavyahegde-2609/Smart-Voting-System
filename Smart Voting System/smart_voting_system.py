import tkinter as tk
import pandas as pd
import pyttsx3
import cv2
import mediapipe as mp
import os

# =========== Text-to-Speech ===========
engine = pyttsx3.init()

def speak(text):
    print("[Voice]:", text)
    engine.say(text)
    engine.runAndWait()


# =========== Load/Create Voter Database ===========
csv_path = "voter_db.csv"

if not os.path.exists(csv_path):
    df = pd.DataFrame(columns=["aadhaar", "category", "iris_path", "face_path", "voted"])
    df.to_csv(csv_path, index=False)
else:
    df = pd.read_csv(csv_path)


# =========== Aadhaar Verification ===========
def verify_aadhaar(aadhaar):
    return df[df["aadhaar"].astype(str) == str(aadhaar)]


# =========== ORB Feature Matching ===========
def compare_iris_similarity(img1, img2):
    try:
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

        orb = cv2.ORB_create()
        kp1, des1 = orb.detectAndCompute(gray1, None)
        kp2, des2 = orb.detectAndCompute(gray2, None)

        if des1 is None or des2 is None:
            return 0

        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(des1, des2)

        return len(matches) / max(len(kp1), len(kp2)) * 100

    except:
        return 0


# =========== Focused Eye Capture ===========
def capture_focused_eye():
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        speak("Webcam error.")
        return None

    speak("Please open your eyes clearly.")

    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

        if results.multi_face_landmarks:
            for landmarks in results.multi_face_landmarks:
                h, w = frame.shape[:2]

                left = landmarks.landmark[33]
                right = landmarks.landmark[263]
                top = landmarks.landmark[159]
                bottom = landmarks.landmark[145]

                x1 = int(min(left.x, right.x) * w) - 40
                x2 = int(max(left.x, right.x) * w) + 40
                y1 = int(top.y * h) - 50
                y2 = int(bottom.y * h) + 50

                eye_frame = frame[max(0, y1):min(h, y2), max(0, x1):min(w, x2)]

                if eye_frame.size == 0:
                    continue

                cv2.imshow("Eye Region View", eye_frame)

                eye_open_dist = abs(top.y - bottom.y)

                if eye_open_dist > 0.03:
                    captured = eye_frame.copy()
                    speak("Iris captured.")
                    cv2.waitKey(800)
                    cap.release()
                    cv2.destroyAllWindows()
                    return captured

        cv2.imshow("Adjust Your Eyes", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return None


# =========== Voting Logic ===========
def process_voting(aadhaar):
    global df
    voter = verify_aadhaar(aadhaar)

    if voter.empty:
        speak("Aadhaar not found.")
        return

    if voter.iloc[0]["voted"] == "yes":
        speak("You have already voted.")
        return

    iris_path = voter.iloc[0]["iris_path"]

    if not os.path.exists(iris_path):
        speak("No registered iris found.")
        return

    speak("Capturing iris for matching.")

    captured_eye = capture_focused_eye()
    if captured_eye is None:
        speak("Iris capture failed.")
        return

    registered_img = cv2.imread(iris_path)
    match_score = compare_iris_similarity(registered_img, captured_eye)

    if match_score >= 40:
        df.loc[df["aadhaar"].astype(str) == str(aadhaar), "voted"] = "yes"
        df.to_csv(csv_path, index=False)
        speak("Vote cast successfully.")
    else:
        speak("Iris did not match.")


# =========== Start GUI ===========
def start_voting_gui():
    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.configure(bg="light sky blue")
    root.title("Smart Voting System")

    speak("Welcome to the Smart Voting System")

    tk.Label(root, text="Welcome to the Smart Voting System",
             font=("Arial", 32, "bold"), bg="light sky blue",
             fg="black").pack(pady=40)

    frame = tk.Frame(root, bg="light sky blue")
    frame.pack(pady=50)

    tk.Label(frame, text="Enter Aadhaar Number:",
             font=("Arial", 20), bg="light sky blue").pack(pady=10)

    aadhaar_entry = tk.Entry(frame, font=("Arial", 20), width=25)
    aadhaar_entry.pack(pady=10)

    def on_submit():
        aadhaar = aadhaar_entry.get().strip()
        if not aadhaar:
            speak("Please enter Aadhaar number.")
            return
        process_voting(aadhaar)

    tk.Button(frame, text="Submit", font=("Arial", 18),
              bg="#4CAF50", fg="white", command=on_submit,
              width=20).pack(pady=20)

    tk.Button(frame, text="Exit", font=("Arial", 16),
              bg="red", fg="white", command=root.destroy,
              width=20).pack(pady=10)

    # Admin Panel Button
    def open_admin_login():
        try:
            from admin_panel import admin_login
            admin_login()
        except Exception as e:
            print("Error opening admin panel:", e)

    tk.Button(frame, text="Admin Panel", font=("Arial", 16),
              bg="#2980B9", fg="white", command=open_admin_login,
              width=20).pack(pady=10)

    root.mainloop()


# Start the GUI when executed
if __name__ == "__main__":
    start_voting_gui()
