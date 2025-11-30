"""
DuoUmiWild - Latent Ratio Selector Node
Selects latent image ratios with optional randomization.
"""

import random
import torch


class LatentRatioSelector:
    """
    A node that creates empty latent images with predefined aspect ratios.
    Supports manual selection or random selection from ratios.
    """

    # All available ratios with their resolutions
    ratio_presets = {
        # Portrait Ratios
        '2:3 Portrait - 832x1248': (832, 1248),
        '3:4 Standard Portrait - 880x1176': (880, 1176),
        '4:5 Large Format Portrait - 912x1144': (912, 1144),
        '9:16 Selfie & Social Media - 768x1360': (768, 1360),

        # Square
        '1:1 Square - 1024x1024': (1024, 1024),

        # Landscape Ratios
        '4:3 SD TV - 1176x880': (1176, 880),
        '1.43:1 IMAX - 1224x856': (1224, 856),
        '1.66:1 European Widescreen - 1312x792': (1312, 792),
        '16:9 Widescreen HD TV - 1360x768': (1360, 768),
        '1.85:1 Standard Widescreen - 1392x752': (1392, 752),
        '2.35:1 Cinemascope - 1568x664': (1568, 664),
        '2.39:1 Anamorphic Widescreen - 1576x656': (1576, 656),
        '1.618:1 Golden Ratio - 1296x800': (1296, 800),

        # Additional Common Ratios
        '3:2 Landscape - 1216x832': (1216, 832),
        '21:9 Ultrawide - 1536x640': (1536, 640),
    }

    # Group ratios by category for easier random selection
    portrait_ratios = [
        '2:3 Portrait - 832x1248',
        '3:4 Standard Portrait - 880x1176',
        '4:5 Large Format Portrait - 912x1144',
        '9:16 Selfie & Social Media - 768x1360',
    ]

    landscape_ratios = [
        '4:3 SD TV - 1176x880',
        '1.43:1 IMAX - 1224x856',
        '1.66:1 European Widescreen - 1312x792',
        '16:9 Widescreen HD TV - 1360x768',
        '1.85:1 Standard Widescreen - 1392x752',
        '2.35:1 Cinemascope - 1568x664',
        '2.39:1 Anamorphic Widescreen - 1576x656',
        '1.618:1 Golden Ratio - 1296x800',
        '3:2 Landscape - 1216x832',
        '21:9 Ultrawide - 1536x640',
    ]

    square_ratios = ['1:1 Square - 1024x1024']

    all_ratios_list = list(ratio_presets.keys())

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "ratio_selected": (cls.all_ratios_list, {
                    "default": "1:1 Square - 1024x1024"
                }),
                "batch_size": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 64
                }),
                "randomize": (["No", "Yes"], {
                    "default": "No",
                    "tooltip": "Randomly select from all ratios (ignores ratio_selected)"
                }),
                "randomize_from": (["All", "Portrait Only", "Landscape Only", "Square Only"], {
                    "default": "All",
                    "tooltip": "When randomize is Yes, select from this category"
                }),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff,
                    "tooltip": "Seed for random ratio selection (when randomize is Yes)"
                }),
            },
        }

    RETURN_TYPES = ("LATENT", "STRING", "INT", "INT")
    RETURN_NAMES = ("latent", "ratio_used", "width", "height")
    FUNCTION = "generate"
    CATEGORY = "DuoUmiWild"

    def generate(self, ratio_selected, batch_size=1, randomize="No", randomize_from="All", seed=0):
        """
        Generate an empty latent image with the specified or random ratio.

        Args:
            ratio_selected: The manually selected ratio
            batch_size: Number of latent images in batch
            randomize: Whether to randomly select a ratio
            randomize_from: Which category to randomize from
            seed: Seed for randomization

        Returns:
            tuple: (latent dict, ratio string, width, height)
        """
        # Determine which ratio to use
        if randomize == "Yes":
            random.seed(seed)

            if randomize_from == "Portrait Only":
                ratio_key = random.choice(self.portrait_ratios)
            elif randomize_from == "Landscape Only":
                ratio_key = random.choice(self.landscape_ratios)
            elif randomize_from == "Square Only":
                ratio_key = random.choice(self.square_ratios)
            else:  # "All"
                ratio_key = random.choice(self.all_ratios_list)
        else:
            ratio_key = ratio_selected

        # Get the resolution
        width, height = self.ratio_presets[ratio_key]

        # Create empty latent tensor
        latent = torch.zeros([batch_size, 4, height // 8, width // 8])

        return ({"samples": latent}, ratio_key, width, height)


# Node registration for ComfyUI
NODE_CLASS_MAPPINGS = {
    "DuoUmiRatioSelector": LatentRatioSelector
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DuoUmiRatioSelector": "Latent Ratio Selector"
}
