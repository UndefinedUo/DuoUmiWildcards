# YAML Wildcard Guide

DuoUmiWild supports advanced YAML-based wildcards with tag-based selection, prefixes, suffixes, and randomization.

## YAML File Structure

YAML files should be placed in the `wildcards/` directory with a `.yaml` extension.

### Basic Structure

```yaml
Entry Name:
  Prompts:
    - 'prompt option 1'
    - 'prompt option 2'
    - 'prompt option 3'
  Tags:
    - Tag1
    - Tag2
    - Tag3
  Prefix:
    - 'optional prefix 1'
    - 'optional prefix 2'
  Suffix:
    - 'optional suffix 1'
    - 'optional suffix 2'
```

### Components

- **Entry Name**: The title/key for this YAML entry
- **Prompts**: List of prompt variations to randomly select from
- **Tags**: List of tags used for tag-based selection
- **Prefix** (optional): Prompts that get added to the START of your final prompt
- **Suffix** (optional): Prompts that get added to the END of your final prompt

## How It Works

When a YAML entry is selected:
1. **Random Choice**: The node randomly chooses whether to use a Prompt, Prefix, or Suffix
2. **Prompts**: Inserted at the location where you referenced it
3. **Prefixes**: Added to the very start of the final prompt
4. **Suffixes**: Added to the very end of the final prompt

### Example

**YAML File (hats.yaml):**
```yaml
Fancy Hat:
  Prompts:
    - 'wearing an elegant top hat'
    - 'wearing a fancy fedora'
  Tags:
    - Hat
    - Headwear
    - Fancy
  Prefix:
    - 'dressed elegantly'
  Suffix:
    - 'looking sophisticated'
```

**Your Prompt:**
```
girl, smiling, <[Hat]>, red blouse
```

**Possible Outputs:**
1. If it selects a **Prompt**:
   ```
   girl, smiling, wearing an elegant top hat, red blouse
   ```

2. If it selects a **Prefix**:
   ```
   dressed elegantly, girl, smiling, red blouse
   ```

3. If it selects a **Suffix**:
   ```
   girl, smiling, red blouse, looking sophisticated
   ```

## Tag-Based Selection

### Single Tag
Select any entry with a specific tag:

```
<[Pose]>
```

Selects any YAML entry tagged with "Pose"

### Multiple Tags (AND)
Select entries that have ALL specified tags:

```
<[Hat][Fancy]>
```

Selects only entries tagged with BOTH "Hat" AND "Fancy"

### Multiple Tags (OR)
Select entries that have ANY of the specified tags:

```
<[Hat|Headband|Crown]>
```

Selects entries tagged with "Hat" OR "Headband" OR "Crown"

### Complex Combinations

You can combine AND and OR:
```
<[Outfit][Fancy|Formal]>
```

Selects entries tagged with "Outfit" AND ("Fancy" OR "Formal")

## Direct Title References

You can reference YAML entries directly by their title after using `{}` randomization:

**YAML (breast_sizes.yaml):**
```yaml
a-size:
  Prompts:
    - 'a-cup breasts'
  Tags:
    - Breast Size

b-size:
  Prompts:
    - 'b-cup breasts'
  Tags:
    - Breast Size
```

**Your Prompt:**
```
girl, {a|b|c|d|e|f}-size, smiling
```

**Process:**
1. `{}` randomly selects a letter, e.g., "c"
2. Creates "c-size" in the text
3. Node finds YAML entry titled "c-size"
4. Replaces with the prompt: "c-cup breasts"

**Final Output:**
```
girl, c-cup breasts, smiling
```

## Curly Brace Randomization

Use `{}` with pipe `|` to randomly select options:

### Basic Randomization
```
{hat|bandana|crown}
```

Randomly selects one: "hat" OR "bandana" OR "crown"

### Range-Based Selection

Select multiple options:

```
{2$$red|blue|green|yellow}
```
Selects exactly 2 colors

```
{1-3$$happy|sad|angry|calm}
```
Selects 1 to 3 moods

```
{0-1$$dark skinned female}
```
Selects 0 or 1 of the option (50% chance)

### Nested with YAML

Combine with YAML tags:
```
{<[Upright Pose]>|<[Angled Forward Pose]>}
```

## Complete Examples

### Example 1: Character Generation

**Prompt:**
```
Fullbody image of a girl featuring her entire body from head to toe, __Artist Names__, __Fav Girls__ wearing __Outfit Maker__, {a|b|c|d|e|f|g|h|i|j|k}-size, {0-1$$dark skinned female}
```

**What Happens:**
1. `__Artist Names__` → Replaced with random artist from .txt file
2. `__Fav Girls__` → Replaced with random character from .txt file
3. `__Outfit Maker__` → Replaced with random outfit from .txt file
4. `{a|b|c|d|e|f|g|h|i|j|k}-size` → Randomly picks a letter, creates "d-size", finds YAML entry, gets "d-cup breasts"
5. `{0-1$$dark skinned female}` → 50% chance to include "dark skinned female"

### Example 2: Pose with Tags

**Prompt:**
```
girl standing, <[Active Pose]>, <[Hand Pose]>, smiling
```

**What Happens:**
1. `<[Active Pose]>` → Selects random YAML entry tagged "Active Pose"
2. `<[Hand Pose]>` → Selects random YAML entry tagged "Hand Pose"

**Possible Output:**
```
girl standing, doing a backflip, heart hands, smiling
```

### Example 3: Complex Combination

**Prompt:**
```
<[Pose]> portrait, wearing {<[Hat]>|<[Headband]>}, __lighting__, {happy|sad|neutral} expression
```

**Process:**
1. `<[Pose]>` → Random pose from YAML
2. `{<[Hat]>|<[Headband]>}` → Randomly chooses to use Hat OR Headband tag
3. `__lighting__` → Random lighting from .txt file
4. `{happy|sad|neutral}` → Random expression

## Creating Your Own YAML Files

### Template

```yaml
Entry Name 1:
  Prompts:
    - 'your prompt text here'
    - 'alternative prompt'
  Tags:
    - CategoryTag
    - DescriptorTag
  Prefix:
    - ''
  Suffix:
    - ''

Entry Name 2:
  Prompts:
    - 'another prompt'
  Tags:
    - DifferentTag
  Prefix:
    - 'prefix that goes at start'
  Suffix:
    - 'suffix that goes at end'
```

### Tips

1. **Use Descriptive Tags**: Make tags easy to remember and specific
2. **Leave Prefix/Suffix Empty**: If you don't need them, use `- ''` or `[]`
3. **Multiple Prompts**: Add variety with multiple prompt options
4. **Nested Wildcards**: Prompts can contain `__wildcards__`, `{}`, and `<[tags]>`!
5. **Case Insensitive**: Tags are case-insensitive (Hat = hat = HAT)

## Advanced: Nested Wildcards in YAML

YAML prompts can contain wildcards that will be expanded:

```yaml
Dynamic Outfit:
  Prompts:
    - 'wearing __clothing__, __accessories__'
    - 'dressed in {casual|formal|fantasy} attire, <[Hat]>'
  Tags:
    - Outfit
    - Dynamic
```

When selected, the wildcards inside the prompt will be recursively expanded!

## File Organization

Organize YAML files by category:

```
wildcards/
├── poses.yaml           # All pose-related entries
├── outfits.yaml         # Clothing and outfit entries
├── accessories.yaml     # Hats, jewelry, etc.
├── expressions.yaml     # Facial expressions
└── characters/
    └── attributes.yaml  # Character attributes
```

All YAML files are loaded automatically from anywhere in the `wildcards/` folder!
