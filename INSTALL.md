# Installation Guide

## Quick Install

### Method 1: Git Clone (Recommended)

1. Open a terminal/command prompt

2. Navigate to your ComfyUI custom_nodes directory:
   ```bash
   cd path/to/ComfyUI/custom_nodes/
   ```

3. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/DuoUmiWild.git
   ```

4. Restart ComfyUI

### Method 2: Manual Installation

1. Download this repository as a ZIP file

2. Extract the contents to:
   ```
   ComfyUI/custom_nodes/DuoUmiWild/
   ```

3. Make sure the folder structure looks like this:
   ```
   ComfyUI/
   └── custom_nodes/
       └── DuoUmiWild/
           ├── __init__.py
           ├── wildcard_node.py
           ├── README.md
           └── wildcards/
               ├── subject.txt
               ├── style.txt
               └── ...
   ```

4. Restart ComfyUI

## Verifying Installation

1. Start ComfyUI

2. Right-click in the workflow canvas

3. Navigate to: **Add Node** → **DuoUmiWild** → **Wildcard Prompt**

4. If you see the node, installation was successful!

## First Use

1. Add the **Wildcard Prompt** node to your workflow

2. In the text field, try:
   ```
   a __quality__ photo of a __subject__
   ```

3. Connect the output to your prompt input

4. Generate and watch the wildcards change with different seeds!

## Customizing Wildcards

Edit the `.txt` files in the `wildcards/` folder or create your own:

1. Navigate to `ComfyUI/custom_nodes/DuoUmiWild/wildcards/`

2. Create a new file, e.g., `myfile.txt`

3. Add one option per line:
   ```
   option 1
   option 2
   option 3
   ```

4. Use in prompts with `__myfile__`

No restart needed - changes take effect immediately!

## Troubleshooting

**Node doesn't appear:**
- Verify the folder is named `DuoUmiWild`
- Check that `__init__.py` and `wildcard_node.py` are present
- Look at ComfyUI console for error messages
- Ensure you fully restarted ComfyUI

**Wildcards not working:**
- Check that wildcard files exist in the `wildcards/` folder
- Verify files have `.txt` extension
- Ensure files aren't empty
- Check console for "file not found" messages

**Python errors:**
- DuoUmiWild has no dependencies beyond ComfyUI
- If you see import errors, try reinstalling ComfyUI

## Support

If you encounter issues:
1. Check the console output for error messages
2. Verify your file structure matches the examples
3. Open an issue on GitHub with details
