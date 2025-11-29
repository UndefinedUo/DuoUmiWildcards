import os
import random
import inspect
import pathlib
import re
import time
import glob
from random import choices
import yaml

import modules.scripts as scripts
import modules.images as images
import gradio as gr

from modules.processing import Processed, process_images
from modules.shared import opts, cmd_opts, state
from modules import scripts, script_callbacks, shared
from modules.styles import StyleDatabase
import modules.textual_inversion.textual_inversion

from modules.sd_samplers import samplers, samplers_for_img2img


ALL_KEY = 'all yaml files'
UsageGuide = """
                    ### Usage
                    * `{a|b|c|...}` will pick one of `a`, `b`, `c`, ...
                    * `{x-y$$a|b|c|...}` will pick between `x` and `y` of `a`, `b`, `c`, ...
                    * `{x$$a|b|c|...}` will pick `x` of `a`, `b`, `c`, ...
                    * `{x-$$a|b|c|...}` will pick atleast `x` of `a`, `b`, `c`, ...
                    * `{-y$$a|b|c|...}` will pick upto `y` of `a`, `b`, `c`, ...
                    * `{x%a|...}` will pick `a` with `x`% chance otherwise one of the rest
                    * `__text__` will pick a random line from the file `text`.txt in the wildcard folder
                    * `<[tag]>` will pick a random item from yaml files in wildcard folder with given `tag`
                    * `<[tag1][tag2]>` will pick a random item from yaml files in wildcard folder with both `tag1` **and** `tag2`
                    * `<[tag1|tag2]>` will pick a random item from yaml files in wildcard folder with `tag1` **or** `tag2`
                    * `<[--tag]>` will pick a random item from yaml files in wildcard folder that does not have the given `tag`
                    * `<file:[tag]>` will pick a random item from yaml file `file`.yaml in wildcard folder with given tag
                    
                    ### Settings override
                    * `@@width=512, height=768@@` will set the width of the image to be `512` and height to be `768`. 
                    * Available settings to override are `cfg_scale, sampler, steps, width, height, denoising_strength`.

                    ### WebUI Prompt Reference
                    * `(text)` emphasizes text by a factor of 1.1
                    * `[text]` deemphasizes text by a factor of 0.9
                    * `(text:x)` (de)emphasizes text by a factor of x
                    * `\(` or `\)` for literal parenthesis in prompt
                    * `[from:to:when]` changes prompt from `from` to `to` after `when` steps if `when` > 1 
                            or after the fraction of `current step/total steps` is bigger than `when`
                    * `[a|b|c|...]` cycles the prompt between the given options each step
                    * `text1 AND text2` creates a prompt that is a mix of the prompts `text1` and `text2`. 
                    """
def get_index(items, item):
    try:
        return items.index(item)
    except Exception:
        return None


def parse_tag(tag):
    """Modified to properly handle seeded tags while maintaining existing functionality"""
    # Remove the standard wildcards markers
    tag = tag.replace("__", "").replace('<', '').replace('>', '').strip()
    
    # If this is a seeded tag, return it as-is
    if tag.startswith('#'):
        return tag
        
    return tag


def read_file_lines(file):
    """
    Read lines from a file and process any range selections.
    
    Args:
        file: File object to read from
        
    Returns:
        list: Selected lines from the file
    """
    f_lines = file.read().splitlines()
    lines = []
    
    for line in f_lines:
        line = line.strip()
        # Skip empty lines
        if not line:
            continue
        # Skip lines that are just comments
        if line.startswith('#'):
            continue
        # For lines with embedded comments, only keep the part before the #
        if '#' in line:
            line = line.split('#')[0].strip()
        lines.append(line)
    
    return lines

def parse_range_string(range_str, num_variants):
    """
    Parse a range string like "1-3" or "2" or "0-2" and return the min and max values.
    
    Args:
        range_str (str): The range string to parse
        num_variants (int): The total number of available variants
        
    Returns:
        tuple: (min_value, max_value)
    """
    if range_str is None:
        return None
    
    parts = range_str.split("-")
    if len(parts) == 1:
        # Single number case
        low = high = min(int(parts[0]), num_variants)
    elif len(parts) == 2:
        # Range case
        low = int(parts[0]) if parts[0] else 0
        high = min(int(parts[1]), num_variants) if parts[1] else num_variants
    else:
        raise Exception(f"Unexpected range {range_str}")
    
    return min(low, high), max(low, high)

def process_wildcard_range(tag, lines):
    """
    Process a wildcard tag that includes a range selection.
    
    Args:
        tag (str): The wildcard tag with range (e.g., "0-2$$Style Maker")
        lines (list): Available lines to choose from
        
    Returns:
        str: Selected items joined with commas
        None: If this is a seeded tag that should be handled elsewhere
    """
    if not lines:
        return ""
    
    # Skip if this is a seeded wildcard
    if tag.startswith('#'):
        return None
        
    # Split the range from the tag
    if "$$" not in tag:
        selected = random.choice(lines)
        # Remove any comments from the selected line
        if '#' in selected:
            selected = selected.split('#')[0].strip()
        return selected
        
    range_str, tag_name = tag.split("$$", 1)
    
    try:
        # Get the range values
        low, high = parse_range_string(range_str, len(lines))
        if low is None or high is None:  # Handle case where parse_range_string returns None
            selected = random.choice(lines)
            # Remove any comments from the selected line
            if '#' in selected:
                selected = selected.split('#')[0].strip()
            return selected
            
        # Select random number of items within range
        num_items = random.randint(low, high)
        if num_items == 0:
            return ""
            
        # Randomly select the specified number of items
        selected = random.sample(lines, num_items)
        # Remove any comments from each selected line
        selected = [line.split('#')[0].strip() if '#' in line else line for line in selected]
        return ", ".join(selected) + ", " if selected else ""
        
    except (ValueError, Exception) as e:
        print(f"Error processing wildcard range: {e}")
        selected = random.choice(lines)
        # Remove any comments from the selected line
        if '#' in selected:
            selected = selected.split('#')[0].strip()
        return selected

