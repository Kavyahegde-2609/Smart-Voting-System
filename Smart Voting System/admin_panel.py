# admin_panel.py

import pandas as pd
import os
from tkinter import *
from tkinter import messagebox

CSV_PATH = "voter_db.csv"
ADMIN_PASSWORD = "admin123"   # Change this to your secure password


# ---------------------- Load Voter Data ----------------------
def load_voter_data():
    if not os.path.exists(CSV_PATH):
        messagebox.showerror("Error", "voter_db.csv not found!")
        return None
    return pd.read_csv(CSV_PATH)


# ---------------------- Open Admin Panel ----------------------
def open_admin_panel():
    df = load_voter_data()
    if df is None:
        return

    total = len(df)
    voted = len(df[df["voted"] == "yes"])
    not_voted = len(df[df["voted"] == "no"])

    normal_voted = len(df[(df["voted"] == "yes") & (df["category"] == "normal")])
    blind_voted = len(df[(df["voted"] == "yes") & (df["category"] == "blind")])

    voted_list = df[df["voted"] == "yes"]["aadhaar"].tolist()

    panel = Tk()
    panel.title("Admin Voting Panel")
    panel.geometry("700x600")
    panel.configure(bg="#FDEDEC")

    Label(panel, text=" Admin Voting Dashboard",
          font=("Arial", 24, "bold"),
          bg="#FDEDEC", fg="#154360").pack(pady=20)

    Label(panel, text=f" Total Registered Voters: {total}",
          font=("Arial", 18), bg="#FDEDEC").pack(pady=10)

    Label(panel, text=f" Voted: {voted}",
          font=("Arial", 18), bg="#FDEDEC").pack()

    Label(panel, text=f" Not Voted: {not_voted}",
          font=("Arial", 18), bg="#FDEDEC").pack()

    Label(panel, text=f" Normal Voters Voted: {normal_voted}",
          font=("Arial", 18), bg="#FDEDEC").pack(pady=10)

    Label(panel, text=f" Blind Voters Voted: {blind_voted}",
          font=("Arial", 18), bg="#FDEDEC").pack(pady=10)

    Label(panel, text=" Aadhaar Numbers of Voted Users:",
          font=("Arial", 16, "bold"),
          bg="#FDEDEC", fg="#1A5276").pack(pady=10)

    listbox = Listbox(panel, width=40, height=10, font=("Arial", 14))
    listbox.pack(pady=10)

    for aadhaar in voted_list:
        listbox.insert(END, aadhaar)

    Button(panel, text="Close", font=("Arial", 14),
           bg="red", fg="white",
           command=panel.destroy).pack(pady=20)

    panel.mainloop()


# ---------------------- Admin Login ----------------------
def admin_login():
    login = Tk()
    login.title("Admin Login")
    login.geometry("400x250")
    login.configure(bg="#EBF5FB")

    Label(login, text="Enter Admin Password",
          font=("Arial", 18), bg="#EBF5FB").pack(pady=20)

    password_entry = Entry(login, font=("Arial", 16),
                           show="*", width=25)
    password_entry.pack(pady=10)

    def check_password():
        if password_entry.get() == ADMIN_PASSWORD:
            login.destroy()
            open_admin_panel()
        else:
            messagebox.showerror("Access Denied", "Incorrect Password!")

    Button(login, text="Login", font=("Arial", 14),
           bg="#3498DB", fg="white",
           command=check_password).pack(pady=15)

    Button(login, text="Exit", font=("Arial", 14),
           bg="gray", fg="white",
           command=login.destroy).pack()

    login.mainloop()


# ---------------------- Main ----------------------
if __name__ == "__main__":
    admin_login()
