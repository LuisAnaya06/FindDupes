"""
================================================================================
FindDupes - Duplicate File Analyzer
================================================================================

AI-GENERATED CODE NOTICE:
This application was developed with assistance from GitHub Copilot and Claude AI.
The core architecture, algorithms, and UI implementation were generated through
AI-assisted development and refined through iterative improvements.

Author: Luis Anaya
Repository: https://github.com/[username]/FindDupes
License: [Your chosen license]
Last Updated: January 2026

================================================================================

File Comparer - Duplicate File Analyzer with AI-powered matching
Main GUI Application using CustomTkinter

Features:
- Exact duplicate detection using SHA-256 hashing with multiprocessing
- Fuzzy similarity matching using RapidFuzz algorithms
- Paginated results display for handling large datasets
- Video thumbnail generation with OpenCV
- Customizable filename normalization patterns
- Safe file deletion to system trash
- Save/load analysis results to JSON

"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
from pathlib import Path
import os
from datetime import datetime
from send2trash import send2trash
from file_analyzer import FileAnalyzer
from PIL import Image
import subprocess
import platform


class FileComparerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title("File Comparer - Video Duplicate Analyzer")
        self.geometry("1200x800")
        
        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Initialize analyzer
        self.analyzer = FileAnalyzer(similarity_threshold=80)
        self.folders = []
        self.exact_duplicates = []
        self.similar_files = []
        self.selected_for_deletion = set()
        self.stop_requested = False
        self.sort_by = "size"  # Default sort by size
        self.generate_thumbnails = True  # Default to enabled
        self.current_scanning_folder = None  # Track currently scanning folder
        self.thumbnail_widgets = {}  # Map file paths to thumbnail label widgets
        self.thumbnail_images = {}  # Persistent cache of CTkImage objects to prevent GC
        
        # Pagination state
        self.current_page = 0
        self.groups_per_page = 50
        self.current_result_type = None
        self.current_sorted_groups = []
        
        # Create UI
        self.create_ui()
        
    def create_ui(self):
        """Create the main user interface"""
        # Main container with padding
        main_container = ctk.CTkFrame(self)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Top section: Folder selection
        self.create_folder_section(main_container)
        
        # Middle section: Analysis controls
        self.create_controls_section(main_container)
        
        # Bottom section: Results display
        self.create_results_section(main_container)
        
    def create_folder_section(self, parent):
        """Create folder selection section"""
        folder_frame = ctk.CTkFrame(parent)
        folder_frame.pack(fill="x", padx=5, pady=5)
        
        # Title
        ctk.CTkLabel(folder_frame, text="Folders to Analyze:", 
                    font=("Arial", 16, "bold")).pack(anchor="w", padx=10, pady=5)
        
        # Folder list and buttons
        list_frame = ctk.CTkFrame(folder_frame)
        list_frame.pack(fill="x", padx=10, pady=5)
        
        # Folder listbox - scrollable frame for individual folder rows
        self.folder_scroll = ctk.CTkScrollableFrame(list_frame, height=100)
        self.folder_scroll.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Buttons
        btn_frame = ctk.CTkFrame(list_frame)
        btn_frame.pack(side="right", fill="y")
        
        ctk.CTkButton(btn_frame, text="Add Folder", command=self.add_folder,
                     width=120).pack(pady=2)
        ctk.CTkButton(btn_frame, text="Clear All", command=self.clear_folders,
                     width=120).pack(pady=2)
        
    def create_controls_section(self, parent):
        """Create analysis controls section"""
        control_frame = ctk.CTkFrame(parent)
        control_frame.pack(fill="x", padx=5, pady=5)
        
        # Left side: Analysis buttons
        left_frame = ctk.CTkFrame(control_frame)
        left_frame.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        
        ctk.CTkButton(left_frame, text="🔍 Find Exact Duplicates", 
                     command=self.find_exact_duplicates,
                     font=("Arial", 14, "bold"), height=40).pack(side="left", padx=5)
        
        ctk.CTkButton(left_frame, text="🤖 Find Similar Files", 
                     command=self.find_similar_files,
                     font=("Arial", 14, "bold"), height=40).pack(side="left", padx=5)
        
        self.stop_button = ctk.CTkButton(left_frame, text="⏹ Stop", 
                     command=self.stop_analysis,
                     font=("Arial", 14, "bold"), height=40,
                     fg_color="red", hover_color="darkred",
                     state="disabled")
        self.stop_button.pack(side="left", padx=5)
        
        # Similarity threshold slider
        threshold_frame = ctk.CTkFrame(left_frame)
        threshold_frame.pack(side="left", padx=20)
        
        ctk.CTkLabel(threshold_frame, text="Similarity:").pack(side="left")
        self.threshold_slider = ctk.CTkSlider(threshold_frame, from_=50, to=100,
                                              number_of_steps=50, width=150,
                                              command=self.update_threshold)
        self.threshold_slider.set(80)
        self.threshold_slider.pack(side="left", padx=5)
        
        self.threshold_label = ctk.CTkLabel(threshold_frame, text="80%", width=40)
        self.threshold_label.pack(side="left")
        
        # Thumbnail checkbox
        self.thumbnail_var = ctk.BooleanVar(value=True)
        self.thumbnail_checkbox = ctk.CTkCheckBox(left_frame, text="Thumbnails", 
                                                  variable=self.thumbnail_var,
                                                  command=self.toggle_thumbnails)
        self.thumbnail_checkbox.pack(side="left", padx=10)
        
        # Right side: File operations
        right_frame = ctk.CTkFrame(control_frame)
        right_frame.pack(side="right", padx=5, pady=5)
        
        ctk.CTkButton(right_frame, text="Save Results", 
                     command=self.save_results).pack(side="left", padx=2)
        ctk.CTkButton(right_frame, text="Load Results", 
                     command=self.load_results).pack(side="left", padx=2)
        
        # Progress bar
        self.progress_frame = ctk.CTkFrame(parent)
        self.progress_frame.pack(fill="x", padx=5, pady=5)
        
        self.progress_label = ctk.CTkLabel(self.progress_frame, text="Ready")
        self.progress_label.pack(anchor="w", padx=10)
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.pack(fill="x", padx=10, pady=5)
        self.progress_bar.set(0)
        
    def create_results_section(self, parent):
        """Create results display section"""
        results_frame = ctk.CTkFrame(parent)
        results_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Title and stats
        header_frame = ctk.CTkFrame(results_frame)
        header_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(header_frame, text="Duplicate Groups:", 
                    font=("Arial", 16, "bold")).pack(side="left", padx=10)
        
        self.stats_label = ctk.CTkLabel(header_frame, text="No results yet")
        self.stats_label.pack(side="left", padx=20)
        
        # Sort dropdown
        ctk.CTkLabel(header_frame, text="Sort by:").pack(side="left", padx=(20, 5))
        self.sort_dropdown = ctk.CTkComboBox(header_frame, 
                                             values=["Size (Largest)", "Size (Smallest)", "Similarity (Highest)", "Similarity (Lowest)"],
                                             command=self.on_sort_changed,
                                             width=180)
        self.sort_dropdown.set("Size (Largest)")
        self.sort_dropdown.pack(side="left", padx=5)
        
        # Delete button
        ctk.CTkButton(header_frame, text="🗑️ Send Selected to Trash", 
                     command=self.delete_selected,
                     fg_color="red", hover_color="darkred",
                     font=("Arial", 12, "bold")).pack(side="right", padx=10)
        
        # Pagination controls
        pagination_frame = ctk.CTkFrame(results_frame)
        pagination_frame.pack(fill="x", padx=5, pady=(0, 5))
        
        self.page_label = ctk.CTkLabel(pagination_frame, text="Page 1 of 1 (0 groups)", 
                                       font=("Arial", 11))
        self.page_label.pack(side="left", padx=10)
        
        self.prev_button = ctk.CTkButton(pagination_frame, text="◀ Previous", 
                                         command=self.previous_page, width=100)
        self.prev_button.pack(side="left", padx=5)
        
        self.next_button = ctk.CTkButton(pagination_frame, text="Next ▶", 
                                         command=self.next_page, width=100)
        self.next_button.pack(side="left", padx=5)
        
        # Jump to page
        ctk.CTkLabel(pagination_frame, text="Jump to page:").pack(side="left", padx=(20, 5))
        self.page_entry = ctk.CTkEntry(pagination_frame, width=60)
        self.page_entry.pack(side="left", padx=5)
        self.page_entry.bind("<Return>", lambda e: self.jump_to_page())
        
        ctk.CTkButton(pagination_frame, text="Go", width=50,
                     command=self.jump_to_page).pack(side="left", padx=5)
        
        # Results display with scrollbar
        self.results_scroll = ctk.CTkScrollableFrame(results_frame)
        self.results_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
    def add_folder(self):
        """Add folder to analysis list"""
        folder = filedialog.askdirectory(title="Select Folder to Analyze")
        if folder:
            # Normalize path to ensure consistency
            folder = os.path.normpath(folder)
            if folder not in self.folders:
                self.folders.append(folder)
                self.update_folder_list()
    
    def remove_folder(self, folder_path):
        """Remove specific folder from list"""
        if folder_path in self.folders:
            self.folders.remove(folder_path)
            self.update_folder_list()
            
    def clear_folders(self):
        """Clear all folders"""
        self.folders = []
        self.update_folder_list()
        
    def update_folder_list(self):
        """Update the folder listbox display with individual remove buttons"""
        # Clear existing widgets
        for widget in self.folder_scroll.winfo_children():
            widget.destroy()
        
        # Add each folder with its own remove button
        for folder in self.folders:
            folder_row = ctk.CTkFrame(self.folder_scroll)
            folder_row.pack(fill="x", padx=2, pady=2)
            
            # Folder path label - highlight if currently scanning
            normalized_folder = os.path.normpath(folder)
            normalized_scanning = os.path.normpath(self.current_scanning_folder) if self.current_scanning_folder else None
            is_scanning = (normalized_scanning and normalized_folder == normalized_scanning)
            
            text_color = "#00FF00" if is_scanning else "white"
            font_style = ("Arial", 10, "bold") if is_scanning else ("Arial", 10, "normal")
            
            ctk.CTkLabel(folder_row, text=folder, anchor="w",
                        text_color=text_color, font=font_style).pack(
                            side="left", fill="x", expand=True, padx=5)
            
            # Remove button for this specific folder
            ctk.CTkButton(folder_row, text="✕", width=30, height=24,
                         command=lambda f=folder: self.remove_folder(f),
                         fg_color="red", hover_color="darkred").pack(side="right", padx=2)
    
    def highlight_current_folder(self, folder_path):
        """Highlight the currently scanning folder in the listbox"""
        self.current_scanning_folder = folder_path
        
        if not folder_path:
            return
        
        # Normalize the folder path for comparison
        normalized_scan_path = os.path.normpath(folder_path)
        
        # Find and highlight the folder row
        for widget in self.folder_scroll.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                # Get the label widget (first child)
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkLabel):
                        label_text = child.cget("text")
                        normalized_label = os.path.normpath(label_text)
                        
                        # Compare normalized paths
                        if normalized_scan_path == normalized_label or normalized_scan_path in normalized_label:
                            # Highlight this folder
                            child.configure(text_color="#00FF00", font=("Arial", 10, "bold"))
                        else:
                            # Normal color
                            child.configure(text_color="white", font=("Arial", 10, "normal"))
                        break
        
        self.update_idletasks()
            
    def update_threshold(self, value):
        """Update similarity threshold"""
        self.threshold_label.configure(text=f"{int(value)}%")
        self.analyzer.similarity_threshold = int(value)
    
    def stop_analysis(self):
        """Stop the current analysis"""
        self.stop_requested = True
        self.progress_label.configure(text="Stopping...")
        self.stop_button.configure(state="disabled")
    
    def toggle_thumbnails(self):
        """Toggle thumbnail generation"""
        self.generate_thumbnails = self.thumbnail_var.get()
        
    def update_progress(self, current, total, message):
        """Update progress bar and label"""
        # Run UI updates on the main thread to avoid Tkinter callback exceptions
        def _do_update():
            try:
                # Extract folder path if in message and highlight
                if isinstance(message, str) and "Scanning:" in message:
                    folder_path = message.split("Scanning: ")[1] if "Scanning: " in message else None
                    if folder_path:
                        self.highlight_current_folder(folder_path)
                elif isinstance(message, str) and (message == "Analysis complete!" or "stopped" in message.lower()):
                    # Clear scanning folder and remove highlighting
                    self.current_scanning_folder = None
                    for widget in self.folder_scroll.winfo_children():
                        if isinstance(widget, ctk.CTkFrame):
                            for child in widget.winfo_children():
                                if isinstance(child, ctk.CTkLabel):
                                    child.configure(text_color="white", font=("Arial", 10, "normal"))
                                    break

                # Update progress label and bar
                self.progress_label.configure(text=message)
                if total and total > 0:
                    try:
                        self.progress_bar.set(max(0.0, min(1.0, float(current) / float(total))))
                    except Exception:
                        self.progress_bar.set(0.0)
                else:
                    self.progress_bar.set(0.5)  # Indeterminate

                self.update_idletasks()
            except Exception:
                # Swallow UI exceptions to avoid crashing background threads
                pass

        try:
            self.after(0, _do_update)
        except Exception:
            # Fallback: attempt direct update if scheduling fails
            _do_update()
        

    def find_exact_duplicates(self):
        """Find exact duplicates in selected folders"""
        if not self.folders:
            messagebox.showwarning("No Folders", "Please add folders to analyze first.")
            return
        
        # Enable stop button and reset flag
        self.stop_requested = False
        self.stop_button.configure(state="normal")
        
        def task():
            try:
                # Scan folders
                self.update_progress(0, None, "Scanning folders...")
                files = self.analyzer.scan_folders(self.folders, self.update_progress, 
                                                  lambda: self.stop_requested)
                
                if self.stop_requested:
                    self.after(0, lambda: self.progress_label.configure(text="Analysis stopped by user"))
                    self.after(0, lambda: self.stop_button.configure(state="disabled"))
                    return
                
                if not files:
                    self.after(0, lambda: messagebox.showinfo("No Files", 
                              "No video files found in selected folders."))
                    self.after(0, lambda: self.stop_button.configure(state="disabled"))
                    return
                
                # Find duplicates
                self.update_progress(0, None, "Finding exact duplicates...")
                self.exact_duplicates = self.analyzer.find_exact_duplicates(
                    files, self.update_progress, lambda: self.stop_requested)
                
                if self.stop_requested:
                    self.after(0, lambda: self.progress_label.configure(text="Analysis stopped by user"))
                    self.after(0, lambda: self.stop_button.configure(state="disabled"))
                    return
                
                # Display results
                self.after(0, lambda: self.display_results(self.exact_duplicates, "Exact"))
                self.after(0, lambda: self.progress_bar.set(1))
                self.after(0, lambda: self.progress_label.configure(text="Analysis complete!"))
                self.after(0, lambda: self.stop_button.configure(state="disabled"))
                
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
                self.after(0, lambda: self.progress_label.configure(text="Error occurred"))
                self.after(0, lambda: self.stop_button.configure(state="disabled"))
        
        # Run in thread
        thread = threading.Thread(target=task, daemon=True)
        thread.start()
        
    def find_similar_files(self):
        """Find similar files in selected folders"""
        if not self.folders:
            messagebox.showwarning("No Folders", "Please add folders to analyze first.")
            return
        
        # Enable stop button and reset flag
        self.stop_requested = False
        self.stop_button.configure(state="normal")
        
        def task():
            try:
                # Scan folders
                self.update_progress(0, None, "Scanning folders...")
                files = self.analyzer.scan_folders(self.folders, self.update_progress,
                                                  lambda: self.stop_requested)
                
                if self.stop_requested:
                    self.after(0, lambda: self.progress_label.configure(text="Analysis stopped by user"))
                    self.after(0, lambda: self.stop_button.configure(state="disabled"))
                    return
                
                if not files:
                    self.after(0, lambda: messagebox.showinfo("No Files", 
                              "No video files found in selected folders."))
                    self.after(0, lambda: self.stop_button.configure(state="disabled"))
                    return
                
                # Find similar files
                self.update_progress(0, None, "Finding similar files...")
                self.similar_files = self.analyzer.find_similar_files(
                    files, self.update_progress, lambda: self.stop_requested)
                
                if self.stop_requested:
                    self.after(0, lambda: self.progress_label.configure(text="Analysis stopped by user"))
                    self.after(0, lambda: self.stop_button.configure(state="disabled"))
                    return
                
                # Display results
                self.after(0, lambda: self.display_results(self.similar_files, "Similar"))
                self.after(0, lambda: self.progress_bar.set(1))
                self.after(0, lambda: self.progress_label.configure(text="Analysis complete!"))
                self.after(0, lambda: self.stop_button.configure(state="disabled"))
                
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
                self.after(0, lambda: self.progress_label.configure(text="Error occurred"))
                self.after(0, lambda: self.stop_button.configure(state="disabled"))
        
        # Run in thread
        thread = threading.Thread(target=task, daemon=True)
        thread.start()
    
    def on_sort_changed(self, choice):
        """Handle sort dropdown change"""
        # Re-sort and re-render current page
        if self.current_sorted_groups:
            self.current_sorted_groups = self.sort_groups(self.current_sorted_groups, self.current_result_type)
            self._render_current_page(regenerate_thumbnails=False)
    
    def sort_groups(self, duplicate_groups, result_type):
        """Sort duplicate groups based on current sort setting"""
        sort_choice = self.sort_dropdown.get()
        
        if "Size" in sort_choice:
            # Sort by total group size
            sorted_groups = sorted(duplicate_groups, 
                                 key=lambda g: sum(f['size'] for f in g),
                                 reverse=("Largest" in sort_choice))
        elif "Similarity" in sort_choice and result_type == "Similar":
            # Sort by average similarity score
            def get_avg_similarity(group):
                if len(group) < 2:
                    return 0
                scores = []
                for file2 in group[1:]:
                    score = self.analyzer.calculate_similarity_score(group[0], file2)
                    scores.append(score)
                return sum(scores) / len(scores) if scores else 0
            
            sorted_groups = sorted(duplicate_groups,
                                 key=get_avg_similarity,
                                 reverse=("Highest" in sort_choice))
        else:
            # For exact duplicates or default, sort by size
            sorted_groups = sorted(duplicate_groups,
                                 key=lambda g: sum(f['size'] for f in g),
                                 reverse=True)
        
        return sorted_groups
        
    def display_results(self, duplicate_groups, result_type, regenerate_thumbnails=True):
        """Display duplicate groups in the results section"""
        # Store results and reset to first page
        self.current_sorted_groups = self.sort_groups(duplicate_groups, result_type)
        self.current_result_type = result_type
        self.current_page = 0
        
        # Render first page
        self._render_current_page(regenerate_thumbnails)
    
    def _render_current_page(self, regenerate_thumbnails=True):
        """Render only the current page of results"""
        # Clear previous display
        for widget in self.results_scroll.winfo_children():
            widget.destroy()
        
        self.selected_for_deletion.clear()
        self.thumbnail_widgets.clear()
        
        if not self.current_sorted_groups:
            ctk.CTkLabel(self.results_scroll, 
                        text=f"No {self.current_result_type.lower()} duplicates found!",
                        font=("Arial", 14)).pack(pady=20)
            self.stats_label.configure(text="No duplicates found")
            self.page_label.configure(text="Page 0 of 0 (0 groups)")
            self.prev_button.configure(state="disabled")
            self.next_button.configure(state="disabled")
            return
        
        # Calculate pagination
        total_groups = len(self.current_sorted_groups)
        total_pages = (total_groups + self.groups_per_page - 1) // self.groups_per_page
        start_idx = self.current_page * self.groups_per_page
        end_idx = min(start_idx + self.groups_per_page, total_groups)
        page_groups = self.current_sorted_groups[start_idx:end_idx]
        
        # Update stats
        total_files = sum(len(group) for group in self.current_sorted_groups)
        page_files = sum(len(group) for group in page_groups)
        self.stats_label.configure(
            text=f"{total_groups} groups, {total_files} files total | Showing {len(page_groups)} groups, {page_files} files")
        
        # Update pagination controls
        self.page_label.configure(
            text=f"Page {self.current_page + 1} of {total_pages} ({total_groups} groups)")
        self.prev_button.configure(state="normal" if self.current_page > 0 else "disabled")
        self.next_button.configure(state="normal" if self.current_page < total_pages - 1 else "disabled")
        
        # Render groups on current page
        for idx, group in enumerate(page_groups):
            actual_group_num = start_idx + idx + 1
            self.create_group_display(group, actual_group_num, self.current_result_type)
        
        # Generate thumbnails for current page
        # Always generate for files that don't have thumbnails yet
        # Only skip if regenerate_thumbnails is False AND all thumbnails already exist
        if self.generate_thumbnails:
            files_needing_thumbnails = []
            for group in page_groups:
                for file_info in group:
                    if not file_info.get('thumbnail') or regenerate_thumbnails:
                        files_needing_thumbnails.append(file_info)
            
            if files_needing_thumbnails:
                self.generate_thumbnails_async_for_files(files_needing_thumbnails)
        
        self.progress_label.configure(text="Ready")
        self.progress_bar.set(0)
    
    def previous_page(self):
        """Navigate to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self._render_current_page(regenerate_thumbnails=False)
    
    def next_page(self):
        """Navigate to next page"""
        total_pages = (len(self.current_sorted_groups) + self.groups_per_page - 1) // self.groups_per_page
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self._render_current_page(regenerate_thumbnails=False)
    
    def jump_to_page(self):
        """Jump to specific page number"""
        try:
            page_num = int(self.page_entry.get())
            total_pages = (len(self.current_sorted_groups) + self.groups_per_page - 1) // self.groups_per_page
            
            if 1 <= page_num <= total_pages:
                self.current_page = page_num - 1
                self._render_current_page(regenerate_thumbnails=False)
                self.page_entry.delete(0, 'end')
            else:
                messagebox.showwarning("Invalid Page", f"Please enter a page number between 1 and {total_pages}")
        except ValueError:
            messagebox.showwarning("Invalid Input", "Please enter a valid page number")
    
    def load_thumbnail(self, file_info, thumb_label):
        """Load and display thumbnail image"""
        try:
            file_path = file_info['path']
            
            # Check if image already cached
            if file_path in self.thumbnail_images:
                photo = self.thumbnail_images[file_path]
                thumb_label.configure(image=photo, text="")
                return
            
            # Load and create new CTkImage
            thumb_image = Image.open(file_info['thumbnail'])
            thumb_image.thumbnail((120, 80), Image.Resampling.LANCZOS)
            photo = ctk.CTkImage(light_image=thumb_image, dark_image=thumb_image, size=(120, 80))
            
            # Store in persistent cache to prevent garbage collection
            self.thumbnail_images[file_path] = photo
            
            thumb_label.configure(image=photo, text="")
        except Exception:
            pass
    
    def generate_thumbnails_async(self, groups):
        """Generate thumbnails in background thread for groups"""
        files_to_process = []
        for group in groups:
            for file_info in group:
                if not file_info.get('thumbnail'):
                    files_to_process.append(file_info)
        
        if files_to_process:
            self.generate_thumbnails_async_for_files(files_to_process)
    
    def generate_thumbnails_async_for_files(self, files_to_process):
        """Generate thumbnails in background thread for specific files"""
        def task():
            if not files_to_process:
                self.after(0, lambda: self.progress_label.configure(text="Ready"))
                return
            
            total = len(files_to_process)
            for idx, file_info in enumerate(files_to_process, 1):
                # Generate thumbnail
                thumb_path = self.analyzer.get_video_thumbnail(file_info['path'])
                file_info['thumbnail'] = thumb_path
                
                # Update UI in main thread
                if thumb_path and os.path.exists(thumb_path):
                    self.after(0, lambda fi=file_info: self.update_thumbnail_in_ui(fi))
                
                # Update progress
                self.after(0, lambda i=idx, t=total: 
                          self.update_progress(i, t, f"Generating thumbnails... {i}/{t}"))
            
            # Clear progress when done
            self.after(0, lambda: self.progress_label.configure(text="Ready"))
            self.after(0, lambda: self.progress_bar.set(0))
        
        # Run in background thread
        thread = threading.Thread(target=task, daemon=True)
        thread.start()
    
    def update_thumbnail_in_ui(self, file_info):
        """Update thumbnail in UI for a specific file"""
        # Get the thumbnail widget for this file
        thumb_label = self.thumbnail_widgets.get(file_info['path'])
        if thumb_label and thumb_label.winfo_exists():
            self.load_thumbnail(file_info, thumb_label)
            
    def create_group_display(self, group, group_num, result_type):
        """Create display for a single duplicate group"""
        # Group container
        group_frame = ctk.CTkFrame(self.results_scroll)
        group_frame.pack(fill="x", padx=5, pady=10)
        
        # Group header
        header_frame = ctk.CTkFrame(group_frame)
        header_frame.pack(fill="x", padx=5, pady=5)
        
        total_size = sum(f['size'] for f in group)
        size_mb = total_size / (1024 * 1024)
        
        header_text = f"Group {group_num} - {len(group)} files - {size_mb:.2f} MB total"
        
        # Add similarity score for similar files groups
        if result_type == "Similar" and len(group) >= 2:
            # Calculate average similarity between first file and others
            scores = []
            for file2 in group[1:]:
                score = self.analyzer.calculate_similarity_score(group[0], file2)
                scores.append(score)
            avg_score = sum(scores) / len(scores) if scores else 0
            header_text += f" - Similarity: {avg_score:.1f}%"
        
        ctk.CTkLabel(header_frame, 
                    text=header_text,
                    font=("Arial", 13, "bold")).pack(side="left", padx=10)
        
        # Files in group
        for file_info in group:
            self.create_file_row(group_frame, file_info)
            
    def create_file_row(self, parent, file_info):
        """Create a row for a single file"""
        file_frame = ctk.CTkFrame(parent)
        file_frame.pack(fill="x", padx=10, pady=5)
        
        # Checkbox for deletion
        var = ctk.BooleanVar()
        checkbox = ctk.CTkCheckBox(file_frame, text="", variable=var,
                                   command=lambda: self.toggle_file_selection(
                                       file_info['path'], var.get()))
        checkbox.pack(side="left", padx=5, pady=5)
        
        # Thumbnail - generate on-demand if enabled
        thumb_label = None
        if self.generate_thumbnails:
            # Create placeholder for thumbnail
            thumb_label = ctk.CTkLabel(file_frame, text="⏳", width=120, height=80,
                                      font=("Arial", 40))
            thumb_label.pack(side="left", padx=5, pady=5)
            
            # Store reference for async updates
            self.thumbnail_widgets[file_info['path']] = thumb_label
            
            # Check if thumbnail already exists
            if file_info.get('thumbnail') and os.path.exists(file_info['thumbnail']):
                self.load_thumbnail(file_info, thumb_label)
        
        # File info
        info_frame = ctk.CTkFrame(file_frame)
        info_frame.pack(side="left", fill="x", expand=True, padx=5)
        
        # Filename
        ctk.CTkLabel(info_frame, text=file_info['name'], 
                    font=("Arial", 11, "bold"),
                    anchor="w").pack(fill="x")
        
        # Path and size
        size_mb = file_info['size'] / (1024 * 1024)
        modified_date = datetime.fromtimestamp(file_info['modified']).strftime('%Y-%m-%d %H:%M:%S')
        details = f"{file_info['path']} - {size_mb:.2f} MB - Modified: {modified_date}"
        ctk.CTkLabel(info_frame, text=details, 
                    font=("Arial", 9),
                    text_color="gray",
                    anchor="w").pack(fill="x")
        
        # Buttons frame
        btn_frame = ctk.CTkFrame(file_frame)
        btn_frame.pack(side="right", padx=5, pady=5)
        
        # Play button
        ctk.CTkButton(btn_frame, text="▶️ Play", width=80,
                     command=lambda: self.play_video(file_info['path'])
                     ).pack(side="left", padx=2)
        
        # Open folder button
        ctk.CTkButton(btn_frame, text="📁 Open", width=80,
                     command=lambda: self.open_file_location(file_info['path'])
                     ).pack(side="left", padx=2)
        
    def toggle_file_selection(self, filepath, selected):
        """Toggle file selection for deletion"""
        # Normalize path for consistent comparison
        filepath = os.path.normpath(filepath)
        if selected:
            self.selected_for_deletion.add(filepath)
        else:
            self.selected_for_deletion.discard(filepath)
            
    def open_file_location(self, filepath):
        """Open file location in explorer"""
        folder = os.path.dirname(filepath)
        os.startfile(folder)
    
    def play_video(self, filepath):
        """Play video in default media player"""
        try:
            if not os.path.exists(filepath):
                messagebox.showerror("Error", "File not found!")
                return
            
            if platform.system() == "Windows":
                os.startfile(filepath)
            elif platform.system() == "Darwin":  # macOS
                subprocess.Popen(["open", filepath])
            else:  # Linux
                subprocess.Popen(["xdg-open", filepath])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open video: {str(e)}")
        
    def delete_selected(self):
        """Send selected files to trash"""
        if not self.selected_for_deletion:
            messagebox.showwarning("No Selection", "Please select files to delete.")
            return
        
        # Confirm deletion
        count = len(self.selected_for_deletion)
        response = messagebox.askyesno(
            "Confirm Deletion",
            f"Send {count} file(s) to trash?\n\nThis action can be undone from the Recycle Bin.")
        
        if not response:
            return
        
        # Delete files
        success_count = 0
        failed = []
        
        for filepath in self.selected_for_deletion:
            try:
                # Normalize path to ensure consistency
                filepath = os.path.normpath(filepath)
                
                # Check if file still exists
                if not os.path.exists(filepath):
                    failed.append((filepath, "File not found"))
                    continue
                    
                send2trash(filepath)
                success_count += 1
            except Exception as e:
                failed.append((filepath, str(e)))
        
        # Show results
        if failed:
            error_msg = f"Successfully deleted {success_count} file(s).\n\n"
            error_msg += f"Failed to delete {len(failed)} file(s):\n"
            for path, error in failed[:5]:  # Show first 5 errors
                error_msg += f"\n{os.path.basename(path)}: {error}"
            messagebox.showwarning("Partial Success", error_msg)
        else:
            messagebox.showinfo("Success", f"Successfully sent {success_count} file(s) to trash!")
        
        # Clear selection and refresh results by removing deleted files
        deleted_paths = set(filepath for filepath in list(self.selected_for_deletion) if filepath not in [fp for fp, _ in failed])
        self.selected_for_deletion.clear()
        
        # Remove deleted files from stored results
        if self.exact_duplicates:
            self.exact_duplicates = [
                [f for f in group if os.path.normpath(f['path']) not in deleted_paths and os.path.exists(f['path'])]
                for group in self.exact_duplicates
            ]
            # Remove empty groups and groups with only 1 file
            self.exact_duplicates = [g for g in self.exact_duplicates if len(g) > 1]
            
            # Update current display if showing exact duplicates
            if self.current_result_type == "Exact":
                self.current_sorted_groups = [
                    [f for f in group if os.path.normpath(f['path']) not in deleted_paths and os.path.exists(f['path'])]
                    for group in self.current_sorted_groups
                ]
                self.current_sorted_groups = [g for g in self.current_sorted_groups if len(g) > 1]
                
                # Stay on same page if possible, otherwise go to last page
                total_pages = max(1, (len(self.current_sorted_groups) + self.groups_per_page - 1) // self.groups_per_page)
                if self.current_page >= total_pages:
                    self.current_page = max(0, total_pages - 1)
                
                self._render_current_page(regenerate_thumbnails=False)
                
        elif self.similar_files:
            self.similar_files = [
                [f for f in group if os.path.normpath(f['path']) not in deleted_paths and os.path.exists(f['path'])]
                for group in self.similar_files
            ]
            # Remove empty groups and groups with only 1 file
            self.similar_files = [g for g in self.similar_files if len(g) > 1]
            
            # Update current display if showing similar files
            if self.current_result_type == "Similar":
                self.current_sorted_groups = [
                    [f for f in group if os.path.normpath(f['path']) not in deleted_paths and os.path.exists(f['path'])]
                    for group in self.current_sorted_groups
                ]
                self.current_sorted_groups = [g for g in self.current_sorted_groups if len(g) > 1]
                
                # Stay on same page if possible, otherwise go to last page
                total_pages = max(1, (len(self.current_sorted_groups) + self.groups_per_page - 1) // self.groups_per_page)
                if self.current_page >= total_pages:
                    self.current_page = max(0, total_pages - 1)
                
                self._render_current_page(regenerate_thumbnails=False)
            
    def save_results(self):
        """Save analysis results to file"""
        if not self.exact_duplicates and not self.similar_files:
            messagebox.showwarning("No Results", "No results to save.")
            return
        
        filepath = filedialog.asksaveasfilename(
            parent=self,
            title="Save Results",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        
        if filepath:
            success = self.analyzer.save_results(
                filepath, self.exact_duplicates, self.similar_files)
            if success:
                messagebox.showinfo("Success", "Results saved successfully!")
            else:
                messagebox.showerror("Error", "Failed to save results.")
                
    def load_results(self):
        """Load analysis results from file"""
        filepath = filedialog.askopenfilename(
            parent=self,
            title="Load Results",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        
        if filepath:
            exact, similar = self.analyzer.load_results(filepath)
            
            if exact or similar:
                self.exact_duplicates = exact
                self.similar_files = similar
                
                # Display based on what was loaded
                if exact:
                    self.display_results(exact, "Exact")
                elif similar:
                    self.display_results(similar, "Similar")
                    
                messagebox.showinfo("Success", "Results loaded successfully!")
            else:
                messagebox.showerror("Error", "Failed to load results.")


def main():
    app = FileComparerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
