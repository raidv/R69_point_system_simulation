from collections import Counter
from typing import List, Tuple

# Import core components and utilities
from simulation_core import Participant, Stage, ChallengeSimulator
from utils import setup_logger, competition_counter


# ==============================================================================
# COMPETITION AND EVALUATION
# ==============================================================================

class Competition:
    """Orchestrates the competition simulation, tracks state, and runs evaluations."""
    def __init__(self, participants: List[Participant], X: float, Y: float, Z: float, C: float, challenge_rand: float, rep_rand: float, verbose: bool = True, log_subdir: str = None):
        global competition_counter
        competition_counter += 1

        self.participants = participants
        self.num_stages = 6
        self.point_config = {'X': X, 'Y': Y, 'Z': Z, 'C': C}
        self.max_stage_points = Y + Z + C  # Max points a single player can earn in a stage
        self.stage_5_leaderboard: List[Participant] | None = None  # Stores state after Stage 5
        self.stage = Stage(X, Y, Z, C)
        self.simulator = ChallengeSimulator(challenge_rand, rep_rand)
        self.verbose = verbose

        log_file_name = f"competition_{competition_counter}_log.txt"
        self.logger = setup_logger(log_file_name, verbose, log_subdir=log_subdir)

        self.logger.info(f"Starting Simulation ({log_file_name})")
        self.logger.info(f"Points: X={X}, Y={Y}, Z={Z}, C={C}")
        self.logger.info(f"Randomness: Challenge={challenge_rand}, Rep Selection={rep_rand}\n")


    # --- Utility Methods ---
    def get_initial_leaderboard(self) -> List[Participant]:
        """Returns all participants sorted by initial skill."""
        return sorted(self.participants, key=lambda p: p.initial_skill, reverse=True)

    def get_final_leaderboard(self) -> List[Participant]:
        """Returns all participants sorted by final total points."""
        return sorted(self.participants, key=lambda p: p.total_points, reverse=True)

    def determine_teams(self, stage_number: int) -> List[List[Participant]]:
        """Forms teams using a snake draft based on current standing."""
        if stage_number == 1:
            sorted_participants = self.get_initial_leaderboard()
        else:
            sorted_participants = self.get_final_leaderboard()

        teams: List[List[Participant]] = [[], [], []]
        
        # Snake Draft logic
        for i, participant in enumerate(sorted_participants):
            team_index = i % 3
            if (i // 3) % 2 == 1: # Reverse direction every other "row"
                team_index = 2 - team_index
            teams[team_index].append(participant)
            
        return teams

    # --- Simulation Flow Methods ---
    def simulate_stage(self, stage_number: int):
        """Runs one full stage of the competition."""
        self.logger.info(f"--- Simulating Stage {stage_number} ---")
        teams = self.determine_teams(stage_number)

        self.logger.info(f"Teams (based on {'Skill' if stage_number == 1 else 'Points'}):")
        for i, team in enumerate(teams):
             self.logger.info(f"  Team {i+1}: {[p.name for p in team]}")

        # Challenge 1
        winning_team_1 = self.stage.run_challenge_1(teams, self.simulator)
        self.logger.info(f"Challenge 1 Winner Team (X={self.point_config['X']}): {[p.name for p in winning_team_1]}")

        # Challenge 2
        winning_team_2 = self.stage.run_challenge_2(teams, self.simulator)
        self.logger.info(f"Challenge 2 Winner Team (Y={self.point_config['Y']}): {[p.name for p in winning_team_2]}")

        # Challenge 3
        winner_rep, winner_team_3, all_reps = self.stage.run_challenge_3(teams, self.simulator)

        self.logger.info(f"Challenge 3 Representatives: {[p.name for p in all_reps]}")
        self.logger.info(f"Challenge 3 Winner Representative (Z={self.point_config['Z']}, C={self.point_config['C']}): {winner_rep.name}")
        self.logger.info(f"Challenge 3 Winner Team: {[p.name for p in winner_team_3]}")

        self.logger.info("\n--- Current Leaderboard ---")
        leaderboard = self.get_final_leaderboard()
        for i, participant in enumerate(leaderboard):
            self.logger.info(f"{i+1}. {participant.name} (Skill: {participant.initial_skill}): {participant.get_points()} points")
        self.logger.info("-" * 30 + "\n")

        if stage_number == 5:
            # Capture the scores *before* any Stage 6 points are added. 
            # We copy the total_points from the current list to a static list.
            current_leaderboard_points = {p.id: p.total_points for p in leaderboard}
            
            # Create a static list of Participants with the current score state
            self.stage_5_leaderboard = [
                Participant(p.id, p.name, p.initial_skill) 
                for p in self.participants
            ]
            for p in self.stage_5_leaderboard:
                p.total_points = current_leaderboard_points[p.id]


    def run_simulation(self):
        """Runs all stages of the competition and generates the final report."""
        for stage_number in range(1, self.num_stages + 1):
            self.simulate_stage(stage_number)

        self.generate_final_report()


    # --- Evaluation Methods ---
    def evaluate_stability(self, top_N: int, target_M: int) -> Tuple[float, int]:
        """Evaluates competitive stability: how many top/bottom initial players remain in the target band."""
        num_participants = len(self.participants)
        initial_board = self.get_initial_leaderboard()
        initial_top_N = initial_board[:top_N]
        initial_bottom_N = initial_board[num_participants - top_N:]
        final_board = self.get_final_leaderboard()

        final_top_M = set(final_board[:target_M])
        top_count = sum(1 for p in initial_top_N if p in final_top_M)

        final_bottom_M = set(final_board[num_participants - target_M:])
        bottom_count = sum(1 for p in initial_bottom_N if p in final_bottom_M)

        successful_players = top_count + bottom_count
        total_possible = 2 * top_N
        stability_score = successful_players / total_possible

        return stability_score, successful_players

    def evaluate_cut_off_collision(self) -> int:
        """Measures the number of people tied across the 6th and 7th rank."""
        final_board = self.get_final_leaderboard()
        num_participants = len(final_board)

        if num_participants < 7:
            return 0

        score_6th = final_board[5].total_points
        score_7th = final_board[6].total_points

        if score_6th > score_7th:
            return 0

        # If score_6th == score_7th, a collision exists. Count all participants with this score.
        collision_score = score_6th
        score_counts = Counter(p.total_points for p in final_board)
        collision_size = score_counts[collision_score]

        return collision_size

    def evaluate_final_contenders(self) -> int:
        """Evaluates how many participants can mathematically still finish in the Top 6 after Stage 5."""
        leaderboard = self.stage_5_leaderboard
        if not leaderboard or len(leaderboard) < 6:
            return 0

        max_stage_points = self.max_stage_points

        # 1. Determine the score of the 6th-ranked participant (the target score)
        score_6th = leaderboard[5].total_points

        contender_count = 0

        # 2. Map participant ID to their Stage 5 score for quick lookup
        stage_5_score_map = {p.id: p.total_points for p in leaderboard}

        # 3. Check every participant's potential
        for participant in self.participants:
            stage_5_score = stage_5_score_map.get(participant.id, 0)

            # Max final score assumes the player wins ALL possible points in Stage 6
            max_final_score = stage_5_score + max_stage_points

            # Check if they can match or beat the current 6th place score
            if max_final_score >= score_6th:
                contender_count += 1

        return contender_count

    # --- Reporting Method ---
    def generate_final_report(self):
        """Logs the evaluation metrics and final leaderboard for the completed competition."""
        
        # 1. Calculate Metrics (using default criteria N=3, M=6)
        N = 3
        M = 6
        stability_score, successful_players = self.evaluate_stability(top_N=N, target_M=M)
        collision_size = self.evaluate_cut_off_collision()
        contender_count = self.evaluate_final_contenders()
        total_possible = 2 * N

        # 2. Log Metrics
        self.logger.info("\n===================================")
        self.logger.info("       FINAL COMPETITION METRICS     ")
        self.logger.info("===================================")

        self.logger.info(f"1. Stability Score (Top {N}/Bottom {N} in Top {M}/Bottom {M}):")
        self.logger.info(f"   Score: {stability_score:.2f} ({successful_players} out of {total_possible} players met criteria)")

        self.logger.info("\n2. Cut-off Collision (6th/7th Rank Tie):")
        self.logger.info(f"   Collision Group Size: {collision_size}")
        if collision_size > 0:
            self.logger.info("   --> WARNING: Tie across the Top 6 / Bottom 6 cut-off.")

        self.logger.info("\n3. Final Stage Contenders (After Stage 5):")
        self.logger.info(f"   Total Contenders for Top 6: {contender_count} out of {len(self.participants)}")
        self.logger.info("===================================\n")


        # 3. Log Final Leaderboard
        self.logger.info("\n========== FINAL RESULTS ==========")
        final_leaderboard = self.get_final_leaderboard()
        for i, participant in enumerate(final_leaderboard):
            self.logger.info(f"{i+1}. {participant.name}: {participant.get_points():.2f} points (Initial Skill: {participant.initial_skill})")
        self.logger.info("===================================\n")