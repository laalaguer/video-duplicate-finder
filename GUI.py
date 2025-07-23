import threading
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from PIL import Image, ImageTk, ImageDraw
from pathlib import Path
from typing import List
# Scan folder using files.py scan() function
from utils.files import scan
from utils.ffprobe import get_video_info
from utils.helpers import size_to_str, seconds_to_str

WINDOW_WIDTH = 900
WINDOW_HEIGHT = 800
PATH_FRAME_WIDTH = 250
MAX_PATH_WIDTH = 240
THUMBNAIL_WIDTH = 100  # Width in pixels for thumbnails

class VideoObject:
    """Represents a video file with metadata and screenshots"""
    
    def __init__(
        self,
        file_path: Path,
        screenshots: List[Path] = None,
        width: int = 0,
        height: int = 0,
        duration: int = 0,
        size: int = 0,
        fps: int = 0,
        codec: str = ""
    ):
        self.file_path = file_path
        self.screenshots = screenshots or []
        self.width = width
        self.height = height
        self.duration = duration
        self.size = size
        self.fps = fps
        self.codec = codec


def _nil_image(max_width: int):
    placeholder = Image.new('RGB', (max_width or THUMBNAIL_WIDTH, 100), color='gray')
    draw = ImageDraw.Draw(placeholder)
    draw.text((10, 40), "No Image", fill='white')
    return ImageTk.PhotoImage(placeholder)


class DuplicateVideoFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("Duplicate Video Finder")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill="both")
        
        # Create Run tab
        self.run_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.run_tab, text="Run")
        
        # Create Log tab
        self.log_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.log_tab, text="Log")
        
        # Build Run tab sections
        self._build_run_tab()
    
    def _build_run_tab(self):
        # Control section (top)
        control_frame = ttk.LabelFrame(self.run_tab, text="Control")
        control_frame.pack(fill="x", padx=5, pady=5)
        
        # Folder selection widgets
        folder_frame = ttk.Frame(control_frame)
        folder_frame.pack(fill="x", padx=5, pady=5)
        
        # Checkbox options
        options_frame = ttk.Frame(control_frame)
        options_frame.pack(fill="x", padx=5, pady=(0,5))
        
        self.folder_path = tk.StringVar()
        folder_entry = ttk.Entry(
            folder_frame,
            textvariable=self.folder_path,
            state="readonly"
        )
        folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        browse_btn = ttk.Button(
            folder_frame,
            text="Browse",
            command=self._select_folder
        )
        browse_btn.pack(side="right")

        # Checkbox options
        self.ignore_readonly = tk.IntVar(value=1)
        ignore_readonly_cb = ttk.Checkbutton(
            options_frame,
            text="Ignore read only folders",
            variable=self.ignore_readonly
        )
        ignore_readonly_cb.pack(side="left", padx=(0,10))

        self.include_subfolders = tk.IntVar(value=1)
        include_subfolders_cb = ttk.Checkbutton(
            options_frame,
            text="Include Sub folders",
            variable=self.include_subfolders
        )
        include_subfolders_cb.pack(side="left")

        # Scan button frame (full width)
        scan_frame = ttk.Frame(control_frame)
        scan_frame.pack(fill="x", padx=5, pady=(0,5))
        
        self.scan_btn = ttk.Button(
            scan_frame,
            text="Scan",
            command=self._scan_folder,
            width=15
        )
        self.scan_btn.pack(pady=5)

        # List section (bottom, scrollable)
        list_frame = ttk.LabelFrame(self.run_tab, text="List")
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create scrollable list
        self._create_scrollable_list(list_frame)
    
    def _scan_folder(self):
        """Handle folder scanning when Scan button is clicked"""
        folder_path = self.folder_path.get()
        if not folder_path or not Path(folder_path).exists():
            print("Error: Folder path does not exist")
            return
            
        # Disable scan button and clear list
        self.scan_btn['state'] = 'disabled'
        self.scan_btn['text'] = "Scanning..."
        self._delete_item()
        self.root.update()  # Force GUI update
        
        # Start scan in background thread
        scan_thread = threading.Thread(
            target=self._run_scan,
            args=(folder_path,),
            daemon=True
        )
        scan_thread.start()
    
    def _run_scan(self, folder_path):
        """Wrapper function to run scan in background thread"""
        try:
            video_files = scan(
                folder_path=folder_path,
                ignore_readonly_folder=bool(self.ignore_readonly.get()),
                recursive=bool(self.include_subfolders.get())
            )
            
            # Create temporary VideoObject list
            _temp = []
            for video_path in video_files:
                try:
                    width, height, duration, size, fps, codec = get_video_info(str(video_path))
                    video_obj = VideoObject(
                        file_path=video_path,
                        width=width,
                        height=height,
                        duration=duration,
                        size=size,
                        fps=int(fps),
                        codec=codec
                    )
                    _temp.append(video_obj)
                except Exception as e:
                    print(f"Error processing {video_path}: {e}")
                    continue
            
            # Update GUI in main thread
            self.root.after(0, self._update_gui_with_results, _temp)
            
        finally:
            # Re-enable button in main thread
            self.root.after(0, lambda: [
                self.scan_btn.config(state='normal', text='Scan'),
                self.root.update()
            ])
    
    def _update_gui_with_results(self, video_objects):
        """Update GUI with scan results (called from main thread)"""
        for video_obj in video_objects:
            self.add_video_item(
                video_path=str(video_obj.file_path),
                thumbnails=[None, None, None],
                resolution=f"{video_obj.width}x{video_obj.height}",
                duration=seconds_to_str(video_obj.duration),
                size=size_to_str(video_obj.size),
                fps=video_obj.fps,
                codec=video_obj.codec
            )

    def _create_scrollable_list(self, parent):
        # Create main frame with scrollbar
        style = ttk.Style()
        style.configure('NoBorder.TFrame', borderwidth=0)
        container = ttk.Frame(parent, style='NoBorder.TFrame')
        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        container.pack(fill="both", expand=True)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind click event to focus canvas for scrolling
        def _on_click(event):
            canvas.focus_set()
        
        canvas.bind("<Button-1>", _on_click)

        # This will hold our video items
        self.video_items = []

    def add_video_item(self, video_path, thumbnails, resolution, duration, size, fps=0, codec=""):
        """Add a new video item to the list"""
        item_frame = ttk.Frame(self.scrollable_frame, padding=5)
        item_frame.pack(fill="x", pady=2)
        
        # Focus canvas when clicking anywhere on video item
        def _focus_canvas(event):
            canvas = self.scrollable_frame.master.master  # Get canvas reference
            canvas.focus_set()
            
        item_frame.bind("<Button-1>", _focus_canvas)
        
        # 1. Delete button
        delete_btn = ttk.Button(
            item_frame,
            text="🗑",
            width=2,
            command=lambda: self._delete_item(item_frame)
        )
        delete_btn.pack(side="left", padx=(0, 5))

        # 2. Video path (wrapped)
        path_frame = ttk.Frame(item_frame, width=PATH_FRAME_WIDTH)
        path_frame.pack_propagate(False)
        path_frame.pack(side="left", fill="y")
        
        path_label = ttk.Label(
            path_frame,
            text=video_path,
            wraplength=MAX_PATH_WIDTH,
            anchor="w"
        )
        path_label.pack(fill="both", expand=True)

        # 3. Thumbnails
        thumbs_frame = ttk.Frame(item_frame)
        thumbs_frame.pack(side="left", padx=5)
        
        for thumb in thumbnails:
            if thumb is None:
                _thumb = _nil_image(THUMBNAIL_WIDTH)
                img_label = ttk.Label(
                    thumbs_frame,
                    image=_thumb,
                    width=THUMBNAIL_WIDTH,
                    relief="solid",
                    borderwidth=1,
                    compound="center"
                )
                img_label.image = _thumb  # Keep reference
            else:
                _thumb = thumb
                img_label = ttk.Label(
                    thumbs_frame,
                    image=_thumb,
                    width=THUMBNAIL_WIDTH,
                    relief="solid",
                    borderwidth=1
                )
                img_label.image = _thumb  # Keep reference
            
            img_label = ttk.Label(
                thumbs_frame,
                image=_thumb,
                width=50,
                relief="solid",
                borderwidth=1
            )
            img_label.pack(side="left", padx=2)

        # 4. Details section
        details_frame = ttk.Frame(item_frame)
        details_frame.pack(side="left", fill="y")
        
        resolution_label = ttk.Label(
            details_frame,
            text=f"Resolution: {resolution}",
            anchor="w"
        )
        resolution_label.pack(fill="x")
        
        duration_label = ttk.Label(
            details_frame,
            text=f"Duration: {duration}",
            anchor="w"
        )
        duration_label.pack(fill="x")
        
        size_label = ttk.Label(
            details_frame,
            text=f"Size: {size}",
            anchor="w"
        )
        size_label.pack(fill="x")

        fps_label = ttk.Label(
            details_frame,
            text=f"FPS: {int(fps)}",
            anchor="w"
        )
        fps_label.pack(fill="x")

        codec_label = ttk.Label(
            details_frame,
            text=f"Codec: {codec}",
            anchor="w"
        )
        codec_label.pack(fill="x")

        self.video_items.append(item_frame)

    def _delete_item(self, item_frame=None):
        """Remove a video item from the list or clear all items if None"""
        if item_frame is None:
            # Clear all items
            for item in self.video_items[:]:
                item.destroy()
            self.video_items.clear()
        else:
            # Remove specific item
            item_frame.destroy()
            if item_frame in self.video_items:
                self.video_items.remove(item_frame)

    def _select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)

if __name__ == "__main__":
    root = tk.Tk()
    app = DuplicateVideoFinder(root)
    root.mainloop()