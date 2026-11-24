import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Kolkata")

ROUTINE_SCHEDULE = [
    {
        "time_str": "9:00 am",
        "time": (9, 0),
        "title": "Wake up, 500 ml water",
        "notes": "Weigh yourself on Mondays only",
        "calories": 0,
    },
    {
        "time_str": "9:30 am",
        "time": (9, 30),
        "title": "Breakfast (~700 kcal)",
        "notes": "4 eggs or 100 g paneer bhurji, 3 rotis or 2 toast slices, a glass of milk",
        "calories": 700,
    },
    {
        "time_str": "12:00 pm",
        "time": (12, 0),
        "title": "Shake (~900 kcal)",
        "notes": "Milk, 2 bananas, 2 tbsp peanut butter, 50 g oats, 1 scoop whey, 5 g creatine. Never skip the shake!",
        "calories": 900,
    },
    {
        "time_str": "2:00 pm",
        "time": (14, 0),
        "title": "Lunch (~700 kcal)",
        "notes": "Rice, dal, chicken or rajma, curd",
        "calories": 700,
    },
    {
        "time_str": "5:00 pm",
        "time": (17, 0),
        "title": "Pre-workout snack (~300 kcal)",
        "notes": "Banana, peanut butter toast, a handful of nuts",
        "calories": 300,
    },
    {
        "time_str": "6:00–7:15 pm",
        "time": (18, 0),
        "title": "Gym / Workout",
        "notes": "4-day split (Mon, Tue, Thu, Fri); Rest on Wed, Sat, Sun",
        "calories": 0,
    },
    {
        "time_str": "7:30 pm",
        "time": (19, 30),
        "title": "Post-workout (~250 kcal)",
        "notes": "Glass of milk or curd with fruit",
        "calories": 250,
    },
    {
        "time_str": "9:00 pm",
        "time": (21, 0),
        "title": "Dinner (~700 kcal)",
        "notes": "4 rotis, chicken or paneer curry, sabzi",
        "calories": 700,
    },
    {
        "time_str": "11:30 pm",
        "time": (23, 30),
        "title": "Before bed (~200 kcal)",
        "notes": "Glass of milk or a handful of nuts",
        "calories": 200,
    },
    {
        "time_str": "12:30 am",
        "time": (0, 30),
        "title": "Sleep",
        "notes": "Lights out by 12:30 to get about 8.5 hours",
        "calories": 0,
    },
]

WORKOUT_SPLITS = {
    "Monday": {
        "focus": "Upper body",
        "exercises": [
            "Bench press (3–4 sets × 6–12 reps)",
            "Barbell row (3–4 sets × 6–12 reps)",
            "Overhead press (3–4 sets × 6–12 reps)",
            "Lat pulldown (3–4 sets × 6–12 reps)",
            "Bicep curl (3–4 sets × 6–12 reps)",
            "Tricep pushdown (3–4 sets × 6–12 reps)",
        ],
        "tip": "Progressive overload: add 2.5 kg or 1 rep from last week. Log your numbers!",
    },
    "Tuesday": {
        "focus": "Lower body",
        "exercises": [
            "Squat (3–4 sets × 6–12 reps)",
            "Romanian deadlift (3–4 sets × 6–12 reps)",
            "Leg press (3–4 sets × 6–12 reps)",
            "Lunges (3–4 sets × 6–12 reps)",
            "Calf raises (3–4 sets × 6–12 reps)",
            "Plank (3 sets × hold 45–60s)",
        ],
        "tip": "Form first! Control the descent on squats and keep back neutral on RDL.",
    },
    "Wednesday": {
        "focus": "Rest & Active Recovery",
        "exercises": [
            "A relaxing 20–30 minute walk",
            "Light stretching / mobility",
        ],
        "tip": "Rest days still need the surplus! Keep eating the full 3,200–3,300 kcal.",
    },
    "Thursday": {
        "focus": "Upper body",
        "exercises": [
            "Incline dumbbell press (3–4 sets × 6–12 reps)",
            "Pull-ups (assisted if needed, 3–4 sets × 6–12 reps)",
            "Seated row (3–4 sets × 6–12 reps)",
            "Lateral raises (3–4 sets × 10–15 reps)",
            "Hammer curl (3–4 sets × 6–12 reps)",
            "Dips (3–4 sets × 6–12 reps)",
        ],
        "tip": "Target upper chest on incline press. Strict form on lateral raises.",
    },
    "Friday": {
        "focus": "Lower body & Core",
        "exercises": [
            "Deadlift (3–4 sets × 5–8 reps)",
            "Leg press (3–4 sets × 6–12 reps)",
            "Leg curl (3–4 sets × 8–12 reps)",
            "Step-ups (3–4 sets × 8–12 reps each leg)",
            "Calf raises (3–4 sets × 12–15 reps)",
            "Hanging leg raise (3 sets × 10–15 reps)",
        ],
        "tip": "Deadlift form is paramount — engage lats, push floor away through heels.",
    },
    "Saturday": {
        "focus": "Rest & Recovery",
        "exercises": ["Full rest day. Light walking or mobility optional."],
        "tip": "Keep eating the same! Muscle protein synthesis peaks during rest.",
    },
    "Sunday": {
        "focus": "Rest & Recovery",
        "exercises": ["Full rest day. Recharge for the week ahead."],
        "tip": "Get prepared for Monday weigh-in tomorrow morning!",
    },
}

