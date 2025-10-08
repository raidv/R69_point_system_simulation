import random
from typing import List, Dict, Tuple


# ==============================================================================
# CORE CLASSES
# ==============================================================================

class Participant:
    """Represents a single competitor."""
    def __init__(self, id: int, name: str, initial_skill: float):
        self.id = id
        self.name = name
        self.initial_skill = initial_skill
        self.total_points = 0.0 # Use float for points consistency

    def add_points(self, points: float):
        """Updates the participant's score, enforcing the zero-point floor."""
        self.total_points += points
        if self.total_points < 0:
            self.total_points = 0.0

    def get_points(self) -> float:
        return self.total_points

    def __repr__(self) -> str:
        """Simple representation for logging and debugging."""
        return self.name


class ChallengeSimulator:
    """Handles logic for determining challenge winners based on skill and randomness."""
    def __init__(self, challenge_rand: float, rep_rand: float):
        self.challenge_randomness = challenge_rand
        self.rep_selection_randomness = rep_rand

    def determine_team_winner(self, teams: List[List[Participant]]) -> List[Participant]:
        """Calculates team scores and returns the winning team."""
        team_scores: List[Tuple[float, List[Participant]]] = []
        # Calculate max skill sum to scale the random factor appropriately
        max_skill_sum = max(sum(p.initial_skill for p in team) for team in teams) if teams else 0.0

        for team in teams:
            team_skill_sum = sum(p.initial_skill for p in team)
            random_component = random.uniform(0.0, max_skill_sum)
            # Score = (Skill Weighted) + (Random Weighted)
            team_score = (1 - self.challenge_randomness) * team_skill_sum + self.challenge_randomness * random_component
            team_scores.append((team_score, team))

        # The team with the highest score wins
        winning_team = max(team_scores, key=lambda item: item[0])[1]
        return winning_team

    def determine_individual_winner(self, representatives: List[Participant]) -> Participant:
        """Calculates individual scores and returns the winning representative."""
        individual_scores: List[Tuple[float, Participant]] = []
        max_skill = max(p.initial_skill for p in representatives) if representatives else 0.0

        for rep in representatives:
            random_component = random.uniform(0.0, max_skill)
            # Score = (Skill Weighted) + (Random Weighted)
            individual_score = (1 - self.challenge_randomness) * rep.initial_skill + self.challenge_randomness * random_component
            individual_scores.append((individual_score, rep))

        winning_rep = max(individual_scores, key=lambda item: item[0])[1]
        return winning_rep

    def select_team_representative(self, team: List[Participant]) -> Participant:
        """Selects one representative from a team based on skill and selection randomness."""
        selection_scores: List[Tuple[float, Participant]] = []
        max_skill = max(p.initial_skill for p in team) if team else 0.0

        for member in team:
            random_component = random.uniform(0.0, max_skill)
            selection_score = (1 - self.rep_selection_randomness) * member.initial_skill + self.rep_selection_randomness * random_component
            selection_scores.append((selection_score, member))

        chosen_rep = max(selection_scores, key=lambda item: item[0])[1]
        return chosen_rep


class Stage:
    """Manages the point distribution for a single competition stage."""
    def __init__(self, X: float, Y: float, Z: float, C: float):
        self.point_values: Dict[str, float] = {'X': X, 'Y': Y, 'Z': Z, 'C': C}

    def run_challenge_1(self, teams: List[List[Participant]], simulator: ChallengeSimulator) -> List[Participant]:
        """Team Challenge 1 (X points)."""
        winning_team = simulator.determine_team_winner(teams)
        for participant in winning_team:
            participant.add_points(self.point_values['X'])
        return winning_team

    def run_challenge_2(self, teams: List[List[Participant]], simulator: ChallengeSimulator) -> List[Participant]:
        """Team Challenge 2 (Y points)."""
        winning_team = simulator.determine_team_winner(teams)
        for participant in winning_team:
            participant.add_points(self.point_values['Y'])
        return winning_team

    def run_challenge_3(self, teams: List[List[Participant]], simulator: ChallengeSimulator) -> Tuple[Participant, List[Participant], List[Participant]]:
        """Individual Challenge 3 (Z and C points)."""
        all_reps = [simulator.select_team_representative(team) for team in teams]
        winner_rep = simulator.determine_individual_winner(all_reps)

        # Find the winning team based on the representative
        winner_team = next((team for team in teams if winner_rep in team), [])
        
        # Point Distribution:
        if winner_team:
            # 1. Team points (Z)
            for participant in winner_team:
                participant.add_points(self.point_values['Z'])

            # 2. Individual Winner bonus (C)
            winner_rep.add_points(self.point_values['C'])

        # 3. Individual Losers penalty (-C)
        for rep in all_reps:
            if rep != winner_rep:
                rep.add_points(-self.point_values['C'])

        # Returns: Winner Rep, Winner Team, All Representatives
        return winner_rep, winner_team, all_reps