# Wildcards
class TagLoader:
    files = []
    wildcard_location = os.path.join(
        pathlib.Path(inspect.getfile(lambda: None)).parent.parent, "wildcards")
    loaded_tags = {}
    missing_tags = set()

    def __init__(self, options):
        self.ignore_paths = dict(options).get('ignore_paths', True)
        self.all_txt_files = glob.glob(os.path.join(self.wildcard_location, '**/*.txt'), recursive=True)
        self.all_yaml_files = glob.glob(os.path.join(self.wildcard_location, '**/*.yaml'), recursive=True)
        self.txt_basename_to_path = {os.path.basename(file).lower().split('.')[0]: file for file in self.all_txt_files}
        self.yaml_basename_to_path = {os.path.basename(file).lower().split('.')[0]: file for file in self.all_yaml_files}
        self.verbose = dict(options).get('verbose', False)
        self.yaml_entries = {}  # Store processed YAML entries

    def process_yaml_entry(self, title, entry_data):
        """Process a single YAML entry with the new structure."""
        processed_entry = {
            'title': title,
            'description': entry_data.get('Description', [None])[0] if isinstance(entry_data.get('Description', []), list) else None,
            'prompts': entry_data.get('Prompts', []),
            'prefixes': entry_data.get('Prefix', []),
            'suffixes': entry_data.get('Suffix', []),
            'tags': [x.lower().strip() for x in entry_data.get('Tags', [])]
        }
        return processed_entry

    def load_tags(self, file_path, verbose=False, cache_files=True):
        """Load tags from a file, supporting both .txt and .yaml formats."""
        if cache_files and self.loaded_tags.get(file_path):
            return self.loaded_tags.get(file_path)

        txt_full_file_path = os.path.join(self.wildcard_location, f'{file_path}.txt')
        yaml_full_file_path = os.path.join(self.wildcard_location, f'{file_path}.yaml')
        txt_file_match = self.txt_basename_to_path.get(file_path.lower()) or txt_full_file_path
        yaml_file_match = self.yaml_basename_to_path.get(file_path.lower()) or yaml_full_file_path
        txt_file_path = txt_file_match if self.ignore_paths else txt_full_file_path
        yaml_file_path = yaml_file_match if self.ignore_paths else yaml_full_file_path

        if file_path == ALL_KEY:
            key = ALL_KEY
        else:
            if self.ignore_paths:
                basename = os.path.basename(file_path.lower())
            key = file_path

        # Handle text files
        if self.wildcard_location and os.path.isfile(txt_file_path):
            with open(txt_file_path, encoding="utf8") as file:
                self.files.append(f"{file_path}.txt")
                self.loaded_tags[key] = read_file_lines(file)
                if self.ignore_paths:
                    self.loaded_tags[basename] = self.loaded_tags[key]

        # Handle YAML files
        if key is ALL_KEY and self.wildcard_location:
            files = glob.glob(os.path.join(self.wildcard_location, '**/*.yaml'), recursive=True)
            output = {}
            for file_path in files:
                with open(file_path, encoding="utf8") as file:
                    self.files.append(f"{file_path}.yaml")
                    try:
                        data = yaml.safe_load(file)
                        if not isinstance(data, dict):
                            if verbose:
                                print(f'Invalid YAML structure in {file_path}')
                            continue

                        for title, entry in data.items():
                            if not isinstance(entry, dict):
                                continue
                            
                            processed_entry = self.process_yaml_entry(title, entry)
                            if processed_entry['tags']:  # Only add if it has tags
                                output[title] = set(processed_entry['tags'])
                                self.yaml_entries[title] = processed_entry

                    except yaml.YAMLError as exc:
                        print(f'Error parsing YAML file {file_path}: {exc}')
            self.loaded_tags[key] = output

        if self.wildcard_location and os.path.isfile(yaml_file_path):
            with open(yaml_file_path, encoding="utf8") as file:
                self.files.append(f"{file_path}.yaml")
                try:
                    data = yaml.safe_load(file)
                    output = {}
                    for title, entry in data.items():
                        if not isinstance(entry, dict):
                            continue
                        
                        processed_entry = self.process_yaml_entry(title, entry)
                        if processed_entry['tags']:  # Only add if it has tags
                            output[title] = set(processed_entry['tags'])
                            self.yaml_entries[title] = processed_entry

                    self.loaded_tags[key] = output
                    if self.ignore_paths:
                        self.loaded_tags[os.path.basename(file_path.lower())] = self.loaded_tags[key]
                except yaml.YAMLError as exc:
                    print(f'Error parsing YAML file {yaml_file_path}: {exc}')

        if not os.path.isfile(yaml_file_path) and not os.path.isfile(txt_file_path):
            self.missing_tags.add(file_path)

        return self.loaded_tags.get(key) if self.loaded_tags.get(key) else []

    def get_entry_details(self, title):
        """Get the full details for a YAML entry by title."""
        return self.yaml_entries.get(title)


