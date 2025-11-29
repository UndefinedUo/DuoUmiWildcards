# DuoUmiWild Examples

This guide shows you various ways to use the Wildcard Prompt node.

## Basic Examples

### Simple Wildcard Replacement

**Input:**
```
__subject__
```

**Result:**
One random line from `wildcards/subject.txt`, for example:
- "beautiful woman"
- "cute cat"
- "dragon knight"

### Multiple Wildcards

**Input:**
```
a __quality__ photo of a __subject__, __style__
```

**Possible Results:**
- "a stunning photo of a cute cat, anime style"
- "a professional photo of a handsome man, oil painting"
- "a masterpiece photo of a fairy princess, photorealistic"

### Wildcards with Context

**Input:**
```
portrait of __subject__, __lighting__, __colors__, highly detailed
```

**Possible Result:**
```
portrait of elegant lady, soft lighting, warm tones, highly detailed
```

## Range-Based Selection

### Exact Number Selection

**Input:**
```
__2$$colors__ landscape with __3$$mood__ atmosphere
```

**Result:**
Selects exactly 2 colors and exactly 3 moods:
```
vibrant colors, pastel colors landscape with dramatic, ethereal, mysterious atmosphere
```

### Range Selection

**Input:**
```
__1-3$$style__ artwork featuring __2-4$$colors__
```

**Result:**
Selects 1 to 3 styles and 2 to 4 colors randomly:
- "digital art, anime style artwork featuring red, blue, purple, pink"
- "oil painting artwork featuring green, yellow"

### Open-Ended Ranges

**Input:**
```
__2-$$subject__ in the scene
```

**Result:**
Selects at least 2 subjects:
```
cute cat, loyal dog, wise owl in the scene
```

**Input:**
```
__-3$$lighting__ effects
```

**Result:**
Selects up to 3 lighting types:
```
soft lighting, dramatic lighting effects
```

## Advanced Combinations

### Complex Prompt Building

**Input:**
```
__1-2$$quality__ __style__ illustration of __subject__, __lighting__, featuring __2-3$$colors__, __mood__ atmosphere, professional composition
```

**Possible Result:**
```
masterpiece, award-winning digital art illustration of elf warrior, golden hour, featuring vibrant colors, warm tones, cool tones, dramatic, cinematic atmosphere, professional composition
```

### Layered Descriptions

**Input:**
```
a scene with __subject__ and __subject__, __style__, __lighting__, __1-2$$mood__ mood
```

**Result (note: each `__subject__` gets a different random selection):**
```
a scene with beautiful woman and majestic horse, watercolor, candlelight, serene, peaceful mood
```

## Workflow Integration Examples

### With CLIP Text Encode

```
[Wildcard Prompt Node]
  text: "__quality__ photo of __subject__, __style__, __lighting__"
  seed: [connected to seed value]
    ↓
[CLIP Text Encode (Positive)]
    ↓
[KSampler]
```

### With Multiple Prompts

**Positive Prompt:**
```
__quality__ portrait of __subject__, __style__, __lighting__, __colors__, detailed
```

**Negative Prompt (using another Wildcard Node):**
Create `wildcards/negative.txt`:
```
blurry
low quality
distorted
ugly
bad anatomy
```

Then use:
```
__1-3$$negative__
```

### Dynamic Style Mixing

**Input:**
```
{__style__|__style__|__style__} blend
```

This uses ComfyUI's native `{}` syntax combined with wildcards to mix styles.

## Practical Use Cases

### Character Generation

**Input:**
```
full body portrait of __subject__, wearing __clothing__, __pose__, __style__, __lighting__, __mood__ atmosphere, 8k, highly detailed
```

Create `wildcards/clothing.txt`:
```
armor
casual clothes
formal suit
fantasy robes
cyberpunk outfit
```

Create `wildcards/pose.txt`:
```
standing confidently
action pose
sitting relaxed
dramatic stance
walking forward
```

### Landscape Generation

**Input:**
```
__1-2$$quality__ landscape, __time__ __weather__, __2-3$$colors__ color palette, __style__, __mood__ atmosphere
```

Create `wildcards/time.txt`:
```
sunrise
sunset
midday
night
dawn
dusk
```

Create `wildcards/weather.txt`:
```
clear sky
cloudy
stormy
foggy
snowy
rainy
```

### Artistic Experimentation

**Input:**
```
__subject__ in the style of __2-3$$artist__, __1-2$$medium__, __lighting__
```

Create `wildcards/artist.txt`:
```
Van Gogh
Monet
Picasso
Dali
Banksy
Studio Ghibli
```

Create `wildcards/medium.txt`:
```
oil on canvas
watercolor
digital painting
mixed media
charcoal
pastels
```

## Tips and Tricks

### 1. Consistent Themes

Use the same seed across multiple generations to maintain consistent wildcard selections while varying other parameters.

### 2. Weighted Randomness

Create wildcard files with duplicate entries to increase probability:

`wildcards/weighted_subjects.txt`:
```
cat
cat
cat
dog
dog
dragon
```

This makes "cat" 3x more likely than "dragon".

### 3. Nested Folder Organization

Organize wildcards by category using subfolders:

```
wildcards/
  characters/
    heroes.txt
    villains.txt
  environments/
    indoor.txt
    outdoor.txt
```

Then reference with full path: `__characters/heroes__`

Or just use the filename (it will find it): `__heroes__`

**Example:**
```
__characters/heroes__ vs __characters/villains__ in __environments/indoor__
```

### 4. Recursive Wildcards

Create wildcard files that reference other wildcards:

**wildcards/combo_scene.txt:**
```
__subject__ in a __environments/indoor__
__quality__ __style__ artwork
__1-2$$mood__ scene with __lighting__
```

**Input:**
```
__combo_scene__
```

**Result:**
The node will expand `__combo_scene__`, then expand all wildcards within it recursively!

### 5. Auto-Refresh for Live Editing

When creating or editing wildcard files:
- Set **autorefresh** to **Yes** to see changes immediately
- Set to **No** for faster performance (caches files)

### 6. Seasonal Wildcards

Create seasonal variations:

`wildcards/summer.txt`, `wildcards/winter.txt`, etc.

Switch between them based on your needs.

### 7. Quality Tiers

Create different quality presets:

`wildcards/quality_low.txt`:
```
decent
acceptable
okay
```

`wildcards/quality_high.txt`:
```
masterpiece
award-winning
stunning
professional
museum quality
```

## Common Patterns

### Portrait Pattern
```
__quality__ portrait of __subject__, __style__, __lighting__, __colors__, __mood__ expression
```

### Landscape Pattern
```
__quality__ landscape, __environment__ setting, __time__ __weather__, __style__, __colors__, __mood__ atmosphere
```

### Abstract Pattern
```
__style__ __mood__ composition, __colors__, __lighting__, abstract, artistic
```

### Photorealistic Pattern
```
__quality__ photo of __subject__, __lighting__, shot on __camera__, __lens__, photorealistic, detailed
```

Create `wildcards/camera.txt` and `wildcards/lens.txt` for the camera pattern!

## Debugging Tips

1. **Test individual wildcards first:**
   ```
   __subject__
   ```

2. **Build complexity gradually:**
   ```
   __subject__, __style__
   ```

3. **Check the console output** for missing file warnings

4. **Use consistent seeds** when testing to reproduce results

5. **Verify file contents** by opening the .txt files

Happy prompting!
