# run_sweep.py

from competition_logic import Competition
from utils import PARTICIPANT_DATA, generate_fresh_participants, competition_counter
from typing import Dict, Tuple, List, Any
import os


# ==============================================================================
# 1. CONFIG IMPORTS
# ==============================================================================

from config import (
    CHALLENGE_RAND, REP_RAND, NUM_COMPETITIONS,
    X_LOWER, X_HIGHER, Y_LOWER, Y_HIGHER,
    Z_LOWER, Z_HIGHER, C_LOWER, C_HIGHER
)


def save_detailed_results(results: Dict[str, Any], subdir: str):
    """Saves the detailed aggregated metrics and average leaderboard for one parameter set."""
    
    results_dir = "sweep_results"
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
        
    params = results['params']
    filename = f"RESULTS_C{params['C']}_Z{params['Z']}_X{params['X']}_Y{params['Y']}.txt"
    filepath = os.path.join(results_dir, filename)

    # The log file reference should point to the subfolder containing the detailed logs
    log_file_reference = f"simulation_logs/{subdir}/competition_{results['log_id']}_log.txt (Last Run ID)"


    with open(filepath, 'w') as f:
        f.write("========================================================\n")
        f.write(f"  DETAILED PARAMETER TEST RESULTS: {subdir}  \n")
        f.write("========================================================\n")
        f.write(f"Point Configuration (C, Z, X, Y): ({params['C']}, {params['Z']}, {params['X']}, {params['Y']})\n")
        f.write(f"Randomness: Challenge={CHALLENGE_RAND}, Rep Selection={REP_RAND}\n")
        f.write(f"Total Competitions Run: {NUM_COMPETITIONS}\n\n")

        f.write("--- OPTIMIZATION METRICS ---\n")
        f.write(f"1. OPTIMIZATION SCORE: {results['optimization_score']:.4f}\n")
        f.write("   (Higher is better; 0.0 is minimum acceptable)\n")
        f.write(f"2. Avg. Stability Score (Target >= 4.0): {results['avg_successful_players_count']:.3f} / 6.0\n")
        f.write(f"3. Avg. Collision Size (Target <= 3.0): {results['avg_cut_off_collision_size']:.3f}\n")
        f.write(f"4. Avg. Contenders (Target >= 9.0): {results['avg_contender_count']:.3f}\n\n")

        f.write("--- AVERAGE FINAL LEADERBOARD ---\n")
        for i, entry in enumerate(results['average_leaderboard']):
            f.write(f"{i+1:2}. {entry['name']:8}: {entry['avg_score']:7.3f} points (Skill: {entry['initial_skill']})\n")
        f.write("--------------------------------------------------------\n")
        
        # Updated reference to link the detailed log
        f.write(f"Corresponding Detailed Log File: {log_file_reference}\n") 

    print(f"   [Report Saved: {filename}]")



# ==============================================================================
# 2. PARAMETER TEST FUNCTION
# ==============================================================================

def run_parameter_test(
    X: int, Y: int, Z: int, C: int,
    challenge_rand: float, rep_rand: float, num_runs: int
) -> Dict[str, Any]: 

    # Aggregator variables
    total_stability_score = 0.0
    total_collision_size = 0
    total_contender_count = 0
    total_successful_players = 0
    avg_score_tracker = {name: 0.0 for name, _ in PARTICIPANT_DATA}

    STABILITY_TOP_N = 3
    STABILITY_TARGET_M = 6

    # Define the nested log subdirectory name
    log_subdir = f"C{C}_Z{Z}_X{X}_Y{Y}"

    for i in range(1, num_runs + 1):
        participants = generate_fresh_participants()

        # The Competition counter is incremented inside Competition.__init__
        competition = Competition(
            participants=participants, X=float(X), Y=float(Y), Z=float(Z), C=float(C),
            challenge_rand=challenge_rand, rep_rand=rep_rand,
            verbose=False, log_subdir=log_subdir 
        )

        competition.run_simulation()

        # Aggregate metrics
        stability_score, successful_players = competition.evaluate_stability(
            top_N=STABILITY_TOP_N, target_M=STABILITY_TARGET_M
        )
        total_stability_score += stability_score
        total_successful_players += successful_players
        total_collision_size += competition.evaluate_cut_off_collision()
        total_contender_count += competition.evaluate_final_contenders()

        for p in competition.get_final_leaderboard():
            avg_score_tracker[p.name] += p.total_points

    # Final calculations
    num_runs_f = float(num_runs)
    avg_stability = total_stability_score / num_runs_f
    avg_successful_players = total_successful_players / num_runs_f
    avg_collision = total_collision_size / num_runs_f
    avg_contenders = total_contender_count / num_runs_f

    # Optimization Score Calculation
    REQUIRED_STABILITY_SUCCESS = 4.0
    MAX_COLLISION = 3.0
    MIN_CONTENDERS = 9.0

    optimization_score = (avg_successful_players - REQUIRED_STABILITY_SUCCESS) + \
                         (MAX_COLLISION - avg_collision) + \
                         (avg_contenders - MIN_CONTENDERS)

    # Average Leaderboard calculation
    average_leaderboard = sorted([
        {"name": name, "avg_score": total_score / num_runs_f,
         "initial_skill": next(skill for p_name, skill in PARTICIPANT_DATA if p_name == name)}
        for name, total_score in avg_score_tracker.items()
    ], key=lambda x: x['avg_score'], reverse=True)

    # competition_counter holds the ID of the last run's log file for this parameter set
    last_log_id = competition_counter 

    results = {
        "params": {'X': X, 'Y': Y, 'Z': Z, 'C': C},
        "log_id": last_log_id,
        "optimization_score": optimization_score,
        "avg_stability_score": avg_stability,
        "avg_successful_players_count": avg_successful_players,
        "avg_cut_off_collision_size": avg_collision,
        "avg_contender_count": avg_contenders,
        "average_leaderboard": average_leaderboard
    }

    save_detailed_results(results, log_subdir)

    return results
    


