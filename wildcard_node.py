"""
DuoUmiWild - ComfyUI Wildcard Node
A custom node for ComfyUI that feeds random lines from .txt wildcard files into prompts.
"""

import os
import random
import re


class WildcardNode:
    """
    A ComfyUI node that randomly selects lines from .txt files in the wildcards directory.
    Supports multiple wildcards in a single prompt using __filename__ syntax.
    """

    def __init__(self):
        self.wildcard_dir = os.path.join(os.path.dirname(__file__), "wildcards")
        # Create wildcards directory if it doesn't exist
        if not os.path.exists(self.wildcard_dir):
            os.makedirs(self.wildcard_dir)

    @classmethod
    def INPUT_TYPES(cls):
        """
        Define the input parameters for the node.
        """
        return {
            "required": {
                "text": ("STRING", {
                    "multiline": True,
                    "default": "a photo of __subject__, __style__"
                }),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff,
                    "tooltip": "Seed for random selection. Use the same seed for consistent results."
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("processed_text",)
    FUNCTION = "process_wildcards"
    CATEGORY = "DuoUmiWild"

    def read_wildcard_file(self, filename):
        """
        Read a wildcard file and return valid lines.

        Args:
            filename: Name of the file (without .txt extension)

        Returns:
            list: Lines from the file, or empty list if file not found
        """
        filepath = os.path.join(self.wildcard_dir, f"{filename}.txt")

        if not os.path.exists(filepath):
            print(f"DuoUmiWild: Wildcard file not found: {filepath}")
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
                return lines
        except Exception as e:
            print(f"DuoUmiWild: Error reading file {filepath}: {e}")
            return []

    def process_range_wildcard(self, match):
        """
        Process wildcard with range syntax like __0-2$$filename__

        Args:
            match: Regex match object containing the wildcard

        Returns:
            str: Selected items joined with commas, or original if error
        """
        content = match.group(1)

        # Check for range syntax: num-num$$filename or num$$filename
        if '$$' in content:
            range_part, filename = content.split('$$', 1)
            lines = self.read_wildcard_file(filename)

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
            # Simple wildcard without range
            lines = self.read_wildcard_file(content)
            if lines:
                return random.choice(lines)
            else:
                return match.group(0)  # Return original if no lines found

    def process_wildcards(self, text, seed):
        """
        Process all wildcards in the input text.

        Args:
            text: Input text containing wildcards in __filename__ format
            seed: Random seed for reproducible results

        Returns:
            tuple: Processed text with wildcards replaced
        """
        # Set random seed for reproducibility
        random.seed(seed)

        # Pattern to match __content__ wildcards
        wildcard_pattern = re.compile(r'__([^_]+(?:_[^_]+)*)__')

        # Process wildcards multiple times to handle nested wildcards
        max_iterations = 10
        iteration = 0
        previous_text = None

        while previous_text != text and iteration < max_iterations:
            previous_text = text
            text = wildcard_pattern.sub(self.process_range_wildcard, text)
            iteration += 1

        # Clean up any extra commas or whitespace
        text = re.sub(r',\s*,', ',', text)  # Remove double commas
        text = re.sub(r',\s*$', '', text)   # Remove trailing commas
        text = re.sub(r'^\s*,\s*', '', text)  # Remove leading commas
        text = re.sub(r'\s+', ' ', text)     # Normalize whitespace
        text = text.strip()

        return (text,)


# Node registration for ComfyUI
NODE_CLASS_MAPPINGS = {
    "DuoUmiWildcard": WildcardNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DuoUmiWildcard": "Wildcard Prompt"
}
