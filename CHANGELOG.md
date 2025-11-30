# Changelog

## v3.1 - UI Improvements & Ratio Selector

### Changes

#### Text Output Enhancement
- **Changed**: Text preview now displays as copyable string instead of image
- Removed PIL/Pillow dependency for preview generation
- Text appears in UI as selectable/copyable output
- More lightweight and user-friendly

#### New Node: Latent Ratio Selector
- Create empty latent images with predefined aspect ratios
- **17 preset ratios** including portrait, landscape, square, and cinematic
- **Randomization feature** with category filtering:
  - Randomize from All ratios
  - Randomize from Portrait Only
  - Randomize from Landscape Only
  - Randomize from Square Only
- **Seeded randomization** for reproducible results
- Outputs: latent, ratio description, width, and height

#### Supported Ratios
- Portrait: 2:3, 3:4, 4:5, 9:16
- Square: 1:1
- Landscape: 4:3, 16:9, 21:9, 3:2
- Cinematic: 1.43:1 (IMAX), 1.66:1 (European), 1.85:1, 2.35:1 (Cinemascope), 2.39:1 (Anamorphic)
- Special: 1.618:1 (Golden Ratio)

#### File Cleanup & Conversion
- **Converted**: `corn-flakes-sex-pose.yaml` → `sex-poses-converted.yaml`
- Removed all "cof" references from file
- Converted from nested wildcard format to Prompts/Tags/Prefix/Suffix structure
- **50+ pose entries** organized by tags
- Added comprehensive tag system for easy selection
- Created `SEX_POSES_README.md` with usage guide
- Now fully compatible with `<[Tag]>` selection system

### Technical Changes
- Removed unused imports: `PIL`, `numpy`, `textwrap`
- Removed `generate_preview()` method
- Removed `output_dir` initialization
- Created new `ratio_selector.py` module
- Updated `__init__.py` to register both nodes

---

## v3.0 - YAML Support & Advanced Features

### Major New Features

#### 1. YAML Wildcard Support
- Load and parse `.yaml` files from wildcards directory
- Tag-based entry selection using `<[Tag]>` syntax
- Support for AND logic: `<[Tag1][Tag2]>` (entries with both tags)
- Support for OR logic: `<[Tag1|Tag2]>` (entries with either tag)
- Complex tag combinations possible

#### 2. YAML Prefix/Suffix Injection
- YAML entries can specify Prefix and Suffix options
- Randomly chooses between using Prompt, Prefix, or Suffix
- Prefixes are automatically added to the start of the final prompt
- Suffixes are automatically added to the end of the final prompt
- Perfect for adding context without cluttering inline prompts

#### 3. Curly Brace Randomization `{}`
- Use `{option1|option2|option3}` for random selection
- Range support: `{2$$a|b|c}` selects exactly 2 options
- Range support: `{1-3$$options}` selects 1 to 3 options
- Perfect for inline variations and combinations

#### 4. Direct YAML Title References
- YAML entries can be referenced by exact title
- Example: `{a|b|c}-size` randomly creates "b-size", which matches YAML entry "b-size"
- Enables powerful letter-based selection patterns
- Works seamlessly with curly brace randomization

#### 5. Combined Syntax Support
- Mix `__wildcards__`, `<[YAML tags]>`, and `{random}` in one prompt
- All syntax types work together recursively
- Example: `girl, {a|b|c}-size, <[Pose]>, __lighting__`
- Processes in order: wildcards → YAML tags → curly braces → YAML titles

### Example YAML Files Added
- `wildcards/Poses.yaml` - Comprehensive pose library with tags
- `wildcards/example_yaml.yaml` - Simple demonstration examples
- `wildcards/breast_sizes.yaml` - Single-letter size references (a-size, b-size, etc.)

### Documentation
- Added `YAML_GUIDE.md` - Complete YAML feature documentation
- Updated `README.md` with YAML examples and feature list
- Updated `EXAMPLES.md` with YAML usage examples

### Technical Changes
- Added `yaml` import for YAML file parsing
- Implemented `load_all_yaml_files()` method
- Implemented `select_by_tags()` for tag-based selection
- Implemented `select_yaml_by_title()` for direct title lookup
- Implemented `process_curly_braces()` for `{}` randomization
- Implemented `process_yaml_tags()` for `<[tag]>` processing
- Added prefix/suffix tracking and injection
- Updated main processing loop to handle all syntax types

---

## v2.0 - Enhanced Features

### New Features

#### 1. Text Preview Display
- The node now displays the processed text directly in the UI
- Visual preview appears as an image card showing the final processed prompt
- Easier to verify wildcard expansions without needing to check outputs

#### 2. Nested Folder Support
- Organize wildcards in subfolders for better organization
- Example structure:
  ```
  wildcards/
  ├── characters/
  │   ├── heroes.txt
  │   └── villains.txt
  └── environments/
      ├── indoor.txt
      └── outdoor.txt
  ```
- Use with full path: `__characters/heroes__`
- Or just filename: `__heroes__` (automatically finds the file)

#### 3. Recursive Wildcard Processing
- Wildcard files can now contain other wildcards
- Automatically expands nested wildcards up to 20 levels deep
- Example:
  - Create `combo.txt` with: `__subject__ in __style__`
  - Use `__combo__` in your prompt
  - Both wildcards inside will be expanded!

#### 4. Auto-Refresh Option
- New `autorefresh` input parameter:
  - **No** (default): Cache files for faster performance
  - **Yes**: Reload files each generation (see edits immediately)
- Perfect for live editing and testing new wildcard files

#### 5. Enhanced File Caching
- Improved performance with intelligent file caching
- Recursive file discovery for nested folders
- Multiple lookup strategies for maximum flexibility

### Technical Improvements
- Added PIL/Pillow for text preview generation
- Integrated `folder_paths` for proper ComfyUI temp directory handling
- Enhanced wildcard pattern matching for nested wildcards
- Improved error handling and logging

### Example Files Added
- `wildcards/characters/heroes.txt`
- `wildcards/characters/villains.txt`
- `wildcards/environments/indoor.txt`
- `wildcards/environments/outdoor.txt`
- `wildcards/nested_example.txt` (demonstrates recursive wildcards)

### Bug Fixes
- Fixed issue with wildcard regex not properly handling nested content
- Improved comma cleanup for cleaner output
- Better handling of empty or comment-only lines

---

## v1.0 - Initial Release

### Features
- Basic wildcard replacement from .txt files
- Range-based selection (`__1-3$$filename__`)
- Seeded randomization for reproducibility
- Comment support in wildcard files
- Inline comment removal
- Automatic comma formatting
- Clean output formatting

### Initial Example Files
- subject.txt
- style.txt
- quality.txt
- lighting.txt
- colors.txt
- mood.txt
