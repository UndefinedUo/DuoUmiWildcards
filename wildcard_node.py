"""
DuoUmiWild - ComfyUI Wildcard Node
A custom node for ComfyUI that feeds random lines from .txt wildcard files into prompts.
"""

import os
import random
import re
import glob
import yaml
import torch
import folder_paths


class WildcardNode:
    """
    A ComfyUI node that randomly selects lines from .txt and .yaml files.
    Supports wildcards, nested folders, recursive wildcards, and YAML tag-based selection.
    """

    def __init__(self):
        self.wildcard_dir = os.path.join(os.path.dirname(__file__), "wildcards")
        # Create wildcards directory if it doesn't exist
        if not os.path.exists(self.wildcard_dir):
            os.makedirs(self.wildcard_dir)

        # Cache for loaded wildcard files
        self.loaded_tags = {}
        self.all_txt_files = {}
        self.all_yaml_files = {}
        self.yaml_entries = {}  # Store parsed YAML entries
        self.yaml_tags_to_entries = {}  # Map tags to entry titles
        self.refresh_file_cache()

        # Track prefixes and suffixes to add
        self.current_prefixes = []
        self.current_suffixes = []

    def refresh_file_cache(self):
        """Build a cache of all .txt and .yaml files for quick lookup, supporting nested folders."""
        self.all_txt_files = glob.glob(os.path.join(self.wildcard_dir, '**/*.txt'), recursive=True)
        self.all_yaml_files = glob.glob(os.path.join(self.wildcard_dir, '**/*.yaml'), recursive=True)

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

        # Load all YAML files
        self.load_all_yaml_files()

    def load_all_yaml_files(self):
        """Load and parse all YAML files, building tag-to-entry mappings."""
        self.yaml_entries = {}
        self.yaml_tags_to_entries = {}

        for yaml_file in self.all_yaml_files:
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    if not isinstance(data, dict):
                        print(f"DuoUmiWild: Invalid YAML structure in {yaml_file}")
                        continue

                    for title, entry in data.items():
                        if not isinstance(entry, dict):
                            continue

                        # Process the entry
                        processed_entry = {
                            'title': title,
                            'prompts': entry.get('Prompts', []),
                            'prefixes': entry.get('Prefix', []),
                            'suffixes': entry.get('Suffix', []),
                            'tags': [tag.lower().strip() for tag in entry.get('Tags', [])]
                        }

                        self.yaml_entries[title] = processed_entry

                        # Build tag to entries mapping
                        for tag in processed_entry['tags']:
                            if tag not in self.yaml_tags_to_entries:
                                self.yaml_tags_to_entries[tag] = []
                            self.yaml_tags_to_entries[tag].append(title)

            except Exception as e:
                print(f"DuoUmiWild: Error loading YAML file {yaml_file}: {e}")

    def select_by_tags(self, tags_query):
        """
        Select a YAML entry based on tag query.
        Supports: <[Tag]>, <[Tag1][Tag2]> (AND), <[Tag1|Tag2]> (OR)

        Args:
            tags_query: The tag query string

        Returns:
            str: Selected prompt text, or empty string if not found
        """
        # Parse tags from the query
        # Extract individual tags and operators
        tag_pattern = re.compile(r'\[([^\]]+)\]')
        tags = tag_pattern.findall(tags_query)

        if not tags:
            return ""

        candidates = set()
        first_tag = True

        for tag_expr in tags:
            tag_expr_lower = tag_expr.lower().strip()

            # Check for OR operation (|)
            if '|' in tag_expr:
                or_tags = [t.strip() for t in tag_expr_lower.split('|')]
                or_candidates = set()
                for or_tag in or_tags:
                    if or_tag in self.yaml_tags_to_entries:
                        or_candidates.update(self.yaml_tags_to_entries[or_tag])

                if first_tag:
                    candidates = or_candidates
                else:
                    candidates &= or_candidates
            else:
                # Single tag
                if tag_expr_lower in self.yaml_tags_to_entries:
                    tag_candidates = set(self.yaml_tags_to_entries[tag_expr_lower])
                    if first_tag:
                        candidates = tag_candidates
                    else:
                        candidates &= tag_candidates
                elif first_tag:
                    return ""  # No match found

            first_tag = False

        if not candidates:
            return ""

        # Select a random candidate
        selected_title = random.choice(list(candidates))
        entry = self.yaml_entries[selected_title]

        # Decide whether to use prompt, prefix, or suffix
        available_options = []
        if entry['prompts']:
            available_options.append('prompt')
        if entry['prefixes']:
            available_options.append('prefix')
        if entry['suffixes']:
            available_options.append('suffix')

        if not available_options:
            return ""

        choice_type = random.choice(available_options)

        if choice_type == 'prompt':
            return random.choice(entry['prompts'])
        elif choice_type == 'prefix':
            prefix = random.choice(entry['prefixes'])
            if prefix:  # Don't add empty prefixes
                self.current_prefixes.append(prefix)
            return ""  # Prefix doesn't go in-place
        elif choice_type == 'suffix':
            suffix = random.choice(entry['suffixes'])
            if suffix:  # Don't add empty suffixes
                self.current_suffixes.append(suffix)
            return ""  # Suffix doesn't go in-place

        return ""

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

    def process_curly_braces(self, match):
        """
        Process {} randomization like {option1|option2|option3}
        Supports range syntax like {0-1$$option1|option2}

        Args:
            match: Regex match object

        Returns:
            str: Selected option(s)
        """
        content = match.group(1)
        options = [opt.strip() for opt in content.split('|')]

        if not options:
            return ""

        # Check for range syntax
        if '$$' in options[0]:
            range_part, first_option = options[0].split('$$', 1)
            options[0] = first_option.strip()

            try:
                if '-' in range_part:
                    parts = range_part.split('-')
                    low = int(parts[0]) if parts[0] else 0
                    high = int(parts[1]) if parts[1] else len(options)
                else:
                    low = high = int(range_part)

                # Clamp to valid range
                low = max(0, min(low, len(options)))
                high = max(0, min(high, len(options)))

                if low > high:
                    low, high = high, low

                num_items = random.randint(low, high)
                if num_items == 0:
                    return ""

                selected = random.sample(options, min(num_items, len(options)))
                return ", ".join(selected)
            except (ValueError, Exception) as e:
                print(f"DuoUmiWild: Error processing range in curly braces: {e}")
                return random.choice(options)
        else:
            # Simple random choice
            return random.choice(options)

    def process_yaml_tags(self, match):
        """
        Process YAML tag selection like <[Tag]> or <[Tag1][Tag2]>

        Args:
            match: Regex match object

        Returns:
            str: Selected YAML entry prompt
        """
        tags_query = match.group(0)  # Get the full match
        return self.select_by_tags(tags_query)

    def select_yaml_by_title(self, title):
        """
        Select a YAML entry directly by its title (e.g., "a-size", "b-size").

        Args:
            title: The entry title to look up

        Returns:
            str: Selected prompt text, or empty string if not found
        """
        if title not in self.yaml_entries:
            return ""

        entry = self.yaml_entries[title]

        # Decide whether to use prompt, prefix, or suffix
        available_options = []
        if entry['prompts']:
            available_options.append('prompt')
        if entry['prefixes'] and entry['prefixes'] != ['']:
            available_options.append('prefix')
        if entry['suffixes'] and entry['suffixes'] != ['']:
            available_options.append('suffix')

        if not available_options:
            return ""

        choice_type = random.choice(available_options)

        if choice_type == 'prompt':
            return random.choice(entry['prompts'])
        elif choice_type == 'prefix':
            prefix = random.choice(entry['prefixes'])
            if prefix:
                self.current_prefixes.append(prefix)
            return ""
        elif choice_type == 'suffix':
            suffix = random.choice(entry['suffixes'])
            if suffix:
                self.current_suffixes.append(suffix)
            return ""

        return ""

    def process_wildcards(self, text, seed, autorefresh):
        """
        Process all wildcards, YAML tags, and {} randomization with recursive support.

        Args:
            text: Input text containing wildcards, YAML tags, and {} randomization
            seed: Random seed for reproducible results
            autorefresh: Whether to refresh file cache and reload files each time

        Returns:
            dict: Contains UI preview and result tuple
        """
        # Set random seed for reproducibility
        random.seed(seed)

        # Clear prefix/suffix tracking
        self.current_prefixes = []
        self.current_suffixes = []

        # Refresh file cache if autorefresh is enabled
        cache_files = (autorefresh == "No")
        if autorefresh == "Yes":
            self.refresh_file_cache()
            self.loaded_tags.clear()

        # Patterns
        wildcard_pattern = re.compile(r'__([^_]+(?:_[^_]+)*)__')  # __filename__
        yaml_tag_pattern = re.compile(r'<\[([^\]]+(?:\]\[)?[^\]]*)\]>')  # <[Tag]> or <[Tag1][Tag2]>
        curly_brace_pattern = re.compile(r'\{([^{}]+)\}')  # {option1|option2}

        # Process multiple times to handle nested structures
        max_iterations = 20
        iteration = 0
        previous_text = None

        while previous_text != text and iteration < max_iterations:
            previous_text = text

            # Process in order: wildcards, YAML tags, then {} randomization
            text = wildcard_pattern.sub(lambda m: self.process_range_wildcard(m, cache_files), text)
            text = yaml_tag_pattern.sub(self.process_yaml_tags, text)
            text = curly_brace_pattern.sub(self.process_curly_braces, text)

            # Also check for direct YAML title references (like "a-size" from {a|b|c}-size)
            for title in self.yaml_entries.keys():
                if title in text:
                    replacement = self.select_yaml_by_title(title)
                    text = text.replace(title, replacement, 1)  # Replace only first occurrence

            iteration += 1

        # Add prefixes and suffixes
        if self.current_prefixes:
            text = ", ".join(self.current_prefixes) + ", " + text
        if self.current_suffixes:
            text = text + ", " + ", ".join(self.current_suffixes)

        # Clean up any extra commas or whitespace
        text = re.sub(r',\s*,', ',', text)  # Remove double commas
        text = re.sub(r',\s*$', '', text)   # Remove trailing commas
        text = re.sub(r'^\s*,\s*', '', text)  # Remove leading commas
        text = re.sub(r'\s+', ' ', text)     # Normalize whitespace
        text = text.strip()

        # Return with UI text display
        return {"ui": {"text": [text]}, "result": (text,)}


# Node registration for ComfyUI
NODE_CLASS_MAPPINGS = {
    "DuoUmiWildcard": WildcardNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DuoUmiWildcard": "Wildcard Prompt"
}
