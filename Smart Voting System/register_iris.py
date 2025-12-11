import tkinter as tk
from tkinter import messagebox
import pandas as pd
import pyttsx3
import cv2
import mediapipe as mp
import os
import time

# ============ Text-to-Speech ============
engine = pyttsx3.init()

def speak(text):
    print("[Voice]:", text)
    engine.say(text)
    engine.runAndWait()


# ============ Load/Create Voter Database ============
csv_path = "voter_db.csv"
if not os.path.exists(csv_path):
    df = pd.DataFrame(columns=["aadhaar", "category", "iris_path", "face_path", "voted"])
    df.to_csv(csv_path, index=False)
else:
    df = pd.read_csv(csv_path)


# ============ Save or Update Voter Entry ============
def save_voter(aadhaar, category, iris_path="", face_path=""):
    global df
    aadhaar = str(aadhaar).strip()
    existing = df[df["aadhaar"].astype(str) == aadhaar]

    if not existing.empty:
        df.loc[df["aadhaar"].astype(str) == aadhaar, "category"] = category
        df.loc[df["aadhaar"].astype(str) == aadhaar, "iris_path"] = iris_path
        df.loc[df["aadhaar"].astype(str) == aadhaar, "face_path"] = face_path
    else:
        df.loc[len(df)] = [aadhaar, category, iris_path, face_path, "no"]

    df.to_csv(csv_path, index=False)


# ============ Combined Face + Iris Capture (Zoomed Face Only) ============
def capture_face_and_iris(aadhaar):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        speak("Webcam not accessible.")
        return None, None

    speak("Please look straight. Capturing face and iris.")

    mp_face_mesh = mp.solutions.face_mesh
    mp_face_detection = mp.solutions.face_detection

    face_detection = mp_face_detection.FaceDetection(min_detection_confidence=0.7)
    face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)

    start_time = time.time()
    iris_path = ""
    face_path = ""

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        detection_result = face_detection.process(rgb)
        mesh_result = face_mesh.process(rgb)

        if detection_result.detections and mesh_result.multi_face_landmarks:
            h, w = frame.shape[:2]
            bboxC = detection_result.detections[0].location_data.relative_bounding_box

            x = int(bboxC.xmin * w)
            y = int(bboxC.ymin * h)
            w_box = int(bboxC.width * w)
            h_box = int(bboxC.height * h)

            face_crop = frame[y:y + h_box, x:x + w_box]

            for landmarks in mesh_result.multi_face_landmarks:
                left = landmarks.landmark[33]
                right = landmarks.landmark[263]
                top = landmarks.landmark[159]
                bottom = landmarks.landmark[145]

                x1 = int(min(left.x, right.x) * w) - 40
                x2 = int(max(left.x, right.x) * w) + 40
                y1 = int(top.y * h) - 50
                y2 = int(bottom.y * h) + 50

                iris_crop = frame[max(0, y1):min(h, y2), max(0, x1):min(w, x2)]

                eye_open_dist = abs(top.y - bottom.y)

                if eye_open_dist > 0.03 and iris_crop.size != 0:
                    face_path = f"face_{aadhaar}.png"
                    iris_path = f"iris_{aadhaar}.png"

                    cv2.imwrite(face_path, face_crop)
                    cv2.imwrite(iris_path, iris_crop)

                    cap.release()
                    cv2.destroyAllWindows()
                    speak("Face and iris captured.")
                    time.sleep(0.5)
                    return face_path, iris_path

        if time.time() - start_time > 6:
            break

        cv2.imshow("Capturing Face & Iris - Look Straight", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return None, None


# ============ Register User ============
def register_user():
    aadhaar = aadhaar_entry.get().strip()
    category = category_var.get()

    if not aadhaar or not category:
        messagebox.showerror("Error", "Please enter Aadhaar and select category.")
        return

    if df[df["aadhaar"].astype(str) == aadhaar].shape[0] > 0 and \
       pd.notna(df[df["aadhaar"].astype(str) == aadhaar].iloc[0]["iris_path"]):
        messagebox.showinfo("Already Registered", "This Aadhaar is already registered.")
        return

    if category == "blind":
        save_voter(aadhaar, category, iris_path="blind_placeholder", face_path="blind_placeholder")
        speak("Blind voter registered successfully.")
        messagebox.showinfo("Success", "Blind voter registered successfully!")
    else:
        face_path, iris_path = capture_face_and_iris(aadhaar)
        if face_path and iris_path:
            save_voter(aadhaar, category, iris_path, face_path)
            speak("Normal voter registered with face and iris.")
            messagebox.showinfo("Success", "Normal voter registered with face and iris!")
        else:
            messagebox.showerror("Failed", "Could not capture face and iris. Try again.")


# ============ GUI Setup ============
root = tk.Tk()
root.title("Smart Voting - Voter Registration")
root.attributes("-fullscreen", True)
root.configure(bg="#E8F8F5")

# Header
tk.Label(root, text="Smart Voting System", font=("Helvetica", 40, "bold"),
         bg="#E8F8F5", fg="#154360").pack(pady=30)

tk.Label(root, text="Voter Registration Interface", font=("Helvetica", 28),
         bg="#E8F8F5", fg="#1A5276").pack(pady=10)

# Form Frame
form = tk.Frame(root, bg="#E8F8F5")
form.pack(pady=40)

# Aadhaar Entry
tk.Label(form, text="Enter Aadhaar Number:", font=("Helvetica", 22),
         bg="#E8F8F5", fg="#154360").grid(row=0, column=0, padx=20, pady=15, sticky="e")

aadhaar_entry = tk.Entry(form, font=("Helvetica", 22), width=30, bd=3, relief="solid")
aadhaar_entry.grid(row=0, column=1, pady=15)

# Category Radio
tk.Label(form, text="Select Category:", font=("Helvetica", 22),
         bg="#E8F8F5", fg="#154360").grid(row=1, column=0, padx=20, pady=15, sticky="e")

category_var = tk.StringVar()
radio_frame = tk.Frame(form, bg="#E8F8F5")
radio_frame.grid(row=1, column=1, pady=15)

tk.Radiobutton(radio_frame, text="Normal", variable=category_var, value="normal",
               font=("Helvetica", 20), bg="#E8F8F5").pack(side=tk.LEFT, padx=20)

tk.Radiobutton(radio_frame, text="Blind", variable=category_var, value="blind",
               font=("Helvetica", 20), bg="#E8F8F5").pack(side=tk.LEFT, padx=20)

# Buttons
tk.Button(root, text="Start Registration", font=("Helvetica", 20, "bold"),
          bg="#28B463", fg="white", width=20, height=2,
          command=register_user).pack(pady=40)

tk.Button(root, text="Exit", font=("Helvetica", 16),
          bg="#CB4335", fg="white", width=15,
          command=root.destroy).pack()

root.mainloop()
