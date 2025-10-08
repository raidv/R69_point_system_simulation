import logging 
import os 
from typing import List
# Note: The Participant class is defined in simulation_core.py, so this import is correct.
from simulation_core import Participant


# ==============================================================================
# FIXED PARTICIPANT DATA
# ==============================================================================

PARTICIPANT_DATA: List[tuple[str, float]] = [
    ("Rank_01", 100), ("Rank_02", 90), ("Rank_03", 80), ("Rank_04", 70),
    ("Rank_05", 60), ("Rank_06", 50), ("Rank_07", 40), ("Rank_08", 30),
    ("Rank_09", 20), ("Rank_10", 10), ("Rank_11", 5), ("Rank_12", 1)
]

# Global counter to ensure unique log filenames
competition_counter: int = 0


# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

def setup_logger(log_file_name: str, console_output: bool, log_subdir: str = None) -> logging.Logger:
    """
    Sets up a logger and creates nested directory paths if log_subdir is provided.
    """
    logger = logging.getLogger(log_file_name)
    logger.setLevel(logging.INFO)
    logger.handlers = []
    logger.propagate = False 

    formatter = logging.Formatter('%(message)s')

    # Console Handler (prints to console if enabled)
    if console_output:
        # ... (Console Handler setup remains the same) ...
        pass

    # File Handler (logs to file)
    log_dir_base = "simulation_logs"
    
    # Create nested structure if subdir is provided (for verbose stage logs)
    if log_subdir:
        log_dir = os.path.join(log_dir_base, log_subdir)
    else:
        # Use the base directory (e.g., for the optimization sweep file)
        log_dir = log_dir_base 

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_path = os.path.join(log_dir, log_file_name)
    fh = logging.FileHandler(log_path, mode='w')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger


def generate_fresh_participants() -> List[Participant]:
    """
    Creates a new list of Participant objects with reset points for each competition run.
    """
    return [Participant(i + 1, name, skill) for i, (name, skill) in enumerate(PARTICIPANT_DATA)]