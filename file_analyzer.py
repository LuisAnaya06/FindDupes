"""
File Analyzer Module - Handles duplicate detection logic
"""
import hashlib
import os
from pathlib import Path
from typing import Dict, List, Tuple, Set
from collections import defaultdict
from rapidfuzz import fuzz
import re
import json
from datetime import datetime
import tempfile

# Try to import custom patterns first, fall back to default if not available
try:
    from filename_patterns_custom import get_all_patterns
    print("Using custom filename patterns from filename_patterns_custom.py")
except ImportError:
    from filename_patterns import get_all_patterns

# Try to import cv2, but make it optional
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("Warning: opencv-python not available. Thumbnail generation will be disabled.")


class FileAnalyzer:
    def __init__(self, similarity_threshold=80):
        """
        Initialize the file analyzer
        
        Args:
            similarity_threshold: Minimum similarity score (0-100) for fuzzy matching
        """
        self.similarity_threshold = similarity_threshold
        self.video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', 
                                '.webm', '.m4v', '.mpeg', '.mpg', '.3gp', '.f4v', 
                                '.ts', '.m3u8'}
        
    def get_file_hash(self, filepath: str, chunk_size=8192) -> str:
        """Calculate SHA256 hash of file content"""
        sha256_hash = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(chunk_size), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except (IOError, OSError):
            return None
    
    def get_file_info(self, filepath: str) -> Dict:
        """Extract file metadata"""
        try:
            # Normalize path to use backslashes on Windows
            filepath = os.path.normpath(filepath)
            stat = os.stat(filepath)
            return {
                'path': filepath,
                'name': os.path.basename(filepath),
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'extension': os.path.splitext(filepath)[1].lower(),
                'normalized_name': self.normalize_filename(os.path.splitext(os.path.basename(filepath))[0])
            }
        except (IOError, OSError):
            return None
    
    def normalize_filename(self, filename: str) -> str:
        """
        Normalize filename for better matching by removing common patterns.
        
        All patterns are defined in filename_patterns.py for easy customization.
        Edit that file to add your own custom patterns!
        """
        # Convert to lowercase
        name = filename.lower()
        
        # Get all patterns from the patterns file
        patterns_to_remove = get_all_patterns()
        
        # Apply all patterns
        for pattern in patterns_to_remove:
            name = re.sub(pattern, ' ', name, flags=re.IGNORECASE)
        
        # Remove extra whitespace
        name = ' '.join(name.split())
        
        return name.strip()
    
    def calculate_similarity_score(self, file1: Dict, file2: Dict) -> float:
        """
        Calculate comprehensive similarity score between two files
        
        Returns: Similarity score 0-100
        """
        scores = []
        weights = []
        
        # 1. Normalized filename matching (token_sort_ratio handles word order better)
        name1 = file1.get('normalized_name', os.path.splitext(file1['name'])[0])
        name2 = file2.get('normalized_name', os.path.splitext(file2['name'])[0])
        
        # Use token_sort_ratio for better matching when words are reordered
        token_score = fuzz.token_sort_ratio(name1, name2)
        scores.append(token_score)
        weights.append(0.5)  # 50% weight on name similarity
        
        # 2. Original filename matching (for backup)
        orig_name1 = os.path.splitext(file1['name'])[0].lower()
        orig_name2 = os.path.splitext(file2['name'])[0].lower()
        orig_score = fuzz.ratio(orig_name1, orig_name2)
        scores.append(orig_score)
        weights.append(0.2)  # 20% weight
        
        # 3. File size similarity (within 5% is considered similar)
        size1 = file1['size']
        size2 = file2['size']
        if size1 > 0 and size2 > 0:
            size_diff = abs(size1 - size2) / max(size1, size2)
            if size_diff <= 0.05:  # Within 5%
                size_score = 100 * (1 - size_diff / 0.05)  # Scale to 0-100
            else:
                size_score = max(0, 100 - size_diff * 100)
            scores.append(size_score)
            weights.append(0.3)  # 30% weight on size similarity
        
        # Calculate weighted average
        if sum(weights) > 0:
            final_score = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
        else:
            final_score = 0
        
        return final_score
    
    def get_video_thumbnail(self, filepath: str, width=120, height=80) -> str:
        """
        Extract thumbnail from video file
        
        Args:
            filepath: Path to video file
            width: Thumbnail width
            height: Thumbnail height
        
        Returns:
            Path to cached thumbnail image or None if failed
        """
        # Return None if cv2 is not available
        if not CV2_AVAILABLE:
            return None
            
        try:
            # Suppress OpenCV/ffmpeg warnings about corrupted video files
            os.environ['OPENCV_LOG_LEVEL'] = 'ERROR'
            if CV2_AVAILABLE:
                cv2.setLogLevel(0)  # Suppress all OpenCV logs
            
            # Create cache directory for thumbnails
            cache_dir = os.path.join(tempfile.gettempdir(), 'FindDupes_thumbnails')
            os.makedirs(cache_dir, exist_ok=True)
            
            # Create unique filename for thumbnail based on file path hash
            thumb_name = hashlib.md5(filepath.encode()).hexdigest() + '.jpg'
            thumb_path = os.path.join(cache_dir, thumb_name)
            
            # Return cached thumbnail if it exists
            if os.path.exists(thumb_path):
                return thumb_path
            
            # Extract first frame from video
            cap = cv2.VideoCapture(filepath)
            if not cap.isOpened():
                return None
            
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                return None
            
            # Resize frame to thumbnail size
            frame = cv2.resize(frame, (width, height))
            
            # Save thumbnail
            cv2.imwrite(thumb_path, frame)
            return thumb_path
            
        except Exception:
            return None
    
    def scan_folders(self, folders: List[str], progress_callback=None, stop_check=None) -> List[Dict]:
        """
        Scan multiple folders for video files
        
        Args:
            folders: List of folder paths to scan
            progress_callback: Optional callback function(current, total, message)
            stop_check: Optional callback function that returns True if should stop
        
        Returns:
            List of file info dictionaries
        """
        all_files = []
        
        for folder in folders:
            if not os.path.exists(folder):
                continue
                
            for root, dirs, files in os.walk(folder):
                # Check if user requested stop
                if stop_check and stop_check():
                    return all_files
                    
                for file in files:
                    # Check if user requested stop
                    if stop_check and stop_check():
                        return all_files
                        
                    filepath = os.path.join(root, file)
                    ext = os.path.splitext(file)[1].lower()
                    
                    if ext in self.video_extensions:
                        file_info = self.get_file_info(filepath)
                        if file_info:
                            # Add thumbnail path
                            file_info['thumbnail'] = self.get_video_thumbnail(filepath)
                            all_files.append(file_info)
                            
                            if progress_callback:
                                progress_callback(len(all_files), None, f"Scanning: {file}")
        
        return all_files
    
    def find_exact_duplicates(self, files: List[Dict], progress_callback=None, stop_check=None) -> List[List[Dict]]:
        """
        Find exact duplicates by comparing file hashes
        
        Args:
            files: List of file info dictionaries
            progress_callback: Optional callback function(current, total, message)
            stop_check: Optional callback function that returns True if should stop
        
        Returns:
            List of duplicate groups (each group is a list of files)
        """
        # Group by size first (optimization)
        size_groups = defaultdict(list)
        for file in files:
            size_groups[file['size']].append(file)
        
        # Only hash files with matching sizes
        hash_groups = defaultdict(list)
        total_to_hash = sum(len(group) for group in size_groups.values() if len(group) > 1)
        hashed_count = 0
        
        for size, file_group in size_groups.items():
            if len(file_group) > 1:  # Only hash if there are potential duplicates
                for file in file_group:
                    # Check if user requested stop
                    if stop_check and stop_check():
                        return []
                        
                    if progress_callback:
                        hashed_count += 1
                        progress_callback(hashed_count, total_to_hash, f"Hashing: {file['name']}")
                    
                    file_hash = self.get_file_hash(file['path'])
                    if file_hash:
                        file['hash'] = file_hash
                        hash_groups[file_hash].append(file)
        
        # Return only groups with duplicates
        duplicates = [group for group in hash_groups.values() if len(group) > 1]
        return duplicates
    
    def find_similar_files(self, files: List[Dict], progress_callback=None, stop_check=None) -> List[List[Dict]]:
        """
        Find similar files by advanced fuzzy matching
        
        Uses multiple algorithms:
        - Normalized filename matching (removes quality tags, dates, etc.)
        - Token-based matching (handles word reordering)
        - File size similarity (within 5% tolerance)
        - Weighted scoring system
        
        Args:
            files: List of file info dictionaries
            progress_callback: Optional callback function(current, total, message)
            stop_check: Optional callback function that returns True if should stop
        
        Returns:
            List of similar file groups
        """
        similar_groups = []
        processed = set()
        total = len(files)
        
        for i, file1 in enumerate(files):
            # Check if user requested stop
            if stop_check and stop_check():
                return similar_groups
                
            if progress_callback:
                progress_callback(i + 1, total, f"Comparing: {file1['name']}")
            
            if file1['path'] in processed:
                continue
            
            group = [file1]
            processed.add(file1['path'])
            
            for file2 in files[i + 1:]:
                if file2['path'] in processed:
                    continue
                
                # Compare only same extension files
                if file1['extension'] == file2['extension']:
                    # Use comprehensive similarity scoring
                    similarity = self.calculate_similarity_score(file1, file2)
                    
                    if similarity >= self.similarity_threshold:
                        group.append(file2)
                        processed.add(file2['path'])
            
            if len(group) > 1:
                # Sort group by filename for consistency
                group.sort(key=lambda x: x['name'])
                similar_groups.append(group)
        
        return similar_groups
    
    def save_results(self, filepath: str, exact_dupes: List[List[Dict]], 
                    similar_files: List[List[Dict]]) -> bool:
        """Save analysis results to JSON file"""
        try:
            data = {
                'timestamp': datetime.now().isoformat(),
                'exact_duplicates': exact_dupes,
                'similar_files': similar_files
            }
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving results: {e}")
            return False
    
    def load_results(self, filepath: str) -> Tuple[List[List[Dict]], List[List[Dict]]]:
        """Load analysis results from JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('exact_duplicates', []), data.get('similar_files', [])
        except Exception as e:
            print(f"Error loading results: {e}")
            return [], []
