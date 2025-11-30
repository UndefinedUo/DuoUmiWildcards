# Latent Ratio Selector Guide

The Latent Ratio Selector node creates empty latent images with predefined aspect ratios, perfect for different types of image generation.

## Features

- **17 preset ratios** covering common use cases
- **Manual selection** or **random selection**
- **Category-based randomization** (Portrait, Landscape, Square, or All)
- **Seeded randomization** for reproducible results
- **Multiple outputs** including width, height, and ratio description

## Usage

### Basic Usage

1. Add the "Latent Ratio Selector" node to your workflow
2. Choose a ratio from the `ratio_selected` dropdown
3. Connect the `latent` output to your KSampler or other latent-compatible nodes

### Random Ratio Selection

1. Set `randomize` to **Yes**
2. Choose a category from `randomize_from`:
   - **All**: Random from any ratio
   - **Portrait Only**: Only portrait orientations
   - **Landscape Only**: Only landscape orientations
   - **Square Only**: 1:1 aspect ratio
3. Set a `seed` value for reproducible randomization
4. The `ratio_used` output tells you which ratio was selected

## Available Ratios

### Portrait Ratios
Perfect for character portraits, selfies, and vertical compositions.

- **2:3 Portrait** - 832x1248 (classic portrait)
- **3:4 Standard Portrait** - 880x1176 (slightly wider)
- **4:5 Large Format Portrait** - 912x1144 (Instagram-style)
- **9:16 Selfie & Social Media** - 768x1360 (phone screen ratio)

### Square Ratio
Perfect for profile pictures, balanced compositions, and social media posts.

- **1:1 Square** - 1024x1024 (perfectly square)

### Landscape Ratios
Perfect for landscapes, wide scenes, and cinematic shots.

- **4:3 SD TV** - 1176x880 (classic TV ratio)
- **3:2 Landscape** - 1216x832 (photography standard)
- **16:9 Widescreen HD TV** - 1360x768 (modern widescreen)
- **21:9 Ultrawide** - 1536x640 (ultrawide monitor)

### Cinematic Ratios
Perfect for film-style compositions and dramatic scenes.

- **1.43:1 IMAX** - 1224x856 (IMAX film format)
- **1.66:1 European Widescreen** - 1312x792 (European cinema)
- **1.85:1 Standard Widescreen** - 1392x752 (US theatrical standard)
- **2.35:1 Cinemascope** - 1568x664 (classic anamorphic)
- **2.39:1 Anamorphic Widescreen** - 1576x656 (modern anamorphic)

### Special Ratios

- **1.618:1 Golden Ratio** - 1296x800 (mathematically aesthetic ratio)

## Node Outputs

The node provides 4 outputs:

1. **latent**: The empty latent tensor (connect to KSampler)
2. **ratio_used**: String describing the ratio (e.g., "16:9 Widescreen HD TV - 1360x768")
3. **width**: Image width in pixels (INT)
4. **height**: Image height in pixels (INT)

## Example Workflows

### Fixed Ratio Workflow

```
[Latent Ratio Selector]
  ratio_selected: "16:9 Widescreen HD TV - 1360x768"
  batch_size: 1
  randomize: No
    ↓ (latent)
[KSampler]
    ↓
[VAE Decode]
```

### Random Landscape Workflow

```
[Latent Ratio Selector]
  ratio_selected: (ignored)
  batch_size: 4
  randomize: Yes
  randomize_from: "Landscape Only"
  seed: 12345
    ↓ (latent)
[KSampler]
    ↓
[VAE Decode]
```

This will randomly select one of the landscape ratios (16:9, 21:9, 4:3, etc.) and generate 4 images with that ratio.

### Combined with Wildcard Node

```
[Wildcard Prompt]
  text: "__subject__, __style__, __lighting__"
  seed: 12345
    ↓ (processed_text)
[CLIP Text Encode]
    ↓
[KSampler]
  latent ← [Latent Ratio Selector]
             randomize: Yes
             randomize_from: "All"
             seed: 12345
```

Use the same seed for both nodes to maintain consistency across generations!

## Tips

1. **Match seeds**: Use the same seed for the Ratio Selector and your prompt generation for consistent results

2. **Portrait for characters**: Use portrait ratios when generating character-focused images

3. **Landscape for scenes**: Use landscape ratios for environmental shots and wide scenes

4. **Cinematic for drama**: Use 2.35:1 or 2.39:1 for dramatic, film-like compositions

5. **Random exploration**: Use "All" randomization to discover what works best for your prompts

6. **Category filtering**: Use category-based randomization (Portrait Only, Landscape Only) when you know the general composition you want

## Comparison with Manual Empty Latent

Traditional Empty Latent Image nodes require you to manually enter width and height. The Ratio Selector:

✅ Provides preset ratios optimized for common use cases
✅ Ensures proper dimensions (divisible by 8 for latent space)
✅ Supports randomization with categories
✅ Shows clear ratio descriptions
✅ Outputs width/height for reference

## Resolution Guide

All resolutions are optimized for SDXL and similar models:
- Total pixel count stays around 1M pixels
- Dimensions are divisible by 64 for optimal VAE encoding/decoding
- Balanced between detail and generation speed

**Note**: For SD1.5 models, you may want to use lower resolutions. These ratios are optimized for SDXL (1024x1024 base).
