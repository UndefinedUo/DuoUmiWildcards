"""
DuoUmiWild - ComfyUI Wildcard Custom Node
Initialize and register the wildcard and ratio selector nodes with ComfyUI.
"""

from .wildcard_node import NODE_CLASS_MAPPINGS as WILDCARD_MAPPINGS
from .wildcard_node import NODE_DISPLAY_NAME_MAPPINGS as WILDCARD_DISPLAY_MAPPINGS
from .ratio_selector import NODE_CLASS_MAPPINGS as RATIO_MAPPINGS
from .ratio_selector import NODE_DISPLAY_NAME_MAPPINGS as RATIO_DISPLAY_MAPPINGS

# Combine all node mappings
NODE_CLASS_MAPPINGS = {
    **WILDCARD_MAPPINGS,
    **RATIO_MAPPINGS
}

NODE_DISPLAY_NAME_MAPPINGS = {
    **WILDCARD_DISPLAY_MAPPINGS,
    **RATIO_DISPLAY_MAPPINGS
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
