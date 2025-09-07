import os
import json
import uuid
from datetime import datetime
import logging
import cv2
import numpy as np
import face_recognition
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import threading

# Configure logging
logging.basicConfig(filename='face_auth.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Directories for saving data
REGISTRATION_DIR = './Registration'
AUTHENTICATION_DIR = './Authentication'
AUTH_LOG_DIR = './Auth_Logs'

ROLES = ['doctor', 'patient', 'receptionist', 'pharmacist']

# Create directories
for role in ROLES:
    os.makedirs(os.path.join(REGISTRATION_DIR, role), exist_ok=True)
    os.makedirs(os.path.join(AUTHENTICATION_DIR, role), exist_ok=True)
os.makedirs(AUTH_LOG_DIR, exist_ok=True)


class FaceAuthApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Face Authentication System")
        self.root.geometry("600x400")
        self.root.configure(bg="#f0f0f0")

        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TButton', font=('Helvetica', 12, 'bold'), padding=10, background='#4CAF50',
                             foreground='white')
        self.style.configure('TLabel', font=('Helvetica', 12), background="#f0f0f0")
        self.style.configure('TEntry', font=('Helvetica', 12))
        self.style.configure('TCombobox', font=('Helvetica', 12))

        # Main frame
        self.main_frame = ttk.Frame(root, padding=20)
        self.main_frame.pack(expand=True, fill='both')

        # Title
        ttk.Label(self.main_frame, text="Face Authentication System", font=('Helvetica', 18, 'bold')).pack(pady=20)

        # Buttons
        ttk.Button(self.main_frame, text="Register Face", command=self.open_register_window).pack(pady=10, fill='x')
        ttk.Button(self.main_frame, text="Authenticate Face", command=self.open_auth_window).pack(pady=10, fill='x')
        ttk.Button(self.main_frame, text="Exit", command=self.root.quit).pack(pady=10, fill='x')

        # Webcam variables
        self.cap = None
        self.photo = None
        self.captured_image = None

    def open_register_window(self):
        self._open_window("Register Face", self._register_face)

    def open_auth_window(self):
        self._open_window("Authenticate Face", self._authenticate_face)

    def _open_window(self, title, action_func):
        window = tk.Toplevel(self.root)
        window.title(title)
        window.geometry("500x600")
        window.configure(bg="#f0f0f0")

        frame = ttk.Frame(window, padding=20)
        frame.pack(expand=True, fill='both')

        ttk.Label(frame, text=title, font=('Helvetica', 16, 'bold')).pack(pady=10)

        ttk.Label(frame, text="Username:").pack(anchor='w')
        username_entry = ttk.Entry(frame)
        username_entry.pack(fill='x', pady=5)

        ttk.Label(frame, text="Role:").pack(anchor='w')
        role_combo = ttk.Combobox(frame, values=ROLES, state='readonly')
        role_combo.pack(fill='x', pady=5)
        role_combo.set(ROLES[0])

        # Video feed label
        video_label = ttk.Label(frame)
        video_label.pack(pady=10, fill='both', expand=True)

        # Buttons
        ttk.Button(frame, text="Capture Face", command=lambda: self._capture_face(video_label)).pack(pady=5, fill='x')
        ttk.Button(frame, text="Submit",
                   command=lambda: self._submit(action_func, window, username_entry.get(), role_combo.get())).pack(
            pady=5, fill='x')

        # Start webcam
        self._start_webcam(video_label, window)

    def _start_webcam(self, label, window):
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                self._show_error(window, "Could not open webcam.")
                return

            def update_frame():
                if self.cap is None or not self.cap.isOpened():
                    return
                ret, frame = self.cap.read()
                if ret:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame).resize((320, 240))
                    self.photo = ImageTk.PhotoImage(image=img)
                    label.config(image=self.photo)
                    label.image = self.photo
                label.after(10, update_frame)

            update_frame()
        except Exception as e:
            logging.error(f"Error starting webcam: {e}")
            self._show_error(window, f"Error starting webcam: {str(e)}")

    def _capture_face(self, label):
        try:
            if self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    self.captured_image = frame
                    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).resize((320, 240))
                    self.photo = ImageTk.PhotoImage(image=img)
                    label.config(image=self.photo)
                    label.image = self.photo
                    self._show_info(label, "Face captured successfully!")
                else:
                    self._show_error(label, "Failed to capture image.")
            else:
                self._show_error(label, "Webcam not available.")
        except Exception as e:
            logging.error(f"Error capturing face: {e}")
            self._show_error(label, f"Error capturing face: {str(e)}")

    def _submit(self, action_func, window, username, role):
        if not username or not role:
            self._show_error(window, "Username and role are required.")
            return
        if self.captured_image is None:
            self._show_error(window, "Please capture a face image first.")
            return

        threading.Thread(target=action_func, args=(username, role, self.captured_image, window), daemon=True).start()

    def _register_face(self, username, role, image, window):
        timestamp_str = datetime.utcnow().isoformat() + 'Z'
        try:
            # Convert image for face_recognition
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_image)
            if not face_locations:
                self._show_error(window, "No face detected in the image.")
                return

            user_dir = os.path.join(REGISTRATION_DIR, role, username)
            if os.path.exists(user_dir):
                self._show_error(window, f'Username "{username}" already registered for role "{role}".')
                return

            os.makedirs(user_dir, exist_ok=True)
            filename = f"registered_face_{uuid.uuid4().hex}.png"
            save_path = os.path.join(user_dir, filename)
            cv2.imwrite(save_path, image)

            # Save face encoding
            encodings = face_recognition.face_encodings(rgb_image, face_locations)
            if encodings:
                encoding_path = os.path.join(user_dir, 'face_encoding.npy')
                np.save(encoding_path, encodings[0])

            user_info = {
                'username': username,
                'role': role,
                'registration_time': timestamp_str
            }
            user_info_path = os.path.join(user_dir, 'user_info.json')
            with open(user_info_path, 'w') as f:
                json.dump(user_info, f, indent=4)

            logging.info(f"Face registered for {username} ({role}) at {save_path}")
            self._show_info(window, f'Face registered successfully for {username} as {role}.')
            window.destroy()
        except Exception as e:
            logging.error(f"Error during face registration: {e}")
            self._show_error(window, f'Error during face registration: {str(e)}')

    def _authenticate_face(self, username, role, captured_image, window):
        timestamp_str = datetime.utcnow().isoformat() + 'Z'
        try:
            # Convert image for face_recognition
            rgb_image = cv2.cvtColor(captured_image, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_image)
            if not face_locations:
                self._show_error(window, "No face detected in the captured image.")
                return

            user_dir = os.path.join(REGISTRATION_DIR, role, username)
            user_info_path = os.path.join(user_dir, 'user_info.json')

            if not os.path.exists(user_info_path):
                self._show_error(window, f'Username "{username}" not found for role "{role}".')
                return

            with open(user_info_path, 'r') as f:
                user_info = json.load(f)
            if user_info.get('role') != role or user_info.get('username') != username:
                self._show_error(window, 'Username and role do not match registered data.')
                return

            encoding_path = os.path.join(user_dir, 'face_encoding.npy')
            if not os.path.exists(encoding_path):
                self._show_error(window, 'No registered face encoding found for this user.')
                return

            # Load registered encoding
            registered_encoding = np.load(encoding_path)

            # Get encoding for captured image
            captured_encodings = face_recognition.face_encodings(rgb_image, face_locations)
            if not captured_encodings:
                self._show_error(window, "No face encoding could be generated from the captured image.")
                return

            # Compare faces
            distance = face_recognition.face_distance([registered_encoding], captured_encodings[0])[0]
            verification_threshold = 0.6  # Default threshold for face_recognition

            if distance < verification_threshold:
                self._log_auth_success(username, role, timestamp_str, distance)
                self._save_auth_image(username, role, captured_image, success=True)
                self._update_last_login(user_info_path, timestamp_str)
                self._show_info(window,
                                f'Authentication successful for {username} as {role}.\nConfidence: {1 - distance:.2f}')
                window.destroy()
            else:
                self._log_auth_failure(username, role, timestamp_str, distance)
                self._save_auth_image(username, role, captured_image, success=False)
                self._show_error(window, f'Authentication failed. Face does not match.\nDistance: {distance:.2f}')
        except Exception as e:
            logging.error(f"Error during face authentication: {e}")
            self._show_error(window, f'Error during face authentication: {str(e)}')

    def _log_auth_success(self, username, role, timestamp, distance):
        log_entry = {
            'timestamp': timestamp,
            'username': username,
            'role': role,
            'status': 'success',
            'distance': float(distance)
        }
        self._write_log(log_entry)

    def _log_auth_failure(self, username, role, timestamp, distance):
        log_entry = {
            'timestamp': timestamp,
            'username': username,
            'role': role,
            'status': 'failed',
            'distance': float(distance),
            'error': 'No sufficient face match'
        }
        self._write_log(log_entry)

    def _write_log(self, log_entry):
        auth_log_path = os.path.join(AUTH_LOG_DIR, f"auth_log_{datetime.now().strftime('%Y%m%d')}.jsonl")
        try:
            with open(auth_log_path, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logging.error(f"Error writing to log file: {e}")

    def _save_auth_image(self, username, role, image, success):
        try:
            auth_dir = os.path.join(AUTHENTICATION_DIR, role, username)
            os.makedirs(auth_dir, exist_ok=True)
            status = 'success' if success else 'failed'
            auth_filename = f"auth_{status}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}.png"
            auth_save_path = os.path.join(auth_dir, auth_filename)
            cv2.imwrite(auth_save_path, image)
        except Exception as e:
            logging.error(f"Error saving authentication image: {e}")

    def _update_last_login(self, user_info_path, timestamp):
        try:
            with open(user_info_path, 'r+') as f:
                user_info = json.load(f)
                user_info['last_login_time'] = timestamp
                f.seek(0)
                json.dump(user_info, f, indent=4)
                f.truncate()
        except Exception as e:
            logging.error(f"Error updating last_login_time: {e}")

    def _show_info(self, window, message):
        self.root.after(0, lambda: messagebox.showinfo("Success", message, parent=window))

    def _show_error(self, window, message):
        self.root.after(0, lambda: messagebox.showerror("Error", message, parent=window))

    def __del__(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()


if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = FaceAuthApp(root)
        root.mainloop()
    except Exception as e:
        logging.error(f"Application error: {e}")
        messagebox.showerror("Error", f"Application failed to start: {str(e)}")