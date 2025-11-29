# DuoUmiWild - ComfyUI Wildcard Node

A custom node for ComfyUI that randomly feeds wildcards from `.txt` files into your prompts.

## Installation

1. Navigate to your ComfyUI custom nodes directory:
   ```
   cd ComfyUI/custom_nodes/
   ```

2. Clone or copy this repository:
   ```
   git clone https://github.com/UndefinedUo/DuoUmiWildcards.git
   ```

3. Restart ComfyUI

The node will appear under the **DuoUmiWild** category in the node menu.

## Usage

### Basic Wildcard Syntax

Use `__filename__` in your prompt to randomly select a line from `wildcards/filename.txt`:

```
a photo of __subject__, __style__
```

This will:
- Read a random line from `wildcards/subject.txt`
- Read a random line from `wildcards/style.txt`
- Replace the wildcards with the selected values

### Range Selection Syntax

Select multiple random items from a wildcard file:

- `__2$$colors__` - Select exactly 2 random colors
- `__1-3$$animals__` - Select between 1 and 3 random animals
- `__-5$$tags__` - Select up to 5 random tags
- `__2-$$items__` - Select at least 2 random items

Examples:
```
__3$$artist__ style painting
__1-2$$mood__, __2-4$$colors__
```

### Creating Wildcard Files

1. Create a `wildcards` folder in the DuoUmiWild directory (it's created automatically on first run)

2. Create `.txt` files with one option per line:

**wildcards/subject.txt:**
```
beautiful woman
handsome man
cute cat
majestic dragon
```

**wildcards/style.txt:**
```
photorealistic
anime style
oil painting
watercolor
digital art
```

3. Use comments to document your wildcards (lines starting with `#` are ignored):

```
# Portrait subjects
beautiful woman
handsome man
# Fantasy subjects
elf warrior
dwarf blacksmith
```

### Using the Seed Parameter

The seed parameter ensures reproducible results:
- Same seed = same random selections
- Different seed = different random selections
- Connect to your KSampler's seed for consistent generations

## Node Inputs

- **text**: Your prompt with wildcards in `__filename__` format
- **seed**: Random seed for reproducible wildcard selection (0 to max int)

## Node Outputs

- **processed_text**: Your prompt with all wildcards replaced with random selections

## Examples

### Simple Example
**Input:**
```
a __quality__ photo of a __subject__
```

**Wildcard files:**
- `wildcards/quality.txt`: high-quality, stunning, professional
- `wildcards/subject.txt`: cat, dog, bird

**Possible outputs:**
- "a stunning photo of a cat"
- "a professional photo of a bird"
- "a high-quality photo of a dog"

### Advanced Example
**Input:**
```
__1-2$$mood__ portrait of __subject__, __2-3$$style__, __lighting__
```

**Possible output:**
```
dramatic, moody portrait of elegant woman, oil painting, renaissance style, soft lighting
```

## Features

- ✅ Random line selection from .txt files
- ✅ Range-based selection (select multiple items)
- ✅ Seeded randomization for reproducibility
- ✅ Comment support in wildcard files (lines starting with #)
- ✅ Inline comment removal
- ✅ Nested wildcard support
- ✅ Automatic comma formatting
- ✅ Clean output (removes extra commas and whitespace)

## File Structure

```
DuoUmiWild/
├── __init__.py          # Node registration
├── wildcard_node.py     # Main node implementation
├── README.md            # This file
└── wildcards/           # Your wildcard .txt files
    ├── subject.txt
    ├── style.txt
    ├── colors.txt
    └── ...
```

## Tips

1. **Organize your wildcards**: Create separate files for different categories (subjects, styles, colors, moods, etc.)

2. **Use descriptive filenames**: Name files clearly so you can easily remember them in prompts

3. **Comment your files**: Add comments to organize and document your wildcard collections

4. **Test with different seeds**: Try different seed values to explore various combinations

5. **Combine with other nodes**: Connect the output to any node that accepts text/string input

## Troubleshooting

**Wildcard not found:**
- Check that the file exists in the `wildcards/` directory
- Ensure the filename matches exactly (case-sensitive on some systems)
- Verify the file has a `.txt` extension

**No output / empty result:**
- Check that your wildcard files aren't empty
- Ensure lines aren't all comments
- Look at the console for error messages

**Same result every time:**
- Verify you're changing the seed value
- Or connect to a random seed generator node

## License

MIT License - Feel free to use and modify as needed.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues on GitHub.

## Credits

Inspired by the original UmiAI wildcard system for Stable Diffusion WebUI.
