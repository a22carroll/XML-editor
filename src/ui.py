import tkinter as tk
from tkinter import filedialog, messagebox
from src.pipeline import run_pipeline


class XMLAIEditor:
    def __init__(self, root):
        self.root = root
        root.title("XML AI Editor - GPT-4o Video Editor")
        root.geometry("500x600")
        
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
        
        # Run button - Store reference to it
        self.run_button = tk.Button(root, text="Generate XML", command=self.run_editor, 
                                   bg="blue", fg="white", font=("Arial", 12, "bold"))
        self.run_button.pack(pady=30)

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
            # Disable button during processing
            self.run_button.config(state="disabled", text="Processing...")
            self.root.update()  # Update the UI to show the change
            
            success = run_pipeline(video_path, prompt, output_path, target_duration)
            
            if success:
                messagebox.showinfo("Success", 
                    "XML project generated successfully!\n\n" +
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
            # Re-enable button after processing
            self.run_button.config(state="normal", text="Generate XML")


def launch_ui():
    root = tk.Tk()
    XMLAIEditor(root)
    root.mainloop()