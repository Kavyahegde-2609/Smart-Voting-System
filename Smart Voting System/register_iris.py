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


# ============ Improved Eye-Only Capture ============
def capture_eye_only(aadhaar):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        speak("Webcam not accessible.")
        return None

    speak("Please open your eyes clearly and look straight at the camera.")

    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True, min_detection_confidence=0.7)

    start_time = time.time()
    iris_path = ""
    stable_frames = 0
    required_stable_frames = 5  # Need 5 consecutive stable frames for better accuracy

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mesh_result = face_mesh.process(rgb)

        if mesh_result.multi_face_landmarks:
            for landmarks in mesh_result.multi_face_landmarks:
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

                iris_crop = frame[y1:y2, x1:x2]

                # Calculate eye openness
                eye_open_dist = abs(top.y - bottom.y)

                # Display the eye region in a separate window
                if iris_crop.size != 0:
                    display_eye = cv2.resize(iris_crop, (400, 200))
                    cv2.imshow("Eye Region - Keep Eyes Open", display_eye)

                # Check if eyes are open enough and image quality is good
                if eye_open_dist > 0.03 and iris_crop.size != 0 and iris_crop.shape[0] > 50 and iris_crop.shape[1] > 100:
                    stable_frames += 1
                    
                    # Draw green rectangle on main frame to indicate good capture
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, f"Stable: {stable_frames}/{required_stable_frames}", 
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                    if stable_frames >= required_stable_frames:
                        iris_path = f"iris_{aadhaar}.png"
                        cv2.imwrite(iris_path, iris_crop)
                        
                        cap.release()
                        cv2.destroyAllWindows()
                        speak("Eye captured successfully.")
                        time.sleep(0.3)
                        return iris_path
                else:
                    stable_frames = 0
                    # Draw red rectangle to indicate poor capture
                    if iris_crop.size != 0:
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                        cv2.putText(frame, "Open eyes wider", (10, 30), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # Timeout after 10 seconds
        if time.time() - start_time > 10:
            speak("Capture timeout. Please try again.")
            break

        cv2.imshow("Capturing Eyes - Look at Camera", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return None


# ============ Register User with Validation ============
def register_user():
    global df
    aadhaar = aadhaar_entry.get().strip()
    category = category_var.get()

    if not aadhaar:
        messagebox.showerror("Error", "Please enter Aadhaar number.")
        return

    if not category:
        messagebox.showerror("Error", "Please select a category (Normal or Blind).")
        return

    # Check if Aadhaar exists in CSV
    existing_voter = df[df["aadhaar"].astype(str) == aadhaar]
    
    if existing_voter.empty:
        messagebox.showerror("Error", "Aadhaar number not found in database. Please contact administrator.")
        return

    # Get the registered category from CSV
    registered_category = existing_voter.iloc[0]["category"]
    
    # Validate if selected category matches registered category
    if registered_category != category:
        messagebox.showerror("Wrong Category", 
                           f"Wrong category selected! This Aadhaar is registered as '{registered_category.upper()}' voter.")
        return

    # Check if already registered with iris/face data
    if pd.notna(existing_voter.iloc[0]["iris_path"]) and existing_voter.iloc[0]["iris_path"] not in ["", "blind_placeholder"]:
        messagebox.showinfo("Already Registered", "This Aadhaar is already registered with biometric data.")
        return

    # Process based on category
    if category == "blind":
        save_voter(aadhaar, category, iris_path="blind_placeholder", face_path="blind_placeholder")
        speak("Blind voter registered successfully.")
        messagebox.showinfo("Success", "Blind voter registered successfully!")
    else:
        # Capture eye for normal voters
        iris_path = capture_eye_only(aadhaar)
        if iris_path:
            save_voter(aadhaar, category, iris_path, iris_path)  # Using same path for both
            speak("Normal voter registered with eye biometric.")
            messagebox.showinfo("Success", "Normal voter registered with eye biometric successfully!")
        else:
            messagebox.showerror("Failed", "Could not capture eye image. Please try again.")


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
