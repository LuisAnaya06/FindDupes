"""
File Comparer - Duplicate File Analyzer with AI-powered matching
Main GUI Application using CustomTkinter
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
        
        # Folder listbox
        self.folder_listbox = ctk.CTkTextbox(list_frame, height=100)
        self.folder_listbox.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Buttons
        btn_frame = ctk.CTkFrame(list_frame)
        btn_frame.pack(side="right", fill="y")
        
        ctk.CTkButton(btn_frame, text="Add Folder", command=self.add_folder,
                     width=120).pack(pady=2)
        ctk.CTkButton(btn_frame, text="Remove Selected", command=self.remove_folder,
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
            
    def remove_folder(self):
        """Remove selected folder from list"""
        # Simple implementation: clear selection and re-select
        self.folders = []
        self.folder_listbox.delete("1.0", "end")
        
    def clear_folders(self):
        """Clear all folders"""
        self.folders = []
        self.update_folder_list()
        
    def update_folder_list(self):
        """Update the folder listbox display"""
        self.folder_listbox.delete("1.0", "end")
        for folder in self.folders:
            self.folder_listbox.insert("end", f"{folder}\n")
            
    def update_threshold(self, value):
        """Update similarity threshold"""
        self.threshold_label.configure(text=f"{int(value)}%")
        self.analyzer.similarity_threshold = int(value)
    
    def stop_analysis(self):
        """Stop the current analysis"""
        self.stop_requested = True
        self.progress_label.configure(text="Stopping...")
        self.stop_button.configure(state="disabled")
        
    def update_progress(self, current, total, message):
        """Update progress bar and label"""
        self.progress_label.configure(text=message)
        if total:
            self.progress_bar.set(current / total)
        else:
            self.progress_bar.set(0.5)  # Indeterminate
        self.update_idletasks()
        
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
        # Determine current result type based on which list has data
        if self.exact_duplicates:
            result_type = "Exact"
            groups = self.exact_duplicates
        elif self.similar_files:
            result_type = "Similar"
            groups = self.similar_files
        else:
            return
        
        # Re-display with new sort
        self.display_results(groups, result_type)
    
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
        
    def display_results(self, duplicate_groups, result_type):
        """Display duplicate groups in the results section"""
        # Clear previous results
        for widget in self.results_scroll.winfo_children():
            widget.destroy()
        
        self.selected_for_deletion.clear()
        
        if not duplicate_groups:
            ctk.CTkLabel(self.results_scroll, 
                        text=f"No {result_type.lower()} duplicates found!",
                        font=("Arial", 14)).pack(pady=20)
            self.stats_label.configure(text="No duplicates found")
            return
        
        # Sort groups
        sorted_groups = self.sort_groups(duplicate_groups, result_type)
        
        # Update stats
        total_files = sum(len(group) for group in sorted_groups)
        self.stats_label.configure(
            text=f"{len(sorted_groups)} groups, {total_files} files")
        
        # Display each group
        for idx, group in enumerate(sorted_groups, 1):
            self.create_group_display(group, idx, result_type)
            
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
        
        # Thumbnail
        if file_info.get('thumbnail') and os.path.exists(file_info['thumbnail']):
            try:
                thumb_image = Image.open(file_info['thumbnail'])
                thumb_image.thumbnail((120, 80), Image.Resampling.LANCZOS)
                photo = ctk.CTkImage(light_image=thumb_image, dark_image=thumb_image, size=(120, 80))
                thumb_label = ctk.CTkLabel(file_frame, image=photo, text="")
                thumb_label.image = photo  # Keep a reference
                thumb_label.pack(side="left", padx=5, pady=5)
            except Exception:
                pass
        
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
        
        # Clear selection and refresh results by removing deleted files from current results
        self.selected_for_deletion.clear()
        
        # Remove deleted files from results without re-scanning
        if self.exact_duplicates:
            self.exact_duplicates = [
                [f for f in group if f['path'] not in {fp for fp, _ in failed} and os.path.exists(f['path'])]
                for group in self.exact_duplicates
            ]
            # Remove empty groups and groups with only 1 file
            self.exact_duplicates = [g for g in self.exact_duplicates if len(g) > 1]
            self.display_results(self.exact_duplicates, "Exact")
        elif self.similar_files:
            self.similar_files = [
                [f for f in group if f['path'] not in {fp for fp, _ in failed} and os.path.exists(f['path'])]
                for group in self.similar_files
            ]
            # Remove empty groups and groups with only 1 file
            self.similar_files = [g for g in self.similar_files if len(g) > 1]
            self.display_results(self.similar_files, "Similar")
            
    def save_results(self):
        """Save analysis results to file"""
        if not self.exact_duplicates and not self.similar_files:
            messagebox.showwarning("No Results", "No results to save.")
            return
        
        filepath = filedialog.asksaveasfilename(
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
