import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from src.pipeline import run_pipeline


class XMLAIEditor:
    def __init__(self, root):
        self.root = root
        root.title("XML AI Editor - GPT-4o Video Editor")
        root.geometry("500x700")  # Increased height for multicam UI
        
        # Mode selection (NEW)
        tk.Label(root, text="Editing Mode:", font=("Arial", 12, "bold")).pack(pady=(10,5))
        self.mode_var = tk.StringVar(value="single")
        
        mode_frame = tk.Frame(root)
        mode_frame.pack(pady=5)
        
        tk.Radiobutton(mode_frame, text="Single Camera", variable=self.mode_var, 
                      value="single", command=self.update_ui_mode).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(mode_frame, text="Multi Camera", variable=self.mode_var, 
                      value="multicam", command=self.update_ui_mode).pack(side=tk.LEFT, padx=10)
        
        # Container for video input UI (MODIFIED)
        self.video_container = tk.Frame(root)
        self.video_container.pack(pady=10, fill=tk.X, padx=20)
        
        # Single camera UI (existing, but wrapped in frame)
        self.single_ui_frame = tk.Frame(self.video_container)
        self.single_ui_frame.pack(fill=tk.X)
        
        tk.Label(self.single_ui_frame, text="Video Folder:").pack(pady=5)
        self.video_entry = tk.Entry(self.single_ui_frame, width=60)
        self.video_entry.pack(pady=5)
        tk.Button(self.single_ui_frame, text="Browse", command=self.browse_video).pack()
        
        # Multi camera UI (NEW - initially hidden)
        self.multicam_ui_frame = tk.Frame(self.video_container)
        
        tk.Label(self.multicam_ui_frame, text="Camera Angles:", font=("Arial", 10, "bold")).pack(pady=5)
        
        # Scrollable area for camera angles
        self.setup_scrollable_cameras()
        
        # Camera angle management buttons
        button_frame = tk.Frame(self.multicam_ui_frame)
        button_frame.pack(pady=5)
        tk.Button(button_frame, text="Add Camera Angle", command=self.add_camera_angle).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Remove Last", command=self.remove_camera_angle).pack(side=tk.LEFT, padx=5)
        
        # Initialize with one camera angle
        self.camera_angles = []
        self.add_camera_angle()
        
        # Rest of your existing UI (unchanged)
        tk.Label(root, text="Editing Prompt:").pack(pady=(20,5))
        self.prompt_entry = tk.Text(root, height=5, width=60)
        self.prompt_entry.pack(pady=5)
        
        tk.Label(root, text="Output Folder:").pack(pady=(20,5))
        self.output_entry = tk.Entry(root, width=60)
        self.output_entry.pack(pady=5)
        tk.Button(root, text="Browse", command=self.browse_output).pack()
        
        tk.Label(root, text="Target Duration (seconds, optional):").pack(pady=(20,5))
        self.duration_entry = tk.Entry(root, width=20)
        self.duration_entry.pack(pady=5)
        
        self.run_button = tk.Button(root, text="Generate XML", command=self.run_editor, 
                                   bg="blue", fg="white", font=("Arial", 12, "bold"))
        self.run_button.pack(pady=30)

    def setup_scrollable_cameras(self):
        """Setup scrollable area for camera angles (NEW)"""
        # Create scrollable frame
        canvas = tk.Canvas(self.multicam_ui_frame, height=150)
        scrollbar = ttk.Scrollbar(self.multicam_ui_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def update_ui_mode(self):
        """Switch between single and multicam UI (NEW)"""
        if self.mode_var.get() == "single":
            self.multicam_ui_frame.pack_forget()
            self.single_ui_frame.pack(fill=tk.X)
        else:
            self.single_ui_frame.pack_forget()
            self.multicam_ui_frame.pack(fill=tk.X)

    def add_camera_angle(self):
        """Add a new camera angle input (NEW)"""
        angle_num = len(self.camera_angles) + 1
        
        angle_frame = tk.Frame(self.scrollable_frame)
        angle_frame.pack(fill=tk.X, pady=2)
        
        # Angle label and name entry
        tk.Label(angle_frame, text=f"Angle {angle_num}:", width=8).pack(side=tk.LEFT)
        
        name_entry = tk.Entry(angle_frame, width=15)
        name_entry.pack(side=tk.LEFT, padx=5)
        name_entry.insert(0, f"Camera_{angle_num}")
        
        # Folder path entry
        path_entry = tk.Entry(angle_frame, width=35)
        path_entry.pack(side=tk.LEFT, padx=5)
        
        # Browse button
        browse_btn = tk.Button(angle_frame, text="Browse", 
                              command=lambda e=path_entry: self.browse_camera_folder(e))
        browse_btn.pack(side=tk.LEFT)
        
        self.camera_angles.append({
            'frame': angle_frame,
            'name_entry': name_entry,
            'path_entry': path_entry,
            'browse_btn': browse_btn
        })

    def remove_camera_angle(self):
        """Remove the last camera angle (NEW)"""
        if len(self.camera_angles) > 1:
            angle = self.camera_angles.pop()
            angle['frame'].destroy()

    def browse_camera_folder(self, entry_widget):
        """Browse for camera angle folder (NEW)"""
        path = filedialog.askdirectory(title="Select Camera Angle Folder")
        if path:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, path)

    # Existing methods (unchanged)
    def browse_video(self):
        path = filedialog.askdirectory(title="Select Video Folder")
        if path:
            self.video_entry.delete(0, tk.END)
            self.video_entry.insert(0, path)
    
    def browse_output(self):
        path = filedialog.askdirectory(title="Select Output Folder")
        if path:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, path)

    def run_editor(self):
        output_path = self.output_entry.get().strip()
        prompt = self.prompt_entry.get("1.0", tk.END).strip()
        duration_str = self.duration_entry.get().strip()
        
        # Get video paths based on mode (MODIFIED)
        is_multicam = self.mode_var.get() == "multicam"
        
        if is_multicam:
            # Collect multicam data
            video_paths = {}
            for angle in self.camera_angles:
                name = angle['name_entry'].get().strip()
                path = angle['path_entry'].get().strip()
                if name and path:
                    video_paths[name] = path
            
            if not video_paths:
                messagebox.showerror("Error", "Please add at least one camera angle")
                return
        else:
            # Single camera mode
            video_path = self.video_entry.get().strip()
            if not video_path:
                messagebox.showerror("Error", "Please select a video folder")
                return
            video_paths = video_path
        
        # Validate other inputs
        if not output_path or not prompt:
            messagebox.showerror("Error", "Please fill in all required fields")
            return
        
        # Parse duration
        target_duration = None
        if duration_str:
            try:
                target_duration = float(duration_str)
                if target_duration <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Duration must be a positive number")
                return
        
        # Run pipeline (MODIFIED to pass multicam flag)
        try:
            self.run_button.config(state="disabled", text="Processing...")
            self.root.update()
            
            success = run_pipeline(video_paths, prompt, output_path, target_duration, is_multicam=is_multicam)
            
            if success:
                mode_text = "Multicam" if is_multicam else "Single camera"
                messagebox.showinfo("Success", 
                    f"{mode_text} XML project generated successfully!\n\n" +
                    "Files created:\n" +
                    "• project.xml - Import into Premiere Pro\n" +
                    "• project.json - Project data\n" +
                    "• edit_summary.txt - Timeline summary")
            else:
                messagebox.showerror("Failed", 
                    "Processing failed. Check the logs folder for details.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {str(e)}")
        
        finally:
            self.run_button.config(state="normal", text="Generate XML")


def launch_ui():
    root = tk.Tk()
    XMLAIEditor(root)
    root.mainloop()