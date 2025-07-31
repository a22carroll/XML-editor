import tkinter as tk
from tkinter import filedialog, messagebox
from src.pipeline import run_pipeline


class ResolveAIEditor:
    def __init__(self, root):
        self.root = root
        root.title("AI Video Editor for DaVinci Resolve")
        root.geometry("500x400")
        
        # Video folder
        tk.Label(root, text="Video Folder:").pack(pady=5)
        self.video_entry = tk.Entry(root, width=60)
        self.video_entry.pack(pady=5)
        tk.Button(root, text="Browse", command=self.browse_video).pack()
        
        # Prompt
        tk.Label(root, text="Editing Prompt:").pack(pady=(20,5))
        self.prompt_entry = tk.Text(root, height=5, width=60)
        self.prompt_entry.pack(pady=5)
        
        # Output folder
        tk.Label(root, text="Output Folder:").pack(pady=(20,5))
        self.output_entry = tk.Entry(root, width=60)
        self.output_entry.pack(pady=5)
        tk.Button(root, text="Browse", command=self.browse_output).pack()
        
        # Duration (optional)
        tk.Label(root, text="Target Duration (seconds, optional):").pack(pady=(20,5))
        self.duration_entry = tk.Entry(root, width=20)
        self.duration_entry.pack(pady=5)
        
        # Run button
        tk.Button(root, text="🎬 Generate Video", command=self.run_editor, 
                 bg="green", fg="white", font=("Arial", 12, "bold")).pack(pady=30)

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
        video_path = self.video_entry.get().strip()
        output_path = self.output_entry.get().strip()
        prompt = self.prompt_entry.get("1.0", tk.END).strip()
        duration_str = self.duration_entry.get().strip()
        
        # Validate inputs
        if not video_path or not output_path or not prompt:
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
        
        # Run pipeline
        try:
            success = run_pipeline(video_path, prompt, output_path, target_duration)
            
            if success:
                messagebox.showinfo("Success", "🎉 Video processing complete!")
            else:
                messagebox.showerror("Failed", "❌ Processing failed - check logs")
                
        except Exception as e:
            messagebox.showerror("Error", f"❌ {str(e)}")


def launch_ui():
    root = tk.Tk()
    ResolveAIEditor(root)
    root.mainloop()