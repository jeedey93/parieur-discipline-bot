import os
from datetime import date
from dotenv import load_dotenv
from google import genai

load_dotenv()

def compare_predictions(morning_file, noon_file, output_file):
    """
    Compare morning (7am) and noon (12pm) NHL predictions and generate a combined analysis.
    """
    api_key = os.environ["GOOGLE_API_KEY"]
    client = genai.Client(api_key=api_key)

    # Read both prediction files
    try:
        with open(morning_file, "r", encoding="utf-8") as f:
            morning_predictions = f.read()
    except FileNotFoundError:
        print(f"Morning predictions file not found: {morning_file}")
        return

    try:
        with open(noon_file, "r", encoding="utf-8") as f:
            noon_predictions = f.read()
    except FileNotFoundError:
        print(f"Noon predictions file not found: {noon_file}")
        return

    # Create comparison prompt
    comparison_prompt = f"""You are a sports betting analyst comparing two NHL prediction reports from the same day at different times (morning and noon).

MORNING PREDICTIONS (7:00 AM):
{morning_predictions}

---

NOON PREDICTIONS (12:00 PM):
{noon_predictions}

---

ANALYSIS TASK:
1. Identify which plays appeared in both reports (consistency)
2. Identify which plays were added/removed between reports (line movement impact)
3. Identify confidence level changes for the same plays
4. Identify odds changes that affected recommendations
5. Provide a unified final recommendation list that:
   - Prioritizes plays that appeared in both reports (stronger conviction)
   - Includes only high/medium confidence plays
   - Maximum 5 total plays
   - Ranked by confidence %
   - Show the "Bet of the Day" first

For each play in the output, do the following:
- If the play appeared in both reports, add a single explicit line before the justification, summarizing the change from morning to noon (e.g., 'Confidence increased due to line movement', 'Odds improved and confidence increased', or 'No change from morning to noon').
- If the play was added or removed at noon, add a line such as 'New play added at noon based on updated odds' or 'Removed at noon due to odds movement'.
- After this line, always include the original justification/reasoning from the noon report for that play, without changing or summarizing it.
- Do not rewrite or paraphrase the original justification; keep it as-is from the noon report.

Format the output similarly to your original report:

🏆 **BET OF THE DAY**
[Best play across both reports]

**Other Recommended Plays**
[Remaining plays]

Include a brief note about changes from morning to noon for each play (as above), but always keep the original noon justification for each play.
"""

    try:
        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=comparison_prompt,
        )
        combined_analysis = response.text.strip()

        # Write combined analysis to output file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(combined_analysis)

        print(f"✅ Combined analysis saved to: {output_file}")
        print("\n" + combined_analysis)

        return combined_analysis

    except Exception as e:
        if "RESOURCE_EXHAUSTED" in str(e) or "quota" in str(e):
            print("AI analysis skipped: Gemini API quota exceeded.")
        else:
            raise


def main():
    """Main function to compare morning and noon NHL predictions."""
    today_str = date.today().isoformat()
    predictions_folder = os.path.join("predictions", "nhl")

    # Define temp file paths
    morning_file = os.path.join(predictions_folder, f"nhl_daily_predictions_{today_str}_7am.txt")
    noon_file = os.path.join(predictions_folder, f"nhl_daily_predictions_{today_str}_12pm.txt")
    output_file = os.path.join(predictions_folder, f"nhl_daily_predictions_{today_str}.txt")

    # Check if both files exist
    if not os.path.exists(morning_file):
        print(f"⚠️  Morning predictions file not found: {morning_file}")
        return

    if not os.path.exists(noon_file):
        print(f"⚠️  Noon predictions file not found: {noon_file}")
        return

    print(f"Comparing NHL predictions from {today_str}...")
    print(f"Morning file: {morning_file}")
    print(f"Noon file: {noon_file}")

    # Run comparison
    compare_predictions(morning_file, noon_file, output_file)

    # Delete temp files after successful comparison
    for temp_file in [morning_file, noon_file]:
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                print(f"✅ Deleted temp file: {temp_file}")
            else:
                print(f"⚠️  Temp file not found for deletion: {temp_file}")
        except Exception as e:
            print(f"⚠️  Could not delete temp file {temp_file}: {e}")

if __name__ == "__main__":
    main()

