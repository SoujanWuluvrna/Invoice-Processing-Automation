import re

def normalize_item_name(name: str) -> str:
    """
    Normalizes item names for DB lookup.
    e.g. 'Widget A' -> 'WidgetA', 'Gadget X' -> 'GadgetX', 'gadgetx' -> 'GadgetX'
    """
    # Remove spaces between word and letter/number
    normalized = re.sub(r'\s+', '', name)
    # Title-case the result for consistent matching
    return normalized.strip()