# ==============================================================================
# 3. REPORTING FUNCTIONS
# ==============================================================================

def save_sweep_results(all_test_results: List[Dict[str, Any]]):
    """Saves the final optimization leaderboard to a text file."""

    text_file = "optimization_sweep_leaderboard.txt"
    csv_file = "optimization_sweep_leaderboard.csv"

    # Sort results by optimization score descending
    final_leaderboard = sorted(
        all_test_results,
        key=lambda r: r['optimization_score'],
        reverse=True
    )

    with open(text_file, 'w') as f:
        f.write("=================================================================================\n")
        f.write("                       OPTIMIZATION SWEEP LEADERBOARD\n")
        f.write(f"Parameters: X, Y, Z, C | Runs per combo: {NUM_COMPETITIONS} | Challenge Rand: {CHALLENGE_RAND}\n")
        f.write("=================================================================================\n")
        f.write("Rank | Score  | X | Y | Z | C | Stability | Collision | Contenders\n")
        f.write("-----|--------|---|---|---|---|-----------|-----------|-----------\n")

        for i, result in enumerate(final_leaderboard):
            params = result['params']
            f.write(
                f"{i+1:4} | {result['optimization_score']:<5.3f} | "
                f"{params['X']:1} | {params['Y']:1} | {params['Z']:1} | {params['C']:1} | "
                f"{result['avg_successful_players_count']:<9.3f} | "
                f"{result['avg_cut_off_collision_size']:<9.3f} | "
                f"{result['avg_contender_count']:<10.3f}\n"
            )

    with open(csv_file, 'w') as f:
        # Write CSV Headers
        f.write("Rank,Optimization_Score,X,Y,Z,C,Avg_Successful_Players,Avg_Collision_Size,Avg_Contender_Count,Log_Subdir,Log_File_ID\n")
        
        for i, result in enumerate(final_leaderboard):
            params = result['params']
            log_subdir = f"C{params['C']}_Z{params['Z']}_X{params['X']}_Y{params['Y']}"
            
            # Write data row
            f.write(
                f"{i+1},"
                f"{result['optimization_score']:.4f},"
                f"{params['X']},{params['Y']},{params['Z']},{params['C']},"
                f"{result['avg_successful_players_count']:.4f},"
                f"{result['avg_cut_off_collision_size']:.4f},"
                f"{result['avg_contender_count']:.4f},"
                f"{log_subdir},"
                f"competition_{result['log_id']}_log.txt\n"
            )

    print("\nOptimization sweep complete. Final leaderboard saved to:\n")
    print(f"  - Text Report: {text_file}")
    print(f"  - CSV Data: {csv_file}")
    print("Full details for each test are available in the 'simulation_logs' folder.")


# ==============================================================================
# 4. MASTER SWEEP FUNCTION
# ==============================================================================

def run_optimization_sweep(
    X_bounds: Tuple[int, int], Y_bounds: Tuple[int, int],
    Z_bounds: Tuple[int, int], C_bounds: Tuple[int, int],
    challenge_rand: float, rep_rand: float, num_runs: int
):
    """
    Executes simulations for all valid integer point combinations (C < Z < X < Y).
    """

    all_test_results = []
    
    # Print header for progress tracking
    print("Starting Optimization Sweep...")
    print(f"Bounds: C=[{C_LOWER}-{C_HIGHER}], Z=[{Z_LOWER}-{Z_HIGHER}], X=[{X_LOWER}-{X_HIGHER}], Y=[{Y_LOWER}-{Y_HIGHER}]")
    print("-" * 60)

    # Nested loops for all combinations
    for C in range(C_bounds[0], C_bounds[1] + 1):
        for Z in range(Z_bounds[0], Z_bounds[1] + 1):
            #if C >= Z: # Commented this out to allow for C to be greater than Z
            #    continue 

            for X in range(X_bounds[0], X_bounds[1] + 1):
                if Z >= X: 
                    continue 

                for Y in range(Y_bounds[0], Y_bounds[1] + 1):
                    if X >= Y: 
                        continue 

                    # Combination is valid: C < Z < X < Y
                    print(f"Testing combination: C={C}, Z={Z}, X={X}, Y={Y}")

                    # Run the parameter test
                    results = run_parameter_test(
                        X=X, Y=Y, Z=Z, C=C,
                        challenge_rand=challenge_rand, rep_rand=rep_rand, num_runs=num_runs
                    )

                    all_test_results.append(results)

    # Save the final sorted leaderboard to a file
    save_sweep_results(all_test_results)


# ==============================================================================
# 5. EXECUTION POINT
# ==============================================================================

if __name__ == '__main__':
    run_optimization_sweep(
        X_bounds=(X_LOWER, X_HIGHER), Y_bounds=(Y_LOWER, Y_HIGHER),
        Z_bounds=(Z_LOWER, Z_HIGHER), C_bounds=(C_LOWER, C_HIGHER),
        challenge_rand=CHALLENGE_RAND, rep_rand=REP_RAND, num_runs=NUM_COMPETITIONS
    )