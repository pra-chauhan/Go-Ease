import os
import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter.ttk import Progressbar, Style, Button, Label, Entry
import threading
from slide_extractor import SlideExtractor
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class SlideExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Slide Extractor")
        self.root.geometry("800x600")
        self.root.configure(bg="#f4f4f9")
        self.style = Style()
        self.style.theme_use('clam')

        self.extractor = None
        self.output_folder = "slides"
        self.create_widgets()

    def create_widgets(self):
        self.center_frame = tk.Frame(self.root, bg="#f4f4f9")
        self.center_frame.pack(expand=True)

        self.url_label = Label(self.center_frame, text="Enter YouTube URL:", font=("Helvetica", 16, "bold"), background="#f4f4f9")
        self.url_label.grid(row=0, column=0, pady=20, padx=20, sticky="w")

        self.url_entry = Entry(self.center_frame, width=50, font=("Helvetica", 16))
        self.url_entry.grid(row=0, column=1, pady=10, padx=20)

        self.interval_label = Label(self.center_frame, text="Frame Interval (Seconds):", font=("Helvetica", 16, "bold"), background="#f4f4f9")
        self.interval_label.grid(row=1, column=0, pady=20, padx=20, sticky="w")

        self.interval_entry = Entry(self.center_frame, width=10, font=("Helvetica", 16))
        self.interval_entry.insert(0, "5")
        self.interval_entry.grid(row=1, column=1, pady=10, padx=20)

        self.threshold_label = Label(self.center_frame, text="Similarity Threshold (0.0 to 1.0):", font=("Helvetica", 16, "bold"), background="#f4f4f9")
        self.threshold_label.grid(row=2, column=0, pady=20, padx=20, sticky="w")

        self.threshold_entry = Entry(self.center_frame, width=10, font=("Helvetica", 16))
        self.threshold_entry.insert(0, "0.9")
        self.threshold_entry.grid(row=2, column=1, pady=10, padx=20)

        self.output_label = Label(self.center_frame, text="Output Directory: slides/", font=("Helvetica", 16), background="#f4f4f9")
        self.output_label.grid(row=3, column=0, pady=20, padx=20, sticky="w")

        self.progress_label = Label(self.center_frame, text="Status: Ready", font=("Helvetica", 16), background="#f4f4f9")
        self.progress_label.grid(row=4, column=0, pady=20, padx=20, sticky="w")

        self.progress_bar = Progressbar(self.center_frame, orient="horizontal", length=500, mode="indeterminate")
        self.progress_bar.grid(row=4, column=1, pady=20, padx=20)

        self.extract_button = Button(self.center_frame, text="Extract Slides", style="Accent.TButton", command=self.extract_slides)
        self.extract_button.grid(row=5, column=0, columnspan=2, pady=30)

        self.pdf_button = Button(self.center_frame, text="Generate PDF", style="Accent.TButton", command=self.generate_pdf)
        self.pdf_button.grid(row=6, column=0, columnspan=2, pady=20)

        self.style.configure("Accent.TButton", font=("Helvetica", 16, "bold"), padding=15, background="#4CAF50", foreground="white")
        self.style.map("Accent.TButton", background=[("active", "#45a049")])

    def extract_slides(self):
        url = self.url_entry.get()
        interval = int(self.interval_entry.get())
        threshold = float(self.threshold_entry.get())

        self.url_entry.config(state="disabled")
        self.interval_entry.config(state="disabled")
        self.threshold_entry.config(state="disabled")
        self.extract_button.config(state="disabled")

        self.progress_label.config(text="Status: Downloading video...")
        self.progress_bar.start()

        threading.Thread(target=self.start_slide_extraction, args=(url, interval, threshold)).start()

    def start_slide_extraction(self, url, interval, threshold):
        try:
            self.extractor = SlideExtractor(video_url=url, interval=interval, similarity_threshold=threshold)

            if self.extractor.extract_slides():
                self.output_folder = self.extractor.get_output_folder()
                self.progress_label.config(text="Status: Extraction Complete!")
            else:
                self.progress_label.config(text="Status: Extraction Failed!")
        except Exception as e:
            self.progress_label.config(text=f"Error: {str(e)}")
        finally:
            if self.extractor:
                self.extractor.cleanup()
            self.progress_bar.stop()
            self.enable_inputs()

    def enable_inputs(self):
        self.url_entry.config(state="normal")
        self.interval_entry.config(state="normal")
        self.threshold_entry.config(state="normal")
        self.extract_button.config(state="normal")

    def generate_pdf(self):
        if not self.extractor:
            messagebox.showerror("Error", "Please extract slides before generating PDF.")
            return

        pdf_filename = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if not pdf_filename:
            return

        try:
            c = canvas.Canvas(pdf_filename, pagesize=letter)
            page_width, page_height = letter

            slide_images = [f for f in os.listdir(self.output_folder) if f.endswith(".png") and f.startswith("slide_")]
            slide_images.sort()

            for slide in slide_images:
                slide_path = os.path.join(self.output_folder, slide)
                img = Image.open(slide_path)
                img_width, img_height = img.size

                max_width = 500
                max_height = 500
                ratio = min(max_width / img_width, max_height / img_height)
                scaled_width = img_width * ratio
                scaled_height = img_height * ratio

                x = (page_width - scaled_width) / 2
                y = (page_height - scaled_height) / 2

                c.drawImage(slide_path, x, y, width=scaled_width, height=scaled_height)
                c.showPage()

            c.save()
            messagebox.showinfo("Success", f"PDF generated successfully at {pdf_filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Error generating PDF: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SlideExtractorApp(root)
    root.mainloop()