# <yaml:[tag]> notation
def parse_tag(tag):
    """Modified to properly handle seeded tags while maintaining existing functionality"""
    # Remove the standard wildcards markers
    tag = tag.replace("__", "").replace('<', '').replace('>', '').strip()
    
    # If this is a seeded tag, return it as-is
    if tag.startswith('#'):
        return tag
        
    return tag

class TagSelector:
    def __init__(self, tag_loader, options):
        self.tag_loader = tag_loader
        self.previously_selected_tags = {}
        self.used_values = {}
        self.selected_options = dict(options).get('selected_options', {})
        self.verbose = dict(options).get('verbose', False)
        self.cache_files = dict(options).get('cache_files', True)
        self.seeded_values = {}
        self.processing_stack = set()
        self.resolved_seeds = {}
        self.selected_entries = {}  # Track selected entries for prefix/suffix handling

    def clear_seeded_values(self):
        """Clear seeded values between generations"""
        self.seeded_values = {}
        self.resolved_seeds = {}
        self.processing_stack.clear()
        self.selected_entries.clear()

    def get_tag_choice(self, parsed_tag, tags):
        """Select a tag from the available choices, handling seeded selection."""
        if not isinstance(tags, list):
            if self.verbose:
                print(f'UmiAI: Expected list of tags but got {type(tags)}')
            return ""

        # Handle pre-selected options first
        if self.selected_options.get(parsed_tag.lower()) is not None:
            selected_index = self.selected_options.get(parsed_tag.lower())
            if 0 <= selected_index < len(tags):
                selected = tags[selected_index]
                # Remove any comments from the selected tag
                if '#' in selected:
                    selected = selected.split('#')[0].strip()
                return selected
            return ""

        # Check if this is a seeded tag with possible multiple seeds
        seed_match = re.match(r'#([0-9|]+)\$\$(.*)', parsed_tag)
        if seed_match:
            # Get all possible seed values
            seed_options = seed_match.group(1).split('|')
            # Randomly select one seed
            chosen_seed = random.choice(seed_options)
            if self.verbose:
                print(f'UmiAI: Selected seed {chosen_seed} from options {seed_options}')
            
            # If we already have a seeded value for this seed, reuse it
            if chosen_seed in self.seeded_values:
                selected = self.seeded_values[chosen_seed]
                if self.verbose:
                    print(f'UmiAI: Reusing seeded value for seed {chosen_seed}: {selected}')
                return self.resolve_wildcard_recursively(selected, chosen_seed)
            
            # Otherwise, select a new value
            if len(tags) == 1:
                selected = tags[0]
            else:
                unused_candidates = [t for t in tags if t not in self.used_values]
                if unused_candidates:
                    selected = random.choice(unused_candidates)
                else:
                    if self.verbose:
                        print(f'UmiAI: All values in tag list were used. Returning random tag.')
                    selected = random.choice(tags)
            
            # Store the selected value for this seed
            self.seeded_values[chosen_seed] = selected
            self.used_values[selected] = True
            
            if self.verbose:
                print(f'UmiAI: Storing new seeded value for seed {chosen_seed}: {selected}')
            
            # Resolve any nested wildcards
            return self.resolve_wildcard_recursively(selected, chosen_seed)

        # Handle standard tag selection
        selected = None
        if len(tags) == 1:
            selected = tags[0]
        else:
            unused_candidates = [t for t in tags if t not in self.used_values]
            if unused_candidates:
                selected = random.choice(unused_candidates)
            else:
                if self.verbose:
                    print(f'UmiAI: All values in tag list were used. Returning random tag.')
                selected = random.choice(tags)

        # When returning the final selected value, check for and remove comments
        if selected:
            self.used_values[selected] = True
            # Store the selected entry for later prefix/suffix handling
            entry_details = self.tag_loader.get_entry_details(selected)
            if entry_details:
                self.selected_entries[parsed_tag] = entry_details
                # If the entry has prompts, use one of those instead of the title
                if entry_details['prompts']:
                    selected = random.choice(entry_details['prompts'])
            
            # Remove any comments from the selected tag
            if isinstance(selected, str) and '#' in selected:
                selected = selected.split('#')[0].strip()

        return selected

    def get_tag_group_choice(self, parsed_tag, groups, tags):
            """Select a tag from a group based on tag criteria"""
            if not isinstance(tags, dict):
                if self.verbose:
                    print(f'UmiAI: Expected dict of tags but got {type(tags)}')
                return ""

            neg_groups = [x.strip().lower() for x in groups if x.startswith('--')]
            neg_groups_set = {x.replace('--', '') for x in neg_groups}
            any_groups = [{y.strip() for y in x.lower().split('|')}
                         for x in groups if '|' in x]
            pos_groups = [x.strip().lower() for x in groups
                         if not x.startswith('--') and '|' not in x]
            pos_groups_set = {x for x in pos_groups}
            
            candidates = []
            for tag, tag_set in tags.items():
                if len(list(pos_groups_set & tag_set)) != len(pos_groups_set):
                    continue
                if len(list(neg_groups_set & tag_set)) > 0:
                    continue
                if len(any_groups) > 0:
                    any_groups_found = 0
                    for any_group in any_groups:
                        if len(list(any_group & tag_set)) == 0:
                            break
                        any_groups_found += 1
                    if len(any_groups) != any_groups_found:
                        continue
                candidates.append(tag)

            if candidates:
                if self.verbose:
                    print(f'UmiAI: Found {len(candidates)} candidates for "{parsed_tag}" with tags: {groups}, first 10: {candidates[:10]}')
                
                # Check if this is a seeded tag
                seed_match = re.match(r'#([0-9|]+)\$\$(.*)', parsed_tag) # Updated regex to match the new seed format
                seed_id = seed_match.group(1) if seed_match else None
                
                selected_title = self.select_value_from_candidates(candidates, seed_id) # This now returns the title
                if selected_title:
                    entry_details = self.tag_loader.get_entry_details(selected_title)
                    if entry_details:
                        self.selected_entries[parsed_tag] = entry_details
                        if entry_details['prompts']:
                            selected_prompt = random.choice(entry_details['prompts'])
                            # Now resolve any nested wildcards within the selected prompt
                            final_value = self.resolve_wildcard_recursively(selected_prompt, seed_id)
                            return final_value
                        # If no prompts, return the title itself, after potential recursive resolution
                        return self.resolve_wildcard_recursively(selected_title, seed_id) # Added recursive resolution for title if no prompts
                    # If no entry_details, just return the title (after potential resolution)
                    return self.resolve_wildcard_recursively(selected_title, seed_id)
                return "" # No candidate selected
                
            if self.verbose:
                print(f'UmiAI: No tag candidates found for: "{parsed_tag}" with tags: {groups}')
            return ""

    def resolve_wildcard_recursively(self, value, seed_id=None):
        """Resolve any nested wildcards in a value, maintaining seed consistency"""
        if value.startswith('__') and value.endswith('__'):
            # This is a nested wildcard, need to resolve it
            nested_tag = value[2:-2]  # Remove the __ markers
            
            # If we have a seed, create a unique seed for this nested wildcard
            nested_seed = f"{seed_id}_{nested_tag}" if seed_id else None
            
            # Prevent infinite recursion
            if nested_tag in self.processing_stack:
                if self.verbose:
                    print(f'UmiAI: Detected recursion loop with tag: {nested_tag}')
                return value
                
            self.processing_stack.add(nested_tag)
            
            # Check if we already resolved this seeded nested wildcard
            if nested_seed and nested_seed in self.resolved_seeds:
                resolved = self.resolved_seeds[nested_seed]
                if self.verbose:
                    print(f'UmiAI: Using cached resolution for {nested_seed}: {resolved}')
            else:
                # Resolve the nested wildcard
                resolved = self.select(nested_tag)
                if nested_seed:
                    self.resolved_seeds[nested_seed] = resolved
                    if self.verbose:
                        print(f'UmiAI: Cached resolution for {nested_seed}: {resolved}')
                        
            self.processing_stack.remove(nested_tag)
            return resolved
            
        return value

    def select_value_from_candidates(self, candidates, seed_id=None):
            """Select a value from the candidates list, handling seeded selection"""
            if seed_id is not None:
                # If we have already selected a value for this seed, return it
                if seed_id in self.seeded_values:
                    value = self.seeded_values[seed_id]
                    if self.verbose:
                        print(f'UmiAI: Reusing seeded value for seed {seed_id}: {value}')
                    return value # Return the cached value directly
                    
            if len(candidates) == 1:
                if self.verbose: 
                    print(f'UmiAI: Only one value {candidates} found. Returning it.')
                selected = candidates[0]
            elif len(candidates) > 1:
                unused_candidates = [c for c in candidates if c not in self.used_values]
                if unused_candidates:
                    selected = random.choice(unused_candidates)
                else:
                    if self.verbose:
                        print(f'UmiAI: All values in {candidates} were used. Returning random tag.')
                    selected = random.choice(candidates)
            else:
                return ""
                
            self.used_values[selected] = True
            
            # Store the selected value if this is a seeded selection
            if seed_id is not None:
                self.seeded_values[seed_id] = selected
                if self.verbose:
                    print(f'UmiAI: Storing new seeded value for seed {seed_id}: {selected}')
                    
            return selected # Return the selected candidate (title)

    def select(self, tag, groups=None):
        """Main selection method that handles all types of wildcards"""
        if self.verbose:
            print(f'UmiAI: Processing tag: {tag}')
                
        self.previously_selected_tags.setdefault(tag, 0)
        if (tag.count(':') == 2) or (len(tag) < 2 and groups):
            return False
                
        if self.previously_selected_tags.get(tag) < 50000:
            self.previously_selected_tags[tag] += 1
            parsed_tag = parse_tag(tag)
                
            # Check if this is a range-based tag (e.g., "0-3$$", "1-3$$")
            if '$$' in parsed_tag:
                range_part, file_part = parsed_tag.split('$$', 1)
                if any(range_part.startswith(str(i)) for i in range(10)) or '-' in range_part:
                    try:
                        tags = self.tag_loader.load_tags(file_part, self.verbose, self.cache_files)
                        if isinstance(tags, list):
                            result = process_wildcard_range(parsed_tag, tags)
                            if result is not None:
                                return result
                    except Exception as e:
                        if self.verbose:
                            print(f'UmiAI: Error processing range wildcard: {e}')
                
            # Then handle seeded tags
            if parsed_tag.startswith('#'):
                tags = self.tag_loader.load_tags(parsed_tag.split('$$')[1], self.verbose, self.cache_files)
                if isinstance(tags, list):
                    return self.get_tag_choice(parsed_tag, tags)
                
            # Regular tag handling
            tags = self.tag_loader.load_tags(parsed_tag, self.verbose, self.cache_files)
            if groups and len(groups) > 0:
                return self.get_tag_group_choice(parsed_tag, groups, tags)
            if len(tags) > 0:
                return self.get_tag_choice(parsed_tag, tags)
            else:
                if self.verbose:
                    print(f'UmiAI: No tags found in wildcard file "{parsed_tag}" or file does not exist')
            return False
                
        if self.previously_selected_tags.get(tag) == 50000:
            self.previously_selected_tags[tag] += 1
            print(f'Processed more than 50000 hits on "{tag}". This probably is a reference loop. Inspect your tags and remove any loops.')
        return False

    def get_prefixes_and_suffixes(self):
        """Get all prefixes and suffixes for selected entries"""
        prefixes = []
        suffixes = []
        negative_prefixes = []
        negative_suffixes = []

        for entry in self.selected_entries.values():
            if entry.get('prefixes'):  # Check if prefixes exist and aren't empty
                for prefix in entry['prefixes']:
                    if prefix:  # Check if prefix isn't None or empty string
                        if '**' in str(prefix):
                            negative_prefixes.append(str(prefix).replace('**', '').strip())
                        else:
                            prefixes.append(str(prefix))
                        
            if entry.get('suffixes'):  # Check if suffixes exist and aren't empty
                for suffix in entry['suffixes']:
                    if suffix:  # Check if suffix isn't None or empty string
                        if '**' in str(suffix):
                            negative_suffixes.append(str(suffix).replace('**', '').strip())
                        else:
                            suffixes.append(str(suffix))

        return {
            'prefixes': prefixes,
            'suffixes': suffixes,
            'negative_prefixes': negative_prefixes,
            'negative_suffixes': negative_suffixes
        }


