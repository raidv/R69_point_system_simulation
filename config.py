# --- COMPETITION CONSTANTS ---
CHALLENGE_RAND: float = 0.4 # Moderate randomness for challenges
REP_RAND: float = 0.3       # Low randomness for rep selection
NUM_COMPETITIONS: int = 100  # Number of runs per parameter combination (Use 50-100 for production)

# --- POINT BOUNDS (All inclusive integers) ---
# 1st challenge point value range for team to be tested
X_LOWER, X_HIGHER = 2, 5
# 2nd challenge point value range for team to be tested
Y_LOWER, Y_HIGHER = 3, 7
# 3rd challenge point value range for team to be tested
Z_LOWER, Z_HIGHER = 1, 5
# 3rd challenge bonus point value range for individual competitor to be tested
C_LOWER, C_HIGHER = 1, 3