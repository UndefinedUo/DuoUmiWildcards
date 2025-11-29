"""
DuoUmiWild - ComfyUI Wildcard Node
A custom node for ComfyUI that feeds random lines from .txt wildcard files into prompts.
"""

import os
import random
import re
import glob
import textwrap
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import torch
import folder_paths


class WildcardNode:
    """
    A ComfyUI node that randomly selects lines from .txt files in the wildcards directory.
    Supports multiple wildcards, nested folders, and recursive wildcards.
    """

    def __init__(self):
        self.wildcard_dir = os.path.join(os.path.dirname(__file__), "wildcards")
        # Create wildcards directory if it doesn't exist
        if not os.path.exists(self.wildcard_dir):
            os.makedirs(self.wildcard_dir)

        self.output_dir = folder_paths.get_temp_directory()
        self.type = "temp"

        # Cache for loaded wildcard files
        self.loaded_tags = {}
        self.all_txt_files = {}
        self.refresh_file_cache()

    def refresh_file_cache(self):
        """Build a cache of all .txt files for quick lookup, supporting nested folders."""
        self.all_txt_files = glob.glob(os.path.join(self.wildcard_dir, '**/*.txt'), recursive=True)
        # Create basename to path mapping (ignoring folders for simple lookups)
        self.txt_basename_to_path = {
            os.path.basename(file).lower().replace('.txt', ''): file
            for file in self.all_txt_files
        }
        # Also create full relative path mapping for nested folder support
        self.txt_relpath_to_path = {
            os.path.relpath(file, self.wildcard_dir).lower().replace('.txt', '').replace('\\', '/'): file
            for file in self.all_txt_files
        }

    @classmethod
    def INPUT_TYPES(cls):
        """
        Define the input parameters for the node.
        """
        return {
            "required": {
                "text": ("STRING", {
                    "multiline": True,
                    "default": "a photo of __subject__, __style__",
                    "dynamicPrompts": False
                }),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff,
                    "tooltip": "Seed for random selection. Use the same seed for consistent results."
                }),
                "autorefresh": (["Yes", "No"], {
                    "default": "No",
                    "tooltip": "Yes: reload wildcard files each time (slower, see edits immediately). No: cache files (faster)."
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("processed_text",)
    FUNCTION = "process_wildcards"
    OUTPUT_NODE = True
    CATEGORY = "DuoUmiWild"

    def read_wildcard_file(self, filename, cache_files=True):
        """
        Read a wildcard file and return valid lines.
        Supports nested folder paths like "subfolder/filename" or just "filename".

        Args:
            filename: Name of the file (without .txt extension), may include subfolder path
            cache_files: Whether to cache file contents

        Returns:
            list: Lines from the file, or empty list if file not found
        """
        # Check cache first if caching is enabled
        if cache_files and filename in self.loaded_tags:
            return self.loaded_tags[filename]

        # Normalize the filename
        normalized = filename.lower().replace('\\', '/')

        # Try multiple lookup strategies:
        # 1. Direct relative path match (for nested folders)
        filepath = self.txt_relpath_to_path.get(normalized)

        # 2. Basename match (for simple filenames)
        if not filepath:
            filepath = self.txt_basename_to_path.get(normalized)

        # 3. Direct construction
        if not filepath:
            filepath = os.path.join(self.wildcard_dir, f"{filename}.txt")

        if not filepath or not os.path.exists(filepath):
            print(f"DuoUmiWild: Wildcard file not found: {filename}")
            return []

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = []
                for line in f:
                    line = line.strip()
                    # Skip empty lines
                    if not line:
                        continue
                    # Skip comment-only lines
                    if line.startswith('#'):
                        continue
                    # Remove inline comments
                    if '#' in line:
                        line = line.split('#')[0].strip()
                    if line:  # Only add if there's content after removing comments
                        lines.append(line)

                # Cache the result if caching is enabled
                if cache_files:
                    self.loaded_tags[filename] = lines

                return lines
        except Exception as e:
            print(f"DuoUmiWild: Error reading file {filepath}: {e}")
            return []

    def process_range_wildcard(self, match, cache_files=True):
        """
        Process wildcard with range syntax like __0-2$$filename__ or nested wildcards.

        Args:
            match: Regex match object containing the wildcard
            cache_files: Whether to cache file contents

        Returns:
            str: Selected items joined with commas, or original if error
        """
        content = match.group(1)

        # Check for range syntax: num-num$$filename or num$$filename
        if '$$' in content:
            range_part, filename = content.split('$$', 1)
            lines = self.read_wildcard_file(filename, cache_files)

            if not lines:
                return match.group(0)  # Return original if no lines

            try:
                # Parse range
                if '-' in range_part:
                    parts = range_part.split('-')
                    low = int(parts[0]) if parts[0] else 0
                    high = int(parts[1]) if parts[1] else len(lines)
                else:
                    # Single number
                    low = high = int(range_part)

                # Clamp to valid range
                low = max(0, min(low, len(lines)))
                high = max(0, min(high, len(lines)))

                if low > high:
                    low, high = high, low

                # Select random number of items within range
                num_items = random.randint(low, high)
                if num_items == 0:
                    return ""

                # Randomly select items
                selected = random.sample(lines, min(num_items, len(lines)))
                return ", ".join(selected)

            except (ValueError, Exception) as e:
                print(f"DuoUmiWild: Error processing range wildcard: {e}")
                return random.choice(lines) if lines else match.group(0)
        else:
            # Simple wildcard without range - check if it's a nested wildcard
            if content.startswith('__') and content.endswith('__'):
                # This is a nested wildcard, will be processed in next iteration
                return match.group(0)

            lines = self.read_wildcard_file(content, cache_files)
            if lines:
                selected = random.choice(lines)
                # Check if selected line contains nested wildcards
                if '__' in selected:
                    # It will be processed in the next recursive iteration
                    return selected
                return selected
            else:
                return match.group(0)  # Return original if no lines found

    def process_wildcards(self, text, seed, autorefresh):
        """
        Process all wildcards in the input text with recursive support.

        Args:
            text: Input text containing wildcards in __filename__ format
            seed: Random seed for reproducible results
            autorefresh: Whether to refresh file cache and reload files each time

        Returns:
            dict: Contains UI preview and result tuple
        """
        # Set random seed for reproducibility
        random.seed(seed)

        # Refresh file cache if autorefresh is enabled
        cache_files = (autorefresh == "No")
        if autorefresh == "Yes":
            self.refresh_file_cache()
            self.loaded_tags.clear()

        # Pattern to match __content__ wildcards
        wildcard_pattern = re.compile(r'__([^_]+(?:_[^_]+)*)__')

        # Process wildcards multiple times to handle nested wildcards
        max_iterations = 20
        iteration = 0
        previous_text = None

        while previous_text != text and iteration < max_iterations:
            previous_text = text
            text = wildcard_pattern.sub(lambda m: self.process_range_wildcard(m, cache_files), text)
            iteration += 1

        # Clean up any extra commas or whitespace
        text = re.sub(r',\s*,', ',', text)  # Remove double commas
        text = re.sub(r',\s*$', '', text)   # Remove trailing commas
        text = re.sub(r'^\s*,\s*', '', text)  # Remove leading commas
        text = re.sub(r'\s+', ' ', text)     # Normalize whitespace
        text = text.strip()

        # Generate preview image
        preview_result = self.generate_preview(text)

        # Return with UI preview
        return {"ui": {"images": preview_result}, "result": (text,)}

    def generate_preview(self, text):
        """
        Generate a preview image of the processed text.

        Args:
            text: The processed text to display

        Returns:
            list: Preview image info for ComfyUI UI
        """
        img_width = 800
        font_size = 24
        margin = 20
        bg_color = (30, 30, 30)
        text_color = (230, 230, 230)

        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            try:
                # Try alternative font paths
                font = ImageFont.truetype("Arial.ttf", font_size)
            except IOError:
                font = ImageFont.load_default()

        char_width = font_size * 0.55
        chars_per_line = int((img_width - (2 * margin)) / char_width)
        lines = textwrap.wrap(text, width=chars_per_line)

        line_height = font_size + 8
        text_block_height = len(lines) * line_height
        img_height = text_block_height + (margin * 2)

        img = Image.new('RGB', (img_width, img_height), color=bg_color)
        draw = ImageDraw.Draw(img)

        y_text = margin
        for line in lines:
            draw.text((margin, y_text), line, font=font, fill=text_color)
            y_text += line_height

        filename = f"wildcard_preview_{random.randint(0, 1000000)}.png"
        full_path = os.path.join(self.output_dir, filename)
        img.save(full_path)

        return [{"filename": filename, "subfolder": "", "type": "temp"}]


# Node registration for ComfyUI
NODE_CLASS_MAPPINGS = {
    "DuoUmiWildcard": WildcardNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DuoUmiWildcard": "Wildcard Prompt"
}
