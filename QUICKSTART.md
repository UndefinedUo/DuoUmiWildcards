# Quick Start Guide

Get started with DuoUmiWild in 5 minutes!

## Step 1: Install

Copy the `DuoUmiWild` folder to:
```
ComfyUI/custom_nodes/DuoUmiWild/
```

Restart ComfyUI.

## Step 2: Add the Node

1. Right-click in your workflow
2. Go to **Add Node** → **DuoUmiWild** → **Wildcard Prompt**
3. Add it before your CLIP Text Encode node

## Step 3: Try Your First Wildcard

In the Wildcard Prompt node, enter:
```
a __quality__ photo of a __subject__
```

Connect:
- **processed_text output** → **CLIP Text Encode input**
- **seed** (can connect to your KSampler seed or leave as 0)

## Step 4: Generate!

Generate an image. The wildcards will randomly pick from:
- `wildcards/quality.txt` (masterpiece, stunning, professional, etc.)
- `wildcards/subject.txt` (beautiful woman, cute cat, dragon knight, etc.)

## Step 5: Experiment

Try range selections:
```
__1-2$$quality__ portrait of __subject__, __style__, __2-3$$colors__
```

This will pick:
- 1-2 quality modifiers
- 1 subject
- 1 style
- 2-3 colors

## What's Next?

### Create Custom Wildcards

1. Go to `ComfyUI/custom_nodes/DuoUmiWild/wildcards/`
2. Create `myfile.txt`
3. Add options (one per line)
4. Use with `__myfile__`

### Use Different Seeds

Connect the seed input to:
- Your KSampler seed (same seed = same wildcards + same image)
- A separate seed value (vary wildcards independently)
- A random seed generator

### Combine Multiple Nodes

Use multiple Wildcard Prompt nodes for:
- Separate positive and negative prompts
- Complex multi-part prompts
- Different seed strategies per section

## Example Workflow

```
┌─────────────────┐
│ Wildcard Prompt │
│  text: __...__  │
│  seed: 12345    │
└────────┬────────┘
         │
         ↓ (processed_text)
┌─────────────────┐
│ CLIP Text       │
│ Encode (Prompt) │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│   KSampler      │
└────────┬────────┘
         │
         ↓
     [Image]
```

## Tips

- **Same result every time?** Change the seed value
- **Wildcard not found?** Check the filename matches exactly
- **Want more options?** Edit the .txt files in the wildcards folder
- **Comments in wildcards?** Start lines with `#`

## Help

Check these files for more info:
- `README.md` - Full documentation
- `EXAMPLES.md` - Detailed examples
- `INSTALL.md` - Installation help

Happy generating! 🎨
