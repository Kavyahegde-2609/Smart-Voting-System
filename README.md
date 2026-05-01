# 🗳️ Smart Voting System with Biometric Authentication

## 📌 Overview

Smart Voting System is a Python-based academic project designed to simulate a secure digital voting process using biometric authentication and accessibility-focused features.

The system verifies voters using Aadhaar-based identification, supports category-based voting (Normal and Blind voters), performs eye/iris biometric verification for secure authentication, prevents duplicate voting, and provides an admin dashboard for monitoring voting statistics.

This project demonstrates how modern technologies such as computer vision, biometric verification, and GUI-based interaction can be applied to voting workflows.

---

## 🚀 Features

### 👤 Voter Registration
- Aadhaar number verification
- Category-based registration (Normal / Blind voters)
- Eye biometric registration for normal voters
- Prevents invalid registrations

### 👁️ Biometric Authentication
- Real-time eye capture using webcam
- Eye/Iris verification using computer vision
- Secure voter identity validation

### 🗳️ Voting System
- Category-based voting workflow
- Duplicate voting prevention
- Secure vote recording

### 🔊 Accessibility Support
- Voice guidance for user instructions
- Blind voter support

### 📊 Admin Dashboard
- Total registered voters
- Voted vs not voted statistics
- Category-wise voting reports
- List of voters who have voted

---

## 🛠️ Tech Stack

### Programming Language
- Python

### Libraries & Frameworks
- Tkinter (GUI)
- OpenCV (Computer Vision)
- MediaPipe (Eye Detection)
- Pandas (Data Handling)
- pyttsx3 (Text-to-Speech)

### Data Storage
- CSV-based voter database

---

## 📂 Project Structure

```bash
Smart-Voting-System/
│
├── admin_panel.py
├── voter_registration.py
├── voting_system.py
├── voter_db.csv
├── test_import.py
├── assets/
└── README.md
```
---

## ✨ Key Highlights

- Biometric-based voter verification
- Accessibility support for visually impaired users
- Duplicate vote prevention
- Real-time eye capture and matching
- Admin analytics dashboard

---

## ⚠️ Disclaimer

This project is developed for academic learning and demonstration purposes only.

It is **NOT** an official voting platform and must not be used for real elections or public decision-making.

---

## 👩‍💻 Author

Kavya Mahabaleshwara Hegde
