import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ── O*NET Soft Skills (categorized) ──────────────────────────────────────────
ONET_SOFT_SKILLS = {
    "Social Skills": [
        "Coordination",
        "Instructing",
        "Negotiation",
        "Persuasion",
        "Service Orientation",
        "Social Perceptiveness",
    ],
    "Thinking Skills": [
        "Active Learning",
        "Active Listening",
        "Complex Problem Solving",
        "Critical Thinking",
        "Judgment and Decision Making",
        "Learning Strategies",
        "Monitoring",
        "Time Management",
    ],
}

# Reverse lookup: skill name → category
SKILL_TO_CATEGORY = {
    skill: cat for cat, skills in ONET_SOFT_SKILLS.items() for skill in skills
}


# ── Helper: call Nebius API ──────────────────────────────────────────────────
def generate_questions(skill_name: str, job_Description: str) -> list[dict]:
    """Call the Nebius-hosted Qwen model and return a list of 5 question dicts."""

    client = OpenAI(
        base_url="https://api.tokenfactory.nebius.com/v1/",
        api_key=os.environ.get("NEBIUS_API_KEY"),
    )

    category = SKILL_TO_CATEGORY.get(skill_name, "")

    system_prompt = f"""You are an expert assessment designer specializing in O*NET workplace competencies.

Your task: Create exactly 5 SCENARIO-BASED multiple-choice questions that assess the soft skill described below,
tailored specifically to the job description provided.

Job Description: {job_Description}
Skill: {skill_name}
Category: {category}

CONTEXT — O*NET Importance & Level:
- Each soft skill has an "Importance" score (0–100) indicating how critical it is for a given job.
- Each soft skill has a "Level" score (0–100) indicating how much proficiency is required.
- Different jobs have very different scores. For example, Negotiation may be Importance 70 / Level 60
  for lawyers but Importance 30 / Level 25 for lab technicians.
- You must consider how important and how advanced this skill is for the given job description and adjust the
  difficulty and depth of the scenarios accordingly. Higher importance/level → harder, more nuanced scenarios.

RULES:
1. EVERY question MUST be a realistic workplace scenario specific to the job description "{job_Description}".
   Start each question with a concrete situation relevant to that job.
2. Do NOT ask theoretical, definition-based, or textbook-style questions. Only real-world scenarios.
3. Each question must have exactly 4 options labeled A, B, C, D.
4. Exactly one option is correct.
5. Include a brief explanation of why the correct answer is best.
6. Questions should range from easy to difficult.

You MUST respond with ONLY a valid JSON array (no markdown, no extra text).
Each element must have this exact schema:
{{
  "question": "...",
  "options": {{
    "A": "...",
    "B": "...",
    "C": "...",
    "D": "..."
  }},
  "correct": "A" | "B" | "C" | "D",
  "explanation": "..."
}}
"""

    response = client.chat.completions.create(
        model="Qwen/Qwen2.5-Coder-7B-fast",
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Generate 5 assessment questions for the O*NET soft skill: {skill_name}",
                    }
                ],
            },
        ],
    )

    raw = response.choices[0].message.content.strip()

    # Strip possible markdown fences
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]
    raw = raw.strip()

    # Extract the JSON array
    match = re.search(r'\[.*\]', raw, re.DOTALL)
    if match:
        raw = match.group(0)

    decoder = json.JSONDecoder()
    result, _ = decoder.raw_decode(raw)
    return result


# ── CLI Interface ────────────────────────────────────────────────────────────
def display_header():
    print("\n" + "=" * 60)
    print("   🎯  O*NET Soft Skills Assessment")
    print("   Powered by O*NET Standards • AI-Generated Scenarios")
    print("=" * 60)


def display_skills_menu():
    print("\n📋 Available Soft Skills:\n")
    all_skills = []
    for category, skills in ONET_SOFT_SKILLS.items():
        print(f"  ── {category} ──")
        for skill in skills:
            all_skills.append(skill)
            print(f"    {len(all_skills):>2}. {skill}")
        print()
    return all_skills


def run_assessment():
    display_header()

    # Get job description
    print("\n🏢 Enter your Job Description:")
    job_desc = input("   > ").strip()
    if not job_desc:
        print("❌ Job description cannot be empty.")
        return

    # Show skills and get selection
    all_skills = display_skills_menu()

    print("🎯 Enter the number of the skill you want to assess:")
    try:
        choice = int(input("   > ").strip())
        if choice < 1 or choice > len(all_skills):
            print(f"❌ Please enter a number between 1 and {len(all_skills)}.")
            return
    except ValueError:
        print("❌ Invalid input. Please enter a number.")
        return

    selected_skill = all_skills[choice - 1]
    category = SKILL_TO_CATEGORY[selected_skill]

    print(f"\n✅ Selected: {selected_skill} ({category})")
    print(f"   Job: {job_desc}")
    print("\n⏳ Generating your assessment...\n")

    # Generate questions
    try:
        questions = generate_questions(selected_skill, job_desc)
    except Exception as e:
        print(f"❌ Failed to generate questions: {e}")
        return

    # Run the quiz
    print("=" * 60)
    print(f"   📝 Assessment: {selected_skill}  ·  🏢 {job_desc}")
    print("=" * 60)

    answers = []
    for i, q in enumerate(questions):
        print(f"\n┌─ Q{i + 1} {'─' * 50}")
        print(f"│  {q['question']}")
        print("│")
        for letter, text in q["options"].items():
            print(f"│   {letter}. {text}")
        print("└" + "─" * 55)

        while True:
            ans = input(f"   Your answer (A/B/C/D): ").strip().upper()
            if ans in ("A", "B", "C", "D"):
                answers.append(ans)
                break
            print("   ⚠️  Please enter A, B, C, or D.")

    # Scoring
    score = 0
    print("\n" + "=" * 60)
    print("   📊 Results")
    print("=" * 60)

    for i, q in enumerate(questions):
        correct = q["correct"]
        user_ans = answers[i]
        is_correct = user_ans == correct

        if is_correct:
            score += 1
            mark = "✅ Correct"
        else:
            mark = f"❌ Incorrect (Correct: {correct})"

        print(f"\n  Q{i + 1}: {mark}")
        print(f"      Your answer: {user_ans}")
        print(f"      Explanation: {q.get('explanation', 'N/A')}")

    # Final score
    pct = score / len(questions) * 100
    print("\n" + "─" * 60)
    if pct == 100:
        emoji = "🏆"
    elif pct >= 60:
        emoji = "👍"
    else:
        emoji = "💪"

    print(f"\n   {emoji}  Score: {score}/{len(questions)} ({pct:.0f}%)")
    print(f"   Skill assessed: {selected_skill}")
    print(f"   Job description: {job_desc}")
    print("─" * 60 + "\n")


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    run_assessment()
