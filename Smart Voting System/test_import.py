# TEST_IMPORT.PY

try:
    import tkinter
    import cv2
    import hashlib
    import pandas as pd
    import pyttsx3
    import mediapipe as mp
    import time
    from PIL import Image
    import os

    print("All required libraries are successfully imported!")
except Exception as e:
    print("Some libraries are missing or incorrect:")
    print(e)
