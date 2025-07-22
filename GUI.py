import tkinter as tk
from tkinter import ttk

class DuplicateVideoFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("Duplicate Video Finder")
        self.root.geometry("800x600")
        
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
        
        scan_btn = ttk.Button(
            scan_frame,
            text="Scan",
            command=self._scan_folder
        )
        scan_btn.pack(fill="x")

        # List section (bottom, scrollable)
        list_frame = ttk.LabelFrame(self.run_tab, text="List")
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create scrollable list
        self._create_scrollable_list(list_frame)
    
    def _scan_folder(self):
        """Handle folder scanning when Scan button is clicked"""
        # Placeholder for scan functionality
        print(f"Scanning folder: {self.folder_path.get()}")
        print(f"Ignore readonly: {self.ignore_readonly.get()}")
        print(f"Include subfolders: {self.include_subfolders.get()}")

    def _create_scrollable_list(self, parent):
        # Create main frame
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill="both", expand=True)
        
        # Create scrollbar
        scrollbar = ttk.Scrollbar(main_frame)
        scrollbar.pack(side="right", fill="y")
        
        # Create listbox
        self.listbox = tk.Listbox(
            main_frame,
            yscrollcommand=scrollbar.set,
            selectmode="extended"
        )
        self.listbox.pack(fill="both", expand=True)
        
        # Configure scrollbar
        scrollbar.config(command=self.listbox.yview)

    def _select_folder(self):
        from tkinter import filedialog
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)

if __name__ == "__main__":
    root = tk.Tk()
    app = DuplicateVideoFinder(root)
    root.mainloop()