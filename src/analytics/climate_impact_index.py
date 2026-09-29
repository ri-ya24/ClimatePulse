import sys
from pathlib import Path
import subprocess
import re

sys.path.append(str(Path(__file__).resolve().parents[1]))

BASE_DIR = Path(__file__).parent


def run_script(script_name):
    script_path = BASE_DIR / script_name

    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"\nError while running {script_name}")
        print(result.stderr)
        sys.exit(1)

    return result.stdout


def extract_score(output, pattern):
    match = re.search(pattern, output)

    if not match:
        print("\nCould not extract score from output.")
        print(output)
        sys.exit(1)

    return float(match.group(1))


print("\nClimatePulse Climate Impact Index")
print("---------------------------------")
print("Calculating latest component scores...\n")


# --------------------------------------------------
# 1. HEAT IMPACT
# --------------------------------------------------

heat_output = run_script("heat_impact_score.py")

heat_score = extract_score(
    heat_output,
    r"Heat Impact Score\s*\n-+\s*\n([\d.]+)"
)


# --------------------------------------------------
# 2. RAINFALL IMPACT
# --------------------------------------------------

rainfall_output = run_script("rainfall_impact_score.py")

rainfall_score = extract_score(
    rainfall_output,
    r"Rainfall Impact Score\s*\n-+\s*\n([\d.]+)"
)


# --------------------------------------------------
# 3. AIR QUALITY IMPACT
# --------------------------------------------------

air_quality_output = run_script("air_quality_score.py")

air_quality_score = extract_score(
    air_quality_output,
    r"Air Quality Impact Score\s*\n-+\s*\n([\d.]+)"
)


# --------------------------------------------------
# 4. DRYNESS IMPACT
# --------------------------------------------------

dryness_output = run_script("dryness_impact_score.py")

dryness_score = extract_score(
    dryness_output,
    r"Dryness Impact Score\s*\n-+\s*\n([\d.]+)"
)


# --------------------------------------------------
# PROJECT-DEFINED WEIGHTS
# --------------------------------------------------

heat_weight = 0.35
rainfall_weight = 0.25
air_quality_weight = 0.25
dryness_weight = 0.15


# --------------------------------------------------
# CLIMATE IMPACT INDEX
# --------------------------------------------------

climate_impact_index = (
    heat_score * heat_weight
    + rainfall_score * rainfall_weight
    + air_quality_score * air_quality_weight
    + dryness_score * dryness_weight
)


# --------------------------------------------------
# DISPLAY RESULTS
# --------------------------------------------------

print("\nComponent Scores")
print("----------------")
print("Heat Impact:", round(heat_score, 2))
print("Rainfall Impact:", round(rainfall_score, 2))
print("Air Quality Impact:", round(air_quality_score, 2))
print("Dryness Impact:", round(dryness_score, 2))


print("\nProject-Defined Weights")
print("----------------------")
print("Heat:", heat_weight)
print("Rainfall:", rainfall_weight)
print("Air Quality:", air_quality_weight)
print("Dryness:", dryness_weight)


print("\nClimate Impact Index")
print("-------------------")
print(
    round(climate_impact_index, 2),
    "/ 100"
)


print("\nNote:")
print(
    "Climate Impact Index is a project-defined "
    "composite indicator and is not an official climate index."
)