class TagReplacer:
    def __init__(self, tag_selector, options):
        self.tag_selector = tag_selector
        self.options = options
        # Fixed regex to properly capture the entire wildcard content
        self.wildcard_regex = re.compile(r'(__|<)(.*?)(__|>)')
        self.opts_regexp = re.compile(r'(?<=\[)(.*?)(?=\])')

    def replace_wildcard(self, matches):
        if matches is None or len(matches.groups()) != 3:
            return ""

        # The actual content is in group 2
        match = matches.group(2)
        if not match:
            return ""

        match_and_opts = match.split(':')
        if (len(match_and_opts) == 2):
            selected_tags = self.tag_selector.select(
                match_and_opts[0], self.opts_regexp.findall(match_and_opts[1]))
        else:
            global_opts = self.opts_regexp.findall(match)
            if len(global_opts) > 0:
                selected_tags = self.tag_selector.select(ALL_KEY, global_opts)
            else:
                selected_tags = self.tag_selector.select(match)

        if selected_tags:
            # Remove any comments from the selected tags before returning them
            # This prevents # from commenting out the rest of the prompt
            if isinstance(selected_tags, str) and '#' in selected_tags:
                selected_tags = selected_tags.split('#')[0].strip()
            return selected_tags
        return matches.group(0)

    def replace_wildcard_recursive(self, prompt):
        p = self.wildcard_regex.sub(self.replace_wildcard, prompt)
        # Keep replacing wildcards until no more changes occur
        count = 0
        max_iterations = 10  # Add a safety limit to prevent infinite loops
        while p != prompt and count < max_iterations:
            prompt = p
            p = self.wildcard_regex.sub(self.replace_wildcard, prompt)
            count += 1
        return p
        
    def replace(self, prompt):
        return self.replace_wildcard_recursive(prompt)


# handle {1$$this | that} notation
class DynamicPromptReplacer:
    def __init__(self):
        self.re_combinations = re.compile(r"\{([^{}]*)\}")

    def get_variant_weight(self, variant):
        split_variant = variant.split("%")
        if len(split_variant) == 2:
            num = split_variant[0]
            try:
                return int(num)
            except ValueError:
                print(f'{num} is not a number')
        return 0

    def get_variant(self, variant):
        split_variant = variant.split("%")
        if len(split_variant) == 2:
            return split_variant[1]
        return variant

    def parse_range(self, range_str, num_variants):
        """
        Parse a range string that may include wildcard markers.
        Handles formats like "__x-y__" or "x-y" or just "x"
        """
        if range_str is None:
            return None
            
        # Strip wildcard markers if present
        cleaned_range = range_str.replace("__", "")
        
        parts = cleaned_range.split("-")
        try:
            if len(parts) == 1:
                # Single number case
                low = high = min(int(parts[0]), num_variants)
            elif len(parts) == 2:
                # Range case
                low = int(parts[0]) if parts[0] else 0
                high = min(int(parts[1]), num_variants) if parts[1] else num_variants
            else:
                raise Exception(f"Unexpected range {range_str}")
                
            return min(low, high), max(low, high)
            
        except ValueError as e:
            print(f"Error parsing range '{range_str}': {e}")
            return 0, num_variants  # Default to full range on error

    def replace_combinations(self, match):
        if match is None or len(match.groups()) == 0:
            return ""

        combinations_str = match.groups()[0]
        
        variants = [s.strip() for s in combinations_str.split("|")]
        weights = [self.get_variant_weight(var) for var in variants]
        variants = [self.get_variant(var) for var in variants]

        splits = variants[0].split("$$")
        is_range_based = len(splits) > 1
        quantity = splits.pop(0) if is_range_based else str(1)
        variants[0] = splits[0] if splits else variants[0]

        low_range, high_range = self.parse_range(quantity, len(variants))
        
        # If quantity is 0, return empty string with no spaces
        if quantity == 0:
            return ""

        summed = sum(weights)
        zero_weights = weights.count(0)
        weights = list(
            map(lambda x: (100 - summed) / zero_weights
                if x == 0 else x, weights))

        try:
            picked = []
            for x in range(low_range):  # Always pick minimum number
                if not variants:  # Check if we've used all variants
                    break
                choice = random.choices(variants, weights)[0]
                if choice.strip():  # Only add non-empty choices
                    picked.append(choice)
                
                index = variants.index(choice)
                variants.pop(index)
                weights.pop(index)
                
            # Randomly pick additional items up to high_range
            additional = random.randint(0, high_range - low_range)
            for x in range(additional):
                if not variants:  # Check if we've used all variants
                    break
                choice = random.choices(variants, weights)[0]
                if choice.strip():  # Only add non-empty choices
                    picked.append(choice)
                
                index = variants.index(choice)
                variants.pop(index)
                weights.pop(index)

            # For range-based replacements or multiple selections, use comma formatting
            if is_range_based or (low_range > 1 or high_range > 1):
                return ", ".join(picked) + (", " if picked else "")
            else:
                # For simple single-item replacements, don't add a trailing comma
                # But if it's just one item selected from multiple options, add a space
                # to maintain proper spacing in the prompt
                return "".join(picked) if len(picked) == 1 else ", ".join(picked) + (", " if picked else "")
            
        except ValueError as e:
            print(f"Error picking variants: {e}")
            return ""

    def replace(self, template):
        if template is None:
            return None

        result = self.re_combinations.sub(self.replace_combinations, template)
        
        # Clean up any potential double commas or spaces that might occur
        result = re.sub(r',\s*,', ',', result)  # Remove double commas
        result = re.sub(r'\s+', ' ', result)    # Remove double spaces
        
        # Only ensure a trailing comma for range-based replacements
        # We might need a more complex approach here if problematic
        
        return result

class PromptGenerator:
    def __init__(self, options):
        self.tag_loader = TagLoader(options)
        self.tag_selector = TagSelector(self.tag_loader, options)
        self.negative_tag_generator = NegativePromptGenerator()
        self.settings_generator = SettingsGenerator()
        self.replacers = [
            TagReplacer(self.tag_selector, options),
            DynamicPromptReplacer(),
            self.settings_generator
        ]
        self.verbose = dict(options).get('verbose', False)

    def use_replacers(self, prompt):
        """Apply all replacers to the prompt in sequence"""
        for replacer in self.replacers:
            prompt = replacer.replace(prompt)
        return prompt

    def generate_single_prompt(self, original_prompt):
        """Generate a single prompt with all wildcards replaced and additions applied"""
        # Clear seeded values before generating new prompt
        self.tag_selector.clear_seeded_values()
        
        # Generate the main prompt
        previous_prompt = original_prompt
        start = time.time()
        prompt = self.use_replacers(original_prompt)
        
        # Keep replacing until no more changes occur
        while previous_prompt != prompt:
            previous_prompt = prompt
            prompt = self.use_replacers(prompt)
            
        # Get prefixes and suffixes
        additions = self.tag_selector.get_prefixes_and_suffixes()
        
        # Add prefixes and suffixes to the prompt
        if additions['prefixes']:
            prompt = ", ".join(additions['prefixes']) + ", " + prompt
        if additions['suffixes']:
            prompt = prompt + ", " + ", ".join(additions['suffixes'])
            
        # Handle negative prefixes and suffixes
        if additions['negative_prefixes'] or additions['negative_suffixes']:
            negative_parts = []
            if additions['negative_prefixes']:
                negative_parts.extend(additions['negative_prefixes'])
            if additions['negative_suffixes']:
                negative_parts.extend(additions['negative_suffixes'])
            self.negative_tag_generator.add_negative_tags(negative_parts)
            
        # Process any remaining negative tags in the prompt
        prompt = self.negative_tag_generator.replace(prompt)
        
        # Clean up extra commas from the prompt
        prompt = re.sub(r',\s*,', ',', prompt)  # Remove double commas
        prompt = re.sub(r',\s*$', '', prompt)   # Remove trailing commas
        prompt = re.sub(r'^\s*,\s*', '', prompt) # Remove leading commas
        prompt = re.sub(r'\s+', ' ', prompt)    # Normalize whitespace
        
        end = time.time()
        if self.verbose:
            print(f"Prompt generated in {end - start} seconds")

        return prompt

    def get_negative_tags(self):
        """Get all collected negative tags"""
        return self.negative_tag_generator.get_negative_tags()

    def get_setting_overrides(self):
        """Get any settings overrides that were found"""
        return self.settings_generator.get_setting_overrides()


