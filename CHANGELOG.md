# Changelog

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