RULES = [
    "🔥 *Progressive Overload:* Add 2.5 kg or 1 rep each week. Log your workouts.",
    "🛡️ *Form First:* For the first 2 weeks, prioritize movement quality over heavy weight.",
    "🥤 *Never Skip the Shake:* It is the easiest 900 kcal of your day.",
    "⚖️ *Track Weekly:* Target +0.5 to 0.75 kg per week. If stalled for 2 weeks, add 1 roti + spoon of ghee to lunch & dinner.",
    "💧 *Hydration:* Drink 3–4 litres of water every single day.",
    "🎯 *Total Targets:* ~3,200–3,300 kcal | 125–135 g protein | ~8.5 hrs sleep.",
]

def get_today_workout(day_name: str = None) -> str:
    if not day_name:
        day_name = datetime.datetime.now(TZ).strftime("%A")
    split = WORKOUT_SPLITS.get(day_name, WORKOUT_SPLITS["Wednesday"])
    
    lines = [
        f"🏋️‍♂️ *{day_name} Workout Focus:* {split['focus']}\n",
        "*Exercises (3–4 sets × 6–12 reps):*",
    ]
    for idx, ex in enumerate(split["exercises"], 1):
        lines.append(f"{idx}. {ex}")
        
    lines.append(f"\n💡 *Coach Tip:* _{split['tip']}_")
    return "\n".join(lines)

def get_daily_routine_summary() -> str:
    lines = [
        "📋 *Daily Routine & Nutrition Plan (3,200–3,300 kcal | 125–135g Protein):*\n",
        "| Time | What | Details |",
        "|---|---|---|",
    ]
    for s in ROUTINE_SCHEDULE:
        lines.append(f"• *{s['time_str']}* — *{s['title']}*\n  _{s['notes']}_")
        
    lines.append("\n📌 *Core Rules:*")
    for r in RULES:
        lines.append(f"• {r}")
        
    return "\n".join(lines)

def build_slot_message(slot_id: str) -> str:
    now = datetime.datetime.now(TZ)
    day_name = now.strftime("%A")
    is_monday = now.weekday() == 0

    if slot_id == "wake_up":
        monday_extra = "\n\n⚖️ *Monday Morning Weigh-in Reminder!* Step on the scale before eating and log your weight. Target: +0.5 to 0.75 kg/week!" if is_monday else ""
        return (
            "🌅 *Good morning, Ansh!* (09:00 AM)\n\n"
            "💧 *Step 1:* Drink **500 ml water** right now to kickstart hydration and digestion."
            f"{monday_extra}\n\n"
            "Daily goal: 3–4 litres of water through the day. Let's make today count! 💪"
        )
        
    elif slot_id == "breakfast":
        return (
            "🍳 *Breakfast Time! (~700 kcal)* (09:30 AM)\n\n"
            "• 4 eggs OR 100 g paneer bhurji\n"
            "• 3 rotis OR 2 slices of toast\n"
            "• 1 glass of milk\n\n"
            "Fuel up your body for a high-energy morning! 🚀"
        )
        
    elif slot_id == "shake":
        return (
            "🥤 *Power Shake Alert! (~900 kcal)* (12:00 PM)\n\n"
            "⚡ *Never skip the shake — easiest 900 kcal of the day!*\n"
            "• Milk\n"
            "• 2 Bananas\n"
            "• 2 tbsp Peanut butter\n"
            "• 50 g Oats\n"
            "• 1 scoop Whey protein\n"
            "• 5 g Creatine\n\n"
            "Chug it down and keep crushing your surplus! 🔥"
        )
        
    elif slot_id == "lunch":
        return (
            "🍛 *Lunch Time! (~700 kcal)* (02:00 PM)\n\n"
            "• Rice + Dal\n"
            "• Chicken OR Rajma\n"
            "• Curd\n\n"
            "💧 *Hydration Check:* Make sure you've finished at least 1.5–2L of water by now!"
        )
        
    elif slot_id == "pre_workout":
        return (
            "⚡ *Pre-Workout Snack (~300 kcal)* (05:00 PM)\n\n"
            "• 1 Banana\n"
            "• Peanut butter toast\n"
            "• Handful of nuts\n\n"
            "Gym starts in 1 hour (6:00 PM). Get your gear ready! 🏋️‍♂️"
        )
        
    elif slot_id == "gym":
        workout_text = get_today_workout(day_name)
        return (
            f"🥊 *Gym Session (6:00–7:15 PM)*\n\n"
            f"{workout_text}\n\n"
            "Remember: Form first, push through the last rep, and log your weights! 💯"
        )
        
    elif slot_id == "post_workout":
        return (
            "🥛 *Post-Workout Nutrition (~250 kcal)* (07:30 PM)\n\n"
            "• 1 glass of milk OR curd with fresh fruit\n\n"
            "Great work finishing the session! Rehydrate and let the recovery begin. 👏"
        )
        
    elif slot_id == "dinner":
        return (
            "🍽️ *Dinner Time! (~700 kcal)* (09:00 PM)\n\n"
            "• 4 rotis\n"
            "• Chicken OR Paneer curry\n"
            "• Sabzi\n\n"
            "You are closing in on today's 3,200–3,300 kcal target! 🎯"
        )
        
    elif slot_id == "before_bed":
        return (
            "🌙 *Pre-Bed Snack (~200 kcal)* (11:30 PM)\n\n"
            "• 1 glass of warm milk OR a handful of nuts\n\n"
            "Time to start winding down. Disconnect from screens to prepare for deep recovery. 🧘"
        )
        
    elif slot_id == "sleep":
        return (
            "😴 *Lights Out! Sleep Time (12:30 AM)*\n\n"
            "Aim for 8.5 hours of uninterrupted sleep for maximum muscle recovery and mental clarity.\n\n"
            "Good night, Ansh! See you at 9:00 AM! 💤"
        )
        
    return ""