class NegativePromptGenerator:
    def __init__(self):
        self.negative_tag = set()
        self.negative_prefixes = []
        self.negative_suffixes = []

    def strip_negative_tags(self, tags):
        # Original negative tag handling
        matches = re.findall('\*\*.*?\*\*', tags)
        if matches:
            for match in matches:
                self.negative_tag.add(match.replace("**", ""))
                tags = tags.replace(match, "")
        return tags

    def add_negative_tags(self, tags):
        """Add additional negative tags from prefixes/suffixes"""
        if isinstance(tags, list):
            for tag in tags:
                self.negative_tag.add(tag.strip())
        else:
            self.negative_tag.add(tags.strip())

    def replace(self, prompt):
        return self.strip_negative_tags(prompt)

    def get_negative_tags(self):
        """Modified to handle ordered negative prompts and clean up empty entries"""
        all_negatives = []
        
        # Add any negative prefixes first
        if self.negative_prefixes:
            all_negatives.extend([p for p in self.negative_prefixes if p.strip()])
        
        # Add regular negative tags
        if self.negative_tag:
            all_negatives.extend([t for t in self.negative_tag if t.strip()])
            
        # Add any negative suffixes last
        if self.negative_suffixes:
            all_negatives.extend([s for s in self.negative_suffixes if s.strip()])
            
        # Join with commas and clean up any potential issues
        result = ", ".join(all_negatives)
        result = re.sub(r',\s*,', ',', result)  # Remove double commas
        result = re.sub(r',\s*$', '', result)   # Remove trailing commas
        result = re.sub(r'^\s*,\s*', '', result) # Remove leading commas
        
        return result


# @@settings@@ notation
class SettingsGenerator:

    def __init__(self):
        self.re_setting_tags = re.compile(r"@@(.*?)@@")
        self.setting_overrides = {}
        self.type_mapping = {
            'cfg_scale': float,
            'sampler': str,
            'steps': int,
            'width': int,
            'height': int,
            'denoising_strength': float
        }

    def strip_setting_tags(self, prompt):
        matches = self.re_setting_tags.findall(prompt)
        if matches:
            for match in matches:
                sep = "," if "," in match else "|"
                for assignment in [m.strip() for m in match.split(sep)]:
                    key_raw, value = assignment.split("=")
                    if not value:
                        print(
                            f"Invalid setting {assignment}, settings should assign a value"
                        )
                        continue
                    key_found = False
                    for key in self.type_mapping.keys():
                        if key.startswith(key_raw):
                            self.setting_overrides[key] = self.type_mapping[
                                key](value)
                            key_found = True
                            break
                    if not key_found:
                        print(
                            f"Unknown setting {key_raw}, setting should be the starting part of: {', '.join(self.type_mapping.keys())}"
                        )
                prompt = prompt.replace('@@' + match + '@@', "")
        return prompt

    def replace(self, prompt):
        return self.strip_setting_tags(prompt)

    def get_setting_overrides(self):
        return self.setting_overrides

def _get_effective_prompt(prompts: list[str], prompt: str) -> str:
    return prompts[0] if prompts else prompt

