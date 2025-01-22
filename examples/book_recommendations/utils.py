import logging
from typing import Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def state_merge(state1: Dict, state2: Dict) -> Dict:
    """Merge two states together."""
    state1.update(state2)
    return state1