class Script(scripts.Script):
    is_txt2img = False

    def title(self):
        return "Prompt generator"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        self.is_txt2img = is_img2img == False
        elemid_prefix = "img2img-umiai-" if is_img2img else "txt2img-umiai-"
        with gr.Accordion('UmiAI', 
                          open=True, 
                          elem_id=elemid_prefix + "accordion"):
            with gr.Row():
                enabled = gr.Checkbox(label="Enable UmiAI", 
                                      value=True, 
                                      elem_id=elemid_prefix + "toggle")
            with gr.Tab("Settings"):       
                with gr.Row(elem_id=elemid_prefix + "seeds"):
                    shared_seed = gr.Checkbox(label="Static wildcards", 
                                              value=False, 
                                              elem_id=elemid_prefix + "static-wildcards", 
                                              tooltip="Always picks the same random/wildcard options when using a static seed.")
                    same_seed = gr.Checkbox(label='Same prompt in batch', 
                                            value=False, 
                                            elem_id=elemid_prefix + "same-seed", 
                                            tooltip="Same prompt will be used for all generated images in a batch.")
                with gr.Row(elem_id=elemid_prefix + "lesser"):                
                    cache_files = gr.Checkbox(label="Cache tag files", 
                                              value=True, 
                                              elem_id=elemid_prefix + "cache-files", 
                                              tooltip="Cache .txt and .yaml files at runtime. Speeds up prompt generation. Disable if you're editing wildcard files to see changes instantly.")
                    verbose = gr.Checkbox(label="Verbose logging", 
                                          value=False, 
                                          elem_id=elemid_prefix + "verbose",
                                          tooltip="Displays UmiAI log messages. Useful when prompt crafting, or debugging file-path errors.")
                    negative_prompt = gr.Checkbox(label='**negative keywords**', 
                                                  value=True,
                                                  elem_id=elemid_prefix + "negative-keywords", 
                                                  tooltip="Collect and add **negative keywords** from wildcards to Negative Prompts.")
                    ignore_folders = gr.Checkbox(label="Ignore folders", 
                                                 value=False,
                                                 elem_id=elemid_prefix + "ignore-folders",
                                                 tooltip="Ignore folder structure, will choose first file found if duplicate file names exist.")
                                            
            with gr.Tab("Usage"):
                gr.Markdown(UsageGuide)

        return [enabled, verbose, cache_files, ignore_folders, same_seed, negative_prompt, shared_seed,
                ]

    def process(self, p, enabled, verbose, cache_files, ignore_folders, same_seed, negative_prompt,
                shared_seed, *args):
        if not enabled:
            return

        debug = False

        if debug: print(f'\nModel: {p.sampler_name}, Seed: {int(p.seed)}, Batch Count: {p.n_iter}, Batch Size: {p.batch_size}, CFG: {p.cfg_scale}, Steps: {p.steps}\nOriginal Prompt: "{p.prompt}"\nOriginal Negatives: "{p.negative_prompt}"\n')
        
        original_prompt = _get_effective_prompt(p.all_prompts, p.prompt)
        original_negative_prompt = _get_effective_prompt(
            p.all_negative_prompts,
            p.negative_prompt,
        )

        hr_fix_enabled = getattr(p, "enable_hr", False)

        TagLoader.files.clear()

        options = {
            'verbose': verbose,
            'cache_files': cache_files,
            'ignore_folders': ignore_folders,
        }
        prompt_generator = PromptGenerator(options)

        for cur_count in range(p.n_iter):  #Batch count
            for cur_batch in range(p.batch_size):  #Batch Size

                index = p.batch_size * cur_count + cur_batch

                # pick same wildcard for a given seed
                if (shared_seed):
                    random.seed(p.all_seeds[p.batch_size *cur_count if same_seed else index])
                else:
                    random.seed(time.time()+index*10)
                
                if debug: print(f'{"Batch #"+str(cur_count) if same_seed else "Prompt #"+str(index):=^30}')

                prompt_generator.negative_tag_generator.negative_tag = set()

                prompt = prompt_generator.generate_single_prompt(original_prompt)
                
                # Clean up any extra commas or whitespace in the final prompt
                prompt = re.sub(r',\s*,', ',', prompt)  # Remove double commas
                prompt = re.sub(r',\s*$', '', prompt)   # Remove trailing commas
                prompt = re.sub(r'^\s*,\s*', '', prompt) # Remove leading commas
                prompt = re.sub(r'\s+', ' ', prompt)    # Normalize whitespace
                
                p.all_prompts[index] = prompt
                if hr_fix_enabled:
                    p.all_hr_prompts[index] = prompt

                if debug: print(f'Prompt: "{prompt}"')

                negative = original_negative_prompt
                if negative_prompt and hasattr(p, "all_negative_prompts"): # hasattr to fix crash on old webui versions
                    neg_tags = prompt_generator.get_negative_tags()
                    if neg_tags.strip():  # Only add if there are actual negative tags
                        negative += (", " if negative.strip() else "") + neg_tags
                    
                    # Clean up any extra commas or whitespace in the final negative prompt
                    negative = re.sub(r',\s*,', ',', negative)  # Remove double commas
                    negative = re.sub(r',\s*$', '', negative)   # Remove trailing commas
                    negative = re.sub(r'^\s*,\s*', '', negative) # Remove leading commas
                    negative = re.sub(r'\s+', ' ', negative)    # Normalize whitespace
                    
                    p.all_negative_prompts[index] = negative
                    if hr_fix_enabled:
                        p.all_hr_negative_prompts[index] = negative
                    if debug: print(f'Negative: "{negative}\n"')

                # same prompt per batch
                if (same_seed):
                    for index, i in enumerate(p.all_prompts):
                        p.all_prompts[index] = prompt
                    break

        def find_sampler_index(sampler_list, value):
            for index, elem in enumerate(sampler_list):
                if elem[0] == value or value in elem[2]:
                    return index

        att_override = prompt_generator.get_setting_overrides()
        #print(att_override)
        for att in att_override.keys():
            if not att.startswith("__"):
                if att == 'sampler':
                    sampler_name = att_override[att]
                    if self.is_txt2img:
                        sampler_index = find_sampler_index(
                            samplers, sampler_name)
                    else:
                        sampler_index = find_sampler_index(
                            samplers_for_img2img, sampler_name)
                    if (sampler_index != None):
                        setattr(p, 'sampler_index', sampler_index)
                    else:
                        print(
                            f"Sampler {sampler_name} not found in prompt {p.all_prompts[0]}"
                        )
                    continue
                setattr(p, att, att_override[att])

        if original_prompt != p.all_prompts[0]:
            p.extra_generation_params["Wildcard prompt"] = original_prompt
            if verbose:
                p.extra_generation_params["File includes"] = "|".join(
                    TagLoader.files)

from modules import sd_hijack
path = os.path.join(scripts.basedir(), "embeddings")
try:
    sd_hijack.model_hijack.embedding_db.add_embedding_dir(path)
except:
    print("UmiAI: Failed to load embeddings. Your a1111 installation is ancient. Update it.")
    pass