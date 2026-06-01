from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.secret_key = "supersecretkey_change_in_production"

# Load your Clarifai API key
CLARIFAI_API_KEY = "5509618baed64038b6b697351e7f1517"

def get_food_model():
    """Initialize Clarifai model with API key"""
    os.environ['CLARIFAI_PAT'] = CLARIFAI_API_KEY
    from clarifai.client.model import Model
    model = Model(url="https://clarifai.com/clarifai/main/models/food-item-recognition")
    return model

DB_PATH = 'database.db'
UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ------------------- Comprehensive Calorie Database by Category -------------------
SOUTH_INDIAN_FOODS = {
    "dosa": {"calories": 168, "serving": "1 piece", "protein": 4, "carbs": 28, "fat": 4},
    "masala dosa": {"calories": 250, "serving": "1 piece", "protein": 6, "carbs": 40, "fat": 8},
    "idli": {"calories": 39, "serving": "1 piece", "protein": 2, "carbs": 8, "fat": 0.5},
    "vada": {"calories": 90, "serving": "1 piece", "protein": 3, "carbs": 12, "fat": 4},
    "medu vada": {"calories": 95, "serving": "1 piece", "protein": 3, "carbs": 13, "fat": 4},
    "upma": {"calories": 180, "serving": "1 cup", "protein": 5, "carbs": 30, "fat": 5},
    "pongal": {"calories": 220, "serving": "1 cup", "protein": 6, "carbs": 35, "fat": 7},
    "sambar": {"calories": 120, "serving": "1 cup", "protein": 4, "carbs": 18, "fat": 4},
    "rasam": {"calories": 50, "serving": "1 cup", "protein": 2, "carbs": 8, "fat": 2},
    "uttapam": {"calories": 150, "serving": "1 piece", "protein": 5, "carbs": 25, "fat": 4},
    "appam": {"calories": 120, "serving": "1 piece", "protein": 2, "carbs": 24, "fat": 2},
    "puttu": {"calories": 130, "serving": "1 cup", "protein": 3, "carbs": 26, "fat": 2},
    "pesarattu": {"calories": 200, "serving": "1 piece", "protein": 8, "carbs": 32, "fat": 5},
    "bonda": {"calories": 85, "serving": "1 piece", "protein": 2, "carbs": 12, "fat": 3},
    "coconut chutney": {"calories": 80, "serving": "2 tbsp", "protein": 1, "carbs": 6, "fat": 6},
}

NORTH_INDIAN_FOODS = {
    "roti": {"calories": 120, "serving": "1 piece", "protein": 3, "carbs": 22, "fat": 3},
    "chapati": {"calories": 120, "serving": "1 piece", "protein": 3, "carbs": 22, "fat": 3},
    "naan": {"calories": 262, "serving": "1 piece", "protein": 8, "carbs": 45, "fat": 5},
    "paratha": {"calories": 200, "serving": "1 piece", "protein": 4, "carbs": 28, "fat": 8},
    "aloo paratha": {"calories": 250, "serving": "1 piece", "protein": 5, "carbs": 35, "fat": 10},
    "paneer butter masala": {"calories": 350, "serving": "1 cup", "protein": 14, "carbs": 15, "fat": 26},
    "dal makhani": {"calories": 280, "serving": "1 cup", "protein": 12, "carbs": 30, "fat": 12},
    "chole": {"calories": 240, "serving": "1 cup", "protein": 10, "carbs": 35, "fat": 6},
    "rajma": {"calories": 220, "serving": "1 cup", "protein": 11, "carbs": 32, "fat": 5},
    "biryani": {"calories": 500, "serving": "1 plate", "protein": 18, "carbs": 65, "fat": 18},
    "butter chicken": {"calories": 400, "serving": "1 cup", "protein": 25, "carbs": 12, "fat": 28},
    "palak paneer": {"calories": 280, "serving": "1 cup", "protein": 12, "carbs": 10, "fat": 20},
    "kadai paneer": {"calories": 320, "serving": "1 cup", "protein": 14, "carbs": 12, "fat": 24},
    "dal tadka": {"calories": 180, "serving": "1 cup", "protein": 10, "carbs": 28, "fat": 4},
    "samosa": {"calories": 150, "serving": "1 piece", "protein": 3, "carbs": 18, "fat": 7},
    "kachori": {"calories": 180, "serving": "1 piece", "protein": 4, "carbs": 22, "fat": 8},
}

CHINESE_FOODS = {
    "fried rice": {"calories": 333, "serving": "1 plate", "protein": 8, "carbs": 55, "fat": 10},
    "noodles": {"calories": 380, "serving": "1 plate", "protein": 10, "carbs": 60, "fat": 12},
    "hakka noodles": {"calories": 350, "serving": "1 plate", "protein": 9, "carbs": 58, "fat": 10},
    "schezwan rice": {"calories": 400, "serving": "1 plate", "protein": 9, "carbs": 62, "fat": 14},
    "schezwan noodles": {"calories": 420, "serving": "1 plate", "protein": 11, "carbs": 64, "fat": 15},
    "manchurian": {"calories": 280, "serving": "1 cup", "protein": 6, "carbs": 35, "fat": 12},
    "gobi manchurian": {"calories": 260, "serving": "1 cup", "protein": 5, "carbs": 32, "fat": 11},
    "spring roll": {"calories": 140, "serving": "1 piece", "protein": 3, "carbs": 18, "fat": 6},
    "momos": {"calories": 180, "serving": "5 pieces", "protein": 7, "carbs": 24, "fat": 6},
    "chowmein": {"calories": 340, "serving": "1 plate", "protein": 9, "carbs": 55, "fat": 10},
    "sweet and sour": {"calories": 320, "serving": "1 cup", "protein": 12, "carbs": 42, "fat": 10},
}

ITALIAN_FOODS = {
    "pizza": {"calories": 266, "serving": "1 slice", "protein": 11, "carbs": 33, "fat": 10},
    "margherita pizza": {"calories": 250, "serving": "1 slice", "protein": 10, "carbs": 32, "fat": 9},
    "pepperoni pizza": {"calories": 300, "serving": "1 slice", "protein": 13, "carbs": 34, "fat": 13},
    "veggie pizza": {"calories": 235, "serving": "1 slice", "protein": 9, "carbs": 31, "fat": 8},
    "pasta": {"calories": 350, "serving": "1 plate", "protein": 12, "carbs": 58, "fat": 8},
    "spaghetti": {"calories": 220, "serving": "1 cup", "protein": 8, "carbs": 43, "fat": 1.5},
    "lasagna": {"calories": 380, "serving": "1 piece", "protein": 18, "carbs": 35, "fat": 18},
    "risotto": {"calories": 320, "serving": "1 cup", "protein": 9, "carbs": 52, "fat": 8},
    "carbonara": {"calories": 400, "serving": "1 plate", "protein": 16, "carbs": 48, "fat": 16},
    "alfredo pasta": {"calories": 420, "serving": "1 plate", "protein": 14, "carbs": 50, "fat": 18},
}

DESSERTS = {
    "gulab jamun": {"calories": 150, "serving": "1 piece", "protein": 2, "carbs": 28, "fat": 4},
    "rasgulla": {"calories": 106, "serving": "1 piece", "protein": 3, "carbs": 20, "fat": 2},
    "jalebi": {"calories": 150, "serving": "1 piece", "protein": 1, "carbs": 30, "fat": 3},
    "laddu": {"calories": 180, "serving": "1 piece", "protein": 3, "carbs": 28, "fat": 6},
    "barfi": {"calories": 170, "serving": "1 piece", "protein": 4, "carbs": 24, "fat": 7},
    "ice cream": {"calories": 137, "serving": "1 scoop", "protein": 2, "carbs": 16, "fat": 7},
    "cake": {"calories": 320, "serving": "1 slice", "protein": 4, "carbs": 45, "fat": 14},
    "chocolate cake": {"calories": 350, "serving": "1 slice", "protein": 5, "carbs": 48, "fat": 16},
    "cheesecake": {"calories": 400, "serving": "1 slice", "protein": 6, "carbs": 35, "fat": 26},
    "brownie": {"calories": 243, "serving": "1 piece", "protein": 3, "carbs": 35, "fat": 11},
    "kheer": {"calories": 200, "serving": "1 cup", "protein": 5, "carbs": 32, "fat": 6},
    "halwa": {"calories": 220, "serving": "1 cup", "protein": 3, "carbs": 38, "fat": 8},
}

DRINKS = {
    "coffee": {"calories": 2, "serving": "1 cup", "protein": 0, "carbs": 0, "fat": 0},
    "tea": {"calories": 2, "serving": "1 cup", "protein": 0, "carbs": 0, "fat": 0},
    "milk tea": {"calories": 80, "serving": "1 cup", "protein": 4, "carbs": 10, "fat": 3},
    "coffee latte": {"calories": 120, "serving": "1 cup", "protein": 6, "carbs": 12, "fat": 5},
    "juice": {"calories": 110, "serving": "1 glass", "protein": 1, "carbs": 26, "fat": 0},
    "smoothie": {"calories": 150, "serving": "1 glass", "protein": 4, "carbs": 30, "fat": 2},
    "milkshake": {"calories": 350, "serving": "1 glass", "protein": 8, "carbs": 50, "fat": 12},
    "soda": {"calories": 140, "serving": "1 can", "protein": 0, "carbs": 39, "fat": 0},
    "lassi": {"calories": 160, "serving": "1 glass", "protein": 6, "carbs": 24, "fat": 4},
    "coconut water": {"calories": 45, "serving": "1 glass", "protein": 1, "carbs": 9, "fat": 0},
}

# Combined database
CALORIE_DATABASE = {
    "South Indian": SOUTH_INDIAN_FOODS,
    "North Indian": NORTH_INDIAN_FOODS,
    "Chinese": CHINESE_FOODS,
    "Italian": ITALIAN_FOODS,
    "Pizza": ITALIAN_FOODS,
    "Dessert": DESSERTS,
    "Drinks": DRINKS,
}

def get_calorie_info(food_name, category_hint=None):
    """Get calorie information for a food item"""
    food_name_lower = food_name.lower()
    
    if category_hint and category_hint in CALORIE_DATABASE:
        db = CALORIE_DATABASE[category_hint]
        if food_name_lower in db:
            info = db[food_name_lower].copy()
            info['category'] = category_hint
            return info
        for key in db:
            if key in food_name_lower or food_name_lower in key:
                info = db[key].copy()
                info['category'] = category_hint
                return info
    
    for category, db in CALORIE_DATABASE.items():
        if food_name_lower in db:
            info = db[food_name_lower].copy()
            info['category'] = category
            return info
        for key in db:
            if key in food_name_lower or food_name_lower in key:
                info = db[key].copy()
                info['category'] = category
                return info
    
    return {"calories": 200, "serving": "1 serving", "category": "Other", "protein": 5, "carbs": 30, "fat": 5}

# ------------------- Database Setup -------------------
def init_db():
    first = not os.path.exists(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            dob TEXT,
            weight REAL,
            height REAL,
            goal TEXT,
            gender TEXT,
            health_conditions TEXT,
            phone TEXT,
            is_premium INTEGER DEFAULT 0,
            premium_expiry TEXT,
            free_scans_used INTEGER DEFAULT 0,
            water_reminder_time TEXT DEFAULT '09:00',
            sleep_reminder_time TEXT DEFAULT '22:00',
            body_type TEXT,
            fitness_goal TEXT,
            activity_level TEXT,
            survey_score INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS water_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount_ml INTEGER,
        entry_date TEXT,
        entry_time TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS sleep_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        sleep_hours REAL,
        entry_date TEXT,
        note TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS workout_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        activity TEXT,
        duration_min INTEGER,
        calories_burnt INTEGER,
        entry_date TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS food_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        food_name TEXT,
        calories INTEGER,
        category TEXT,
        entry_date TEXT,
        entry_time TEXT,
        image_path TEXT,
        meal_type TEXT,
        protein REAL,
        carbs REAL,
        fat REAL,
        FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS weight_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        weight REAL,
        entry_date TEXT,
        entry_time TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        message TEXT,
        type TEXT,
        is_read INTEGER DEFAULT 0,
        created_at TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS payment_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        plan_type TEXT,
        payment_status TEXT,
        transaction_id TEXT,
        payment_date TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    conn.commit()
    conn.close()
    if first:
        print("✅ Database created at", DB_PATH)

init_db()

# ------------------- Helper Functions -------------------
def get_db_conn():
    return sqlite3.connect(DB_PATH)

# ------------------- Migrate Existing Database -------------------
def migrate_db():
    """Add new columns to existing database"""
    conn = get_db_conn()
    c = conn.cursor()
    
    # Get existing columns
    c.execute("PRAGMA table_info(users)")
    existing_columns = [col[1] for col in c.fetchall()]
    
    # Add missing columns
    new_columns = {
        'gender': 'TEXT',
        'health_conditions': 'TEXT',
        'phone': 'TEXT',
        'is_premium': 'INTEGER DEFAULT 0',
        'premium_expiry': 'TEXT',
        'free_scans_used': 'INTEGER DEFAULT 0',
        'water_reminder_time': "TEXT DEFAULT '09:00'",
        'sleep_reminder_time': "TEXT DEFAULT '22:00'",
        'body_type': 'TEXT',
        'fitness_goal': 'TEXT',
        'activity_level': 'TEXT',
        'survey_score': 'INTEGER'
    }
    
    for col_name, col_type in new_columns.items():
        if col_name not in existing_columns:
            try:
                c.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
                print(f"✅ Added column: {col_name}")
            except sqlite3.OperationalError as e:
                print(f"Column {col_name} might already exist: {e}")
    
    conn.commit()
    conn.close()
    print("✅ Database migration completed!")

migrate_db()

def calculate_bmi(weight, height_cm):
    try:
        if weight is None or height_cm is None:
            return None
        h = float(height_cm) / 100.0
        if h <= 0: 
            return None
        bmi = float(weight) / (h * h)
        return round(bmi, 2)
    except Exception:
        return None

def check_premium_access(user_id):
    """Check if user has premium access or free scans remaining"""
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT is_premium, premium_expiry, free_scans_used FROM users WHERE id=?", (user_id,))
    user = c.fetchone()
    conn.close()
    
    if not user:
        return False, "User not found"
    
    is_premium, expiry, free_used = user
    
    if is_premium and expiry:
        try:
            expiry_date = datetime.strptime(expiry, '%Y-%m-%d').date()
            if expiry_date >= date.today():
                return True, "premium"
        except:
            pass
    
    if free_used < 3:
        return True, "free"
    
    return False, "limit_reached"

def add_notification(user_id, message, notif_type="info"):
    """Add a notification for user"""
    conn = get_db_conn()
    c = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute("INSERT INTO notifications (user_id, message, type, created_at) VALUES (?, ?, ?, ?)",
              (user_id, message, notif_type, now))
    conn.commit()
    conn.close()

def send_email_notification(user_email, subject, message):
    """Send email notification - configure with your email service"""
    try:
        print(f"📧 Email to {user_email}: {subject} - {message}")
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

def check_calorie_threshold(user_id, calories_consumed, calories_burnt):
    """Check if user needs workout notification"""
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT weight, height, gender FROM users WHERE id=?", (user_id,))
    user = c.fetchone()
    conn.close()
    
    if not user or not user[0] or not user[1]:
        return None
    
    weight, height, gender = user
    bmi = calculate_bmi(weight, height)
    
    if gender == 'Male':
        base_cal = 2500
    elif gender == 'Female':
        base_cal = 2000
    else:
        base_cal = 2200
    
    net_calories = calories_consumed - calories_burnt
    
    if net_calories > base_cal * 1.2:
        msg = f"⚠️ High calorie intake today ({net_calories} kcal)! Consider a workout to balance it out. 💪"
        add_notification(user_id, msg, "warning")
        return msg
    elif bmi and bmi > 25 and net_calories > base_cal:
        msg = f"💡 You've consumed {net_calories} kcal today. A 30-min walk can help! 🚶"
        add_notification(user_id, msg, "info")
        return msg
    
    return None

def sum_today_water(user_id):
    conn = get_db_conn()
    c = conn.cursor()
    today = date.today().isoformat()
    c.execute("SELECT SUM(amount_ml) FROM water_logs WHERE user_id=? AND entry_date=?", (user_id, today))
    s = c.fetchone()[0]
    conn.close()
    return int(s) if s else 0

def last_sleep(user_id):
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT sleep_hours, entry_date FROM sleep_logs WHERE user_id=? ORDER BY entry_date DESC LIMIT 1", (user_id,))
    r = c.fetchone()
    conn.close()
    return r

def sum_today_workout_calories(user_id):
    conn = get_db_conn()
    c = conn.cursor()
    today = date.today().isoformat()
    c.execute("SELECT SUM(calories_burnt) FROM workout_logs WHERE user_id=? AND entry_date=?", (user_id, today))
    s = c.fetchone()[0]
    conn.close()
    return int(s) if s else 0

def sum_today_food_calories(user_id):
    conn = get_db_conn()
    c = conn.cursor()
    today = date.today().isoformat()
    c.execute("SELECT SUM(calories) FROM food_logs WHERE user_id=? AND entry_date=?", (user_id, today))
    s = c.fetchone()[0]
    conn.close()
    return int(s) if s else 0

# =============== NEW HELPERS FOR SURVEY & WORKOUT RECOMMENDATIONS ===============

def infer_body_type_from_answers(a1, a2, a3):
    """Infer body type from Q1-Q3 answers"""
    answers = [a1, a2, a3]
    count_a = answers.count('A')
    count_b = answers.count('B')
    count_c = answers.count('C')

    if count_a >= max(count_b, count_c):
        return "Ectomorph"
    if count_b >= max(count_a, count_c):
        return "Mesomorph"
    return "Endomorph"

def compute_survey_score(body_type, fitness_goal, activity_level, sleep_opt, water_opt):
    """Compute health profile score (0-100)"""
    score = 50

    if activity_level == "Active":
        score += 20
    elif activity_level == "Moderate":
        score += 10
    elif activity_level == "Light":
        score += 5

    if sleep_opt in ("7-8", "8+"):
        score += 15
    elif sleep_opt == "5-6":
        score += 5

    if water_opt in ("2-3L", "3L+"):
        score += 15
    elif water_opt == "1-2L":
        score += 5

    if body_type == "Endomorph" and fitness_goal == "Fat loss":
        score += 5
    if body_type == "Ectomorph" and fitness_goal == "Muscle gain":
        score += 5

    return max(0, min(100, score))

def get_workout_recommendations(user_id, net_calories, target_net):
    """
    Get personalized workout recommendations based on:
    - Body type (Ectomorph/Mesomorph/Endomorph)
    - Fitness goal (Fat loss/Muscle gain/Maintain/Endurance)
    - Actual weight and BMI
    - Health conditions
    - Net calorie status
    """
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("""SELECT gender, body_type, fitness_goal, health_conditions, weight, height 
                 FROM users WHERE id=?""", (user_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        return []

    gender, body_type, fitness_goal, health_conditions, weight, height = row
    health_conditions = (health_conditions or "").lower()
    
    # Calculate BMI for additional personalization
    bmi = calculate_bmi(weight, height) if weight and height else None

    recs = []
    over_target = net_calories > target_net

    # Base daily movement with BMI consideration
    if bmi and bmi > 25:  # Overweight/Obese
        recs.append({
            "title": "⚠️ Brisk Walk (Priority)",
            "detail": f"40–50 min daily (BMI: {bmi} - weight management needed).",
            "reason": "Higher calorie burn needed to reduce weight and improve health."
        })
    elif bmi and bmi < 18.5:  # Underweight
        recs.append({
            "title": "Light Walk",
            "detail": "20–30 min for general fitness (focus on strength, not cardio).",
            "reason": "Preserve energy for muscle-building workouts."
        })
    else:  # Normal weight
        recs.append({
            "title": "Brisk Walk",
            "detail": "30–40 min outdoors or treadmill.",
            "reason": "Improves heart health and helps manage daily calorie balance."
        })

    # Goal-specific logic with weight consideration
    if fitness_goal == "Fat loss":
        # If overweight, emphasize more cardio
        if bmi and bmi > 27:
            recs.append({
                "title": "🔥 High-Intensity Interval Walking",
                "detail": "25–35 min alternating (2 min fast / 1 min slow).",
                "reason": f"Your BMI ({bmi}) suggests focusing on efficient calorie burn."
            })
        else:
            recs.append({
                "title": "Interval Walking / Light Jog",
                "detail": "20–30 min with 1 min fast / 2 min slow.",
                "reason": "Intervals increase calorie burn efficiency."
            })
        
        recs.append({
            "title": "Full-body Strength Training",
            "detail": "3 sessions/week (squats, push-ups, rows, core).",
            "reason": "Strength work preserves muscle while losing fat."
        })
    
    elif fitness_goal == "Muscle gain":
        recs.append({
            "title": "💪 Push–Pull–Legs Split",
            "detail": "45–60 min strength training, 3–4 days/week.",
            "reason": "Focus on compound lifts and progressive overload."
        })
        
        if bmi and bmi > 25:
            recs.append({
                "title": "Light Cardio Post-Workout",
                "detail": "5–10 min walking after weights.",
                "reason": f"Minimal cardio (BMI {bmi}). Focus on eating in surplus for gains."
            })
        else:
            recs.append({
                "title": "Short Low-intensity Cardio",
                "detail": "10–15 min walking after workouts.",
                "reason": "Supports recovery without eating into muscle gain."
            })
    
    elif fitness_goal == "Maintain fitness":
        recs.append({
            "title": "Mixed Cardio + Strength",
            "detail": "30 min moderate cardio + 20 min bodyweight strength, 3–4 days/week.",
            "reason": "Balances heart health and strength."
        })
    
    elif fitness_goal == "Endurance":
        recs.append({
            "title": "Steady-state Cardio",
            "detail": "40–50 min jog/cycle 3–5 days/week.",
            "reason": "Builds aerobic capacity and stamina."
        })

    # Body type tuning with weight awareness
    if body_type == "Endomorph":
        if bmi and bmi > 28:
            recs.append({
                "title": "🔥 Extended Low-impact Cardio",
                "detail": "Cycling or elliptical 50–60 min, 4–5 days/week.",
                "reason": f"Higher body fat (BMI {bmi}) requires sustained calorie burn."
            })
        else:
            recs.append({
                "title": "Low-impact Cardio",
                "detail": "Cycling, elliptical, or brisk walking 40 min.",
                "reason": "Higher cardio volume supports fat loss with less joint stress."
            })
    
    elif body_type == "Ectomorph":
        recs.append({
            "title": "💪 Strength over Cardio",
            "detail": "Focus on weights; limit cardio to 2–3 short sessions/week.",
            "reason": "Prevents excessive calorie burn and supports muscle gain."
        })
    
    elif body_type == "Mesomorph":
        recs.append({
            "title": "⚡ Athletic Conditioning",
            "detail": "Circuits combining strength + short cardio bursts.",
            "reason": "Leverages naturally athletic build for performance."
        })

    # Weight-specific recommendations
    if weight:
        if weight > 80 and bmi and bmi > 27:
            recs.insert(0, {
                "title": "🎯 Weight Loss Priority",
                "detail": f"Current weight {weight}kg. Target 500-750 kcal daily deficit.",
                "reason": f"BMI {bmi} indicates significant weight reduction benefits health."
            })
        elif weight < 50 and body_type == "Ectomorph":
            recs.insert(0, {
                "title": "🍽️ Muscle Building Focus",
                "detail": f"Current weight {weight}kg. Eat in 300-500 kcal surplus.",
                "reason": "Combine strength training with adequate protein intake."
            })

    # Health condition adjustments
    if "diabetes" in health_conditions:
        recs.append({
            "title": "🩺 Post-meal Walking",
            "detail": "10–15 min walk after major meals (breakfast, lunch, dinner).",
            "reason": "Helps with blood sugar control and prevents spikes."
        })
    
    if "joint" in health_conditions or "knee" in health_conditions:
        recs.append({
            "title": "🏊 Joint-friendly Workouts",
            "detail": "Swimming, cycling, yoga, and resistance bands.",
            "reason": "Avoids high-impact stress on joints."
        })
    
    if "pcos" in health_conditions:
        recs.append({
            "title": "⚖️ PCOS-Specific Training",
            "detail": "30–40 min low-impact cardio + 20 min strength, 3–4 days/week.",
            "reason": "Supports hormone balance and weight management."
        })
    
    if "asthma" in health_conditions:
        recs.append({
            "title": "😤 Asthma-Safe Exercise",
            "detail": "Moderate intensity with rest breaks. Avoid very high intensity.",
            "reason": "Reduces risk of breathing difficulty."
        })
    
    if "thyroid" in health_conditions:
        recs.append({
            "title": "⚡ Thyroid-Aware Training",
            "detail": "Moderate cardio + strength, 3–4 days/week. Avoid over-training.",
            "reason": "Prevents metabolic stress on thyroid function."
        })

    # If net calories clearly over target, add specific suggestion
    if over_target:
        extra = net_calories - target_net
        walk_min = max(10, (extra + 4) // 5)
        recs.insert(0, {
            "title": "🔥 Extra Activity Today",
            "detail": f"{walk_min} min brisk walking or light cardio.",
            "reason": f"Helps offset approximately {extra} kcal surplus based on today's intake."
        })

    return recs

# ------------------- Routes -------------------
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip().lower()
        password = generate_password_hash(request.form['password'])
        conn = get_db_conn()
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", (username, email, password))
            conn.commit()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Email already registered. Try logging in.", "danger")
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/add_sample_data')
def add_sample_data():
    """Add sample data for demonstration"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db_conn()
    c = conn.cursor()
    
    for i in range(7):
        day = (date.today() - timedelta(days=i)).isoformat()
        
        c.execute("""INSERT INTO food_logs 
                    (user_id, food_name, calories, category, entry_date, entry_time, protein, carbs, fat) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                 (user_id, "Idli", 120, "South Indian", day, "08:00:00", 4, 24, 1))
        
        c.execute("""INSERT INTO food_logs 
                    (user_id, food_name, calories, category, entry_date, entry_time, protein, carbs, fat) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                 (user_id, "Biryani", 500, "North Indian", day, "13:00:00", 18, 65, 18))
        
        c.execute("""INSERT INTO food_logs 
                    (user_id, food_name, calories, category, entry_date, entry_time, protein, carbs, fat) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                 (user_id, "Roti", 240, "North Indian", day, "20:00:00", 6, 44, 6))
    
    for i in range(7):
        day = (date.today() - timedelta(days=i)).isoformat()
        c.execute("""INSERT INTO workout_logs 
                    (user_id, activity, duration_min, calories_burnt, entry_date) 
                    VALUES (?, ?, ?, ?, ?)""",
                 (user_id, "Running", 30, 300, day))
    
    conn.commit()
    conn.close()
    
    flash("✅ Sample data added for demonstration!", "success")
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        conn = get_db_conn()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=?", (email,))
        user = c.fetchone()
        conn.close()
        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            flash("Welcome back!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials. Try again.", "danger")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully", "info")
    return redirect(url_for('login'))

@app.route('/forgot_password')
def forgot_password():
    return render_template('forgot_password.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    categories = [
        {"slug":"south-indian","name":"South Indian","image":"south_indian.jpg"},
        {"slug":"north-indian","name":"North Indian","image":"north_indian.jpg"},
        {"slug":"italian","name":"Italian","image":"italian.jpg"},
        {"slug":"chinese","name":"Chinese","image":"chinese.jpg"},
        {"slug":"dessert","name":"Dessert","image":"dessert.jpg"},
        {"slug":"pizza","name":"Pizza","image":"pizza.jpg"},
        {"slug":"drinks","name":"Drinks","image":"drinks.jpg"},
    ]

    user_id = session['user_id']
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = c.fetchone()
    
    # Get premium status separately and convert to int
    c.execute("SELECT is_premium, premium_expiry, free_scans_used FROM users WHERE id=?", (user_id,))
    premium_data = c.fetchone()
    conn.close()

    # Convert user tuple to list so we can modify it
    user_list = list(user) if user else []
    
    # Fix: Ensure free_scans_used (index 12) is an integer
    if user_list and len(user_list) > 12:
        try:
            user_list[12] = int(user_list[12]) if user_list[12] else 0
        except (ValueError, TypeError):
            user_list[12] = 0
    
    # Convert back to tuple
    user = tuple(user_list) if user_list else None

    water_today = sum_today_water(user_id)
    last_sleep_entry = last_sleep(user_id)
    workout_cals_today = sum_today_workout_calories(user_id)
    food_cals_today = sum_today_food_calories(user_id)
    bmi = calculate_bmi(user[5], user[6]) if user and user[5] and user[6] else None
    
    check_calorie_threshold(user_id, food_cals_today, workout_cals_today)

    show_premium_banner = False
    if premium_data:
        is_premium = premium_data[0]
        free_scans = int(premium_data[2]) if premium_data[2] else 0
        if not is_premium and free_scans >= 3:
            show_premium_banner = True

    return render_template('dashboard.html',
                           username=session.get('username'),
                           categories=categories,
                           water_today=water_today,
                           last_sleep=last_sleep_entry,
                           workout_cals_today=workout_cals_today,
                           food_cals_today=food_cals_today,
                           bmi=bmi,
                           user=user,
                           show_premium_banner=show_premium_banner)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    if request.method == 'POST':
        dob = request.form.get('dob')
        weight = request.form.get('weight')
        height = request.form.get('height')
        goal = request.form.get('goal')
        gender = request.form.get('gender')
        health_conditions = request.form.get('health_conditions')
        phone = request.form.get('phone')

        conn = get_db_conn()
        c = conn.cursor()
        c.execute("""UPDATE users SET dob=?, weight=?, height=?, goal=?, gender=?, health_conditions=?, phone=? WHERE id=?""",
                 (dob, weight, height, goal, gender, health_conditions, phone, user_id))
        conn.commit()
        conn.close()

        flash("✅ Profile updated successfully!", "success")
        return redirect(url_for('profile'))

    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = c.fetchone()
    conn.close()

    bmi = calculate_bmi(user[5], user[6]) if user and user[5] and user[6] else None

    return render_template('profile.html', user=user, bmi=bmi)

@app.route('/profile_survey', methods=['GET', 'POST'])
def profile_survey():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    if request.method == 'POST':
        q1 = request.form.get('q1')
        q2 = request.form.get('q2')
        q3 = request.form.get('q3')

        body_type = infer_body_type_from_answers(q1, q2, q3)

        fitness_goal = request.form.get('q4')
        activity_level = request.form.get('q5')

        conditions = request.form.getlist('q6')
        if "None" in conditions:
            conditions = ["None"]
        health_conditions = ", ".join(conditions) if conditions else None

        sleep_opt = request.form.get('q7')
        water_opt = request.form.get('q8')

        survey_score = compute_survey_score(body_type, fitness_goal, activity_level, sleep_opt, water_opt)

        conn = get_db_conn()
        c = conn.cursor()
        c.execute("""UPDATE users SET body_type=?, fitness_goal=?, activity_level=?, health_conditions=?, survey_score=? WHERE id=?""",
                 (body_type, fitness_goal, activity_level, health_conditions, survey_score, user_id))
        conn.commit()
        conn.close()

        flash("✅ Health & body-type survey saved", "success")
        return redirect(url_for('dashboard'))

    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT body_type, fitness_goal, activity_level, health_conditions, survey_score FROM users WHERE id=?", (user_id,))
    row = c.fetchone()
    conn.close()

    body_type = row[0] if row else None
    fitness_goal = row[1] if row else None
    activity_level = row[2] if row else None
    health_conditions = row[3] if row else None
    survey_score = row[4] if row else None

    return render_template('profile_survey.html',
                           body_type=body_type,
                           fitness_goal=fitness_goal,
                           activity_level=activity_level,
                           health_conditions=health_conditions,
                           survey_score=survey_score)

@app.route('/category/<slug>', methods=['GET', 'POST'])
def category(slug):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    friendly = slug.replace('-', ' ').title()
    
    if request.method == 'POST':
        has_access, access_type = check_premium_access(user_id)
        
        if not has_access:
            flash("⚠️ Free scan limit reached! Upgrade to Premium for unlimited scans.", "warning")
            return redirect(url_for('premium'))
        
        file = request.files.get('image')
        if file and file.filename:
            filename = f"{slug}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            try:
                model = get_food_model()
                result = model.predict_by_filepath(file_path, input_type="image")
                
                items = []
                for concept in result.outputs[0].data.concepts[:5]:
                    name = concept.name
                    score = round(concept.value * 100, 1)
                    calorie_info = get_calorie_info(name, friendly)
                    
                    items.append({
                        "name": name,
                        "confidence": score,
                        "calories": calorie_info["calories"],
                        "serving": calorie_info["serving"],
                        "category": calorie_info["category"],
                        "protein": calorie_info.get("protein", 0),
                        "carbs": calorie_info.get("carbs", 0),
                        "fat": calorie_info.get("fat", 0),
                    })
                
                if items:
                    main_dish = items[0]
                    
                    today = date.today().isoformat()
                    now_time = datetime.now().strftime('%H:%M:%S')
                    conn = get_db_conn()
                    c = conn.cursor()
                    c.execute("""INSERT INTO food_logs 
                                (user_id, food_name, calories, category, entry_date, entry_time, image_path, protein, carbs, fat) 
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                             (user_id, main_dish["name"], main_dish["calories"], 
                              main_dish["category"], today, now_time, filename,
                              main_dish.get("protein", 0), main_dish.get("carbs", 0), main_dish.get("fat", 0)))
                    
                    if access_type == "free":
                        c.execute("UPDATE users SET free_scans_used = free_scans_used + 1 WHERE id=?", (user_id,))
                        c.execute("SELECT free_scans_used FROM users WHERE id=?", (user_id,))
                        scans_used = c.fetchone()[0]
                        
                        if scans_used >= 3:
                            conn.commit()
                            conn.close()
                            flash(f"🎯 You've used all 3 free scans! Upgrade to Premium for unlimited access.", "warning")
                            return redirect(url_for('premium'))
                        else:
                            flash(f"✅ Added {main_dish['name']} ({main_dish['calories']} cal) - {3 - scans_used} free scans remaining", "success")
                    else:
                        flash(f"✅ Added {main_dish['name']} ({main_dish['calories']} cal)", "success")
                    
                    conn.commit()
                    conn.close()
                    
                    return render_template('category_result.html', 
                                         category_name=friendly, 
                                         image=filename, 
                                         items=items, 
                                         main_dish=main_dish,
                                         slug=slug)
                else:
                    flash("No food items detected. Try another image.", "warning")
            except Exception as e:
                flash(f"Error analyzing image: {str(e)}", "danger")
                return redirect(url_for('category', slug=slug))
    
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT is_premium, free_scans_used FROM users WHERE id=?", (user_id,))
    user = c.fetchone()
    conn.close()
    
    scans_remaining = 3 - user[1] if user and not user[0] else None
    
    return render_template('category_upload.html', 
                         category_name=friendly, 
                         slug=slug,
                         scans_remaining=scans_remaining,
                         is_premium=user[0] if user else False)

@app.route('/food_history')
def food_history():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("""SELECT id, food_name, calories, category, entry_date, image_path, entry_time 
                 FROM food_logs WHERE user_id=? ORDER BY entry_date DESC, entry_time DESC LIMIT 100""", 
              (user_id,))
    logs = c.fetchall()
    conn.close()
    
    return render_template('food_history.html', logs=logs)

@app.route('/history')
def history():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    view = request.args.get('view', 'daily')
    
    conn = get_db_conn()
    c = conn.cursor()
    
    if view == 'daily':
        days = [(date.today() - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
        data = []
        for day in days:
            c.execute("SELECT SUM(calories) FROM food_logs WHERE user_id=? AND entry_date=?", (user_id, day))
            cal = c.fetchone()[0] or 0
            data.append({'date': day, 'calories': cal})
    
    elif view == 'weekly':
        data = []
        for i in range(3, -1, -1):
            week_start = date.today() - timedelta(days=date.today().weekday() + 7*i)
            week_end = week_start + timedelta(days=6)
            c.execute("SELECT SUM(calories) FROM food_logs WHERE user_id=? AND entry_date BETWEEN ? AND ?", 
                     (user_id, week_start.isoformat(), week_end.isoformat()))
            cal = c.fetchone()[0] or 0
            data.append({'date': f"Week {4-i}", 'calories': cal})
    
    else:
        data = []
        for i in range(5, -1, -1):
            month_date = date.today() - timedelta(days=30*i)
            month_str = month_date.strftime('%Y-%m')
            c.execute("SELECT SUM(calories) FROM food_logs WHERE user_id=? AND entry_date LIKE ?", 
                     (user_id, f"{month_str}%"))
            cal = c.fetchone()[0] or 0
            data.append({'date': month_str, 'calories': cal})
    
    conn.close()
    
    return render_template('history.html', data=data, view=view)

@app.route('/analytics')
def analytics():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db_conn()
    c = conn.cursor()
    
    c.execute("SELECT gender, weight, height, goal FROM users WHERE id=?", (user_id,))
    user_info = c.fetchone()
    
    gender = user_info[0] if user_info else None
    if gender == 'Male':
        recommended_cal = 2500
    elif gender == 'Female':
        recommended_cal = 2000
    else:
        recommended_cal = 2200
    
    days = [(date.today() - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
    calories_in = []
    calories_out = []
    net_calories = []
    
    for day in days:
        c.execute("SELECT SUM(calories) FROM food_logs WHERE user_id=? AND entry_date=?", (user_id, day))
        cal_in = c.fetchone()[0] or 0
        
        c.execute("SELECT SUM(calories_burnt) FROM workout_logs WHERE user_id=? AND entry_date=?", (user_id, day))
        cal_out = c.fetchone()[0] or 0
        
        calories_in.append(cal_in)
        calories_out.append(cal_out)
        net_calories.append(cal_in - cal_out)
    
    conn.close()
    
    return render_template('analytics.html', 
                         days=days,
                         calories_in=calories_in,
                         calories_out=calories_out,
                         net_calories=net_calories,
                         recommended_cal=recommended_cal)

@app.route('/graph_data')
def graph_data():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    days = [(date.today() - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
    
    conn = get_db_conn()
    c = conn.cursor()
    
    calories_in = []
    calories_out = []
    
    for day in days:
        c.execute("SELECT SUM(calories) FROM food_logs WHERE user_id=? AND entry_date=?", (user_id, day))
        cal_in = c.fetchone()[0] or 0
        calories_in.append(cal_in)
        
        c.execute("SELECT SUM(calories_burnt) FROM workout_logs WHERE user_id=? AND entry_date=?", (user_id, day))
        cal_out = c.fetchone()[0] or 0
        calories_out.append(cal_out)
    
    conn.close()
    
    return jsonify({
        'days': days,
        'calories_in': calories_in,
        'calories_out': calories_out,
        'net': [cin - cout for cin, cout in zip(calories_in, calories_out)]
    })

@app.route('/weight_tracker', methods=['GET', 'POST'])
def weight_tracker():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    if request.method == 'POST':
        weight = float(request.form.get('weight'))
        today = date.today().isoformat()
        now_time = datetime.now().strftime('%H:%M:%S')
        
        conn = get_db_conn()
        c = conn.cursor()
        c.execute("INSERT INTO weight_logs (user_id, weight, entry_date, entry_time) VALUES (?, ?, ?, ?)",
                 (user_id, weight, today, now_time))
        c.execute("UPDATE users SET weight=? WHERE id=?", (weight, user_id))
        conn.commit()
        conn.close()
        
        flash(f"✅ Weight updated to {weight} kg", "success")
        return redirect(url_for('weight_tracker'))
    
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT weight, entry_date, entry_time FROM weight_logs WHERE user_id=? ORDER BY entry_date DESC, entry_time DESC LIMIT 30",
             (user_id,))
    logs = c.fetchall()
    
    c.execute("SELECT weight FROM users WHERE id=?", (user_id,))
    current_weight = c.fetchone()[0]
    conn.close()
    
    return render_template('weight_tracker.html', logs=logs, current_weight=current_weight)

@app.route('/manual_food_entry', methods=['GET', 'POST'])
def manual_food_entry():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    if request.method == 'POST':
        food_name = request.form.get('food_name').strip()
        calories = int(request.form.get('calories'))
        category = request.form.get('category')
        meal_type = request.form.get('meal_type')
        protein = float(request.form.get('protein', 0))
        carbs = float(request.form.get('carbs', 0))
        fat = float(request.form.get('fat', 0))
        
        today = date.today().isoformat()
        now_time = datetime.now().strftime('%H:%M:%S')
        
        conn = get_db_conn()
        c = conn.cursor()
        c.execute("""INSERT INTO food_logs 
                    (user_id, food_name, calories, category, entry_date, entry_time, meal_type, protein, carbs, fat) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                 (user_id, food_name, calories, category, today, now_time, meal_type, protein, carbs, fat))
        conn.commit()
        conn.close()
        
        flash(f"✅ Added {food_name} ({calories} cal) manually", "success")
        return redirect(url_for('food_history'))
    
    return render_template('manual_food_entry.html')

@app.route('/delete_food/<int:food_id>', methods=['POST'])
def delete_food(food_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("DELETE FROM food_logs WHERE id=? AND user_id=?", (food_id, user_id))
    conn.commit()
    conn.close()
    
    flash("✅ Food entry deleted", "success")
    return redirect(url_for('food_history'))

@app.route('/edit_food/<int:food_id>', methods=['GET', 'POST'])
def edit_food(food_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db_conn()
    c = conn.cursor()
    
    if request.method == 'POST':
        food_name = request.form.get('food_name')
        calories = int(request.form.get('calories'))
        protein = float(request.form.get('protein', 0))
        carbs = float(request.form.get('carbs', 0))
        fat = float(request.form.get('fat', 0))
        
        c.execute("UPDATE food_logs SET food_name=?, calories=?, protein=?, carbs=?, fat=? WHERE id=? AND user_id=?",
                 (food_name, calories, protein, carbs, fat, food_id, user_id))
        conn.commit()
        conn.close()
        
        flash("✅ Food entry updated", "success")
        return redirect(url_for('food_history'))
    
    c.execute("SELECT id, food_name, calories, category, protein, carbs, fat FROM food_logs WHERE id=? AND user_id=?", (food_id, user_id))
    food = c.fetchone()
    conn.close()
    
    return render_template('edit_food.html', food=food)

@app.route('/workout', methods=['GET', 'POST'])
def workout():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    if request.method == 'POST':
        activity = request.form.get('activity')
        duration_min = int(request.form.get('duration_min') or 0)
        intensity = request.form.get('intensity')
        calories_burnt = request.form.get('calories_burnt')

        if not calories_burnt or calories_burnt.strip() == "":
            per_min = 5
            if activity == "Walking":
                per_min = 5
            elif activity == "Running":
                per_min = 10
            elif activity == "Cycling":
                per_min = 8
            elif activity == "Yoga":
                per_min = 4
            elif activity == "Strength Training":
                per_min = 7
            elif activity == "HIIT":
                per_min = 12
            elif activity == "Sports":
                per_min = 8

            if intensity == "Low":
                per_min = int(per_min * 0.8)
            elif intensity == "High":
                per_min = int(per_min * 1.2)

            calories_burnt = per_min * duration_min
        else:
            calories_burnt = int(calories_burnt)

        today = date.today().isoformat()
        conn = get_db_conn()
        c = conn.cursor()
        c.execute("""INSERT INTO workout_logs (user_id, activity, duration_min, calories_burnt, entry_date)
                     VALUES (?, ?, ?, ?, ?)""",
                 (user_id, activity, duration_min, calories_burnt, today))
        conn.commit()
        conn.close()

        flash(f"✅ Logged {activity} ({duration_min} min, {calories_burnt} kcal)", "success")
        return redirect(url_for('workout'))

    calories_in = sum_today_food_calories(user_id)
    calories_out = sum_today_workout_calories(user_id)
    net_calories = calories_in - calories_out

    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT gender, goal, body_type, fitness_goal FROM users WHERE id=?", (user_id,))
    row = c.fetchone()
    conn.close()

    gender = row[0] if row else None
    goal = row[1] if row else None
    body_type = row[2] if row else None
    fitness_goal = row[3] if row else None

    if gender == 'Male':
        base_cal = 2500
    elif gender == 'Female':
        base_cal = 2000
    else:
        base_cal = 2200

    if goal == "Weight Loss":
        target_net = int(base_cal * 0.8)
    elif goal == "Weight Gain":
        target_net = int(base_cal * 1.1)
    else:
        target_net = base_cal

    status = "On Track"
    if net_calories > target_net:
        status = "Over Target"
    elif net_calories > target_net * 0.9:
        status = "Slightly Over"

    extra_cal = max(0, net_calories - target_net)
    suggested_walk_min = (extra_cal + 4) // 5 if extra_cal > 0 else 0

    if extra_cal > 0:
        msg = f"🔥 Net calories {net_calories} kcal (target {target_net}). Try an extra {suggested_walk_min} min brisk walk."
        add_notification(user_id, msg, "warning")

    burn_target = 500
    burn_progress = min(100, int(calories_out * 100 / burn_target)) if burn_target > 0 else 0
    burn_remaining = max(0, burn_target - calories_out)

    today_str = date.today().isoformat()
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("""SELECT id, activity, duration_min, calories_burnt, entry_date
                 FROM workout_logs WHERE user_id=? AND entry_date=? ORDER BY id DESC""",
             (user_id, today_str))
    today_workouts = c.fetchall()

    days = [(date.today() - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
    weekly_burn = []
    weekly_duration = []

    for d in days:
        c.execute("SELECT SUM(calories_burnt), SUM(duration_min) FROM workout_logs WHERE user_id=? AND entry_date=?", (user_id, d))
        row = c.fetchone()
        cal_burn = row[0] or 0
        dur = row[1] or 0
        weekly_burn.append(cal_burn)
        weekly_duration.append(dur)

    conn.close()

    recommendations = get_workout_recommendations(user_id, net_calories, target_net)

    return render_template('workout.html',
                           calories_in=calories_in,
                           calories_out=calories_out,
                           net_calories=net_calories,
                           target_net=target_net,
                           status=status,
                           suggested_walk_min=suggested_walk_min,
                           burn_target=burn_target,
                           burn_progress=burn_progress,
                           burn_remaining=burn_remaining,
                           today_workouts=today_workouts,
                           days=days,
                           weekly_burn=weekly_burn,
                           weekly_duration=weekly_duration,
                           recommendations=recommendations,
                           body_type=body_type,
                           fitness_goal=fitness_goal)

@app.route('/water', methods=['GET', 'POST'])
def water():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    if request.method == 'POST':
        amount_ml = int(request.form.get('amount_ml') or 0)
        time_input = request.form.get('time')  # HH:MM format from time input
        today_str = date.today().isoformat()
        
        # If time provided, use it; otherwise use current time
        if time_input:
            entry_time = time_input + ":00"  # Convert HH:MM to HH:MM:SS
        else:
            entry_time = datetime.now().strftime('%H:%M:%S')

        conn = get_db_conn()
        c = conn.cursor()
        # Match your actual schema: user_id, amount_ml, entry_date, entry_time
        c.execute(
            "INSERT INTO water_logs (user_id, amount_ml, entry_date, entry_time) VALUES (?, ?, ?, ?)",
            (user_id, amount_ml, today_str, entry_time)
        )
        conn.commit()
        conn.close()
        flash(f"💧 Logged {amount_ml} ml water at {time_input}", "success")
        return redirect(url_for('water'))

    # GET: calculate summary
    today_str = date.today().isoformat()
    conn = get_db_conn()
    c = conn.cursor()

    # total water today
    c.execute("SELECT COALESCE(SUM(amount_ml), 0) FROM water_logs WHERE user_id=? AND entry_date=?",
              (user_id, today_str))
    total_water_ml = c.fetchone()[0] or 0

    # fetch today logs - match your actual columns
    c.execute("""SELECT id, amount_ml, entry_date, entry_time
                 FROM water_logs
                 WHERE user_id=? AND entry_date=?
                 ORDER BY id DESC""",
             (user_id, today_str))
    today_water_logs = c.fetchall()

    conn.close()

    # targets and remaining
    water_target_ml = 2000
    remaining_water_ml = max(0, water_target_ml - total_water_ml)
    suggested_glass_ml = 250

    return render_template(
        'water.html',
        total_water_ml=total_water_ml,
        water_target_ml=water_target_ml,
        remaining_water_ml=remaining_water_ml,
        suggested_glass_ml=suggested_glass_ml,
        today_water_logs=today_water_logs
    )


from datetime import datetime, date, timedelta

@app.route('/sleep', methods=['GET', 'POST'])
def sleep():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    # ----- POST: log new sleep -----
    if request.method == 'POST':
        sleep_date = request.form.get('sleep_date')      # 'YYYY-MM-DD'
        sleep_start = request.form.get('sleep_start')    # 'HH:MM'
        sleep_end = request.form.get('sleep_end')        # 'HH:MM'

        start_dt = datetime.strptime(f"{sleep_date} {sleep_start}", "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(f"{sleep_date} {sleep_end}", "%Y-%m-%d %H:%M")

        if end_dt <= start_dt:
            end_dt += timedelta(days=1)

        duration_hours = round((end_dt - start_dt).total_seconds() / 3600, 2)

        conn = get_db_conn()
        c = conn.cursor()
        # match schema: (user_id, sleep_hours, entry_date, note)
        c.execute(
            "INSERT INTO sleep_logs (user_id, sleep_hours, entry_date, note) "
            "VALUES (?, ?, ?, ?)",
            (user_id, duration_hours, sleep_date, "")
        )
        conn.commit()
        conn.close()

        flash(f"😴 Logged {duration_hours} hours of sleep", "success")
        return redirect(url_for('sleep'))

    # ----- GET: summary + recent logs -----
    today_str = date.today().isoformat()

    conn = get_db_conn()
    c = conn.cursor()

    # recent logs: (id, sleep_hours, entry_date)
    c.execute(
        """SELECT id, sleep_hours, entry_date
           FROM sleep_logs
           WHERE user_id=?
           ORDER BY entry_date DESC, id DESC
           LIMIT 7""",
        (user_id,)
    )
    recent_sleep_logs = c.fetchall()

    # compute summary BEFORE closing conn
    sleep_target_hours = 8.0
    if recent_sleep_logs:
        last_sleep_hours = float(recent_sleep_logs[0][1] or 0)
    else:
        last_sleep_hours = 0.0

    sleep_debt_hours = round(max(0.0, sleep_target_hours - last_sleep_hours), 2)

    conn.close()

    return render_template(
        'sleep.html',
        last_sleep_hours=last_sleep_hours,
        sleep_target_hours=sleep_target_hours,
        sleep_debt_hours=sleep_debt_hours,
        bedtime_suggestion="30–60 minutes",
        today=today_str,
        recent_sleep_logs=recent_sleep_logs
    )

# ==================== IMPROVED CHATBOT ROUTES ====================
# Copy everything below and REPLACE your existing chatbot routes in app.py

@app.route('/chatbot')
def chatbot():
    """Chatbot page - shows AI coach interface"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("""SELECT username, weight, height, gender, goal, body_type, 
                 fitness_goal, activity_level, health_conditions FROM users WHERE id=?""", (user_id,))
    user = c.fetchone()
    conn.close()
    
    return render_template('chatbot.html', user=user)


@app.route('/chatbot/send', methods=['POST'])
def chatbot_send():
    """Handle chatbot messages - uses smart rule-based responses"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not logged in'}), 401
        
        user_id = session['user_id']
        user_message = request.json.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Empty message'}), 400
        
        # Get user context
        conn = get_db_conn()
        c = conn.cursor()
        c.execute("""SELECT username, weight, height, gender, goal, body_type, 
                     fitness_goal, activity_level, health_conditions, dob FROM users WHERE id=?""", (user_id,))
        user = c.fetchone()
        
        # Get today's stats
        today = date.today().isoformat()
        c.execute("SELECT SUM(calories) FROM food_logs WHERE user_id=? AND entry_date=?", (user_id, today))
        calories_today = c.fetchone()[0] or 0
        
        c.execute("SELECT SUM(calories_burnt) FROM workout_logs WHERE user_id=? AND entry_date=?", (user_id, today))
        workout_today = c.fetchone()[0] or 0
        
        c.execute("SELECT SUM(amount_ml) FROM water_logs WHERE user_id=? AND entry_date=?", (user_id, today))
        water_today = c.fetchone()[0] or 0
        
        # Get weekly averages
        week_ago = (date.today() - timedelta(days=7)).isoformat()
        c.execute("SELECT AVG(calories) FROM food_logs WHERE user_id=? AND entry_date >= ?", (user_id, week_ago))
        avg_calories_week = c.fetchone()[0] or 0
        
        c.execute("SELECT AVG(calories_burnt) FROM workout_logs WHERE user_id=? AND entry_date >= ?", (user_id, week_ago))
        avg_workout_week = c.fetchone()[0] or 0
        
        conn.close()
        
        # Calculate BMI
        bmi = calculate_bmi(user[1], user[2]) if user and user[1] and user[2] else None
        
        # Get intelligent response
        bot_reply = get_smart_response(
            user_message, user, calories_today, workout_today, water_today, 
            bmi, avg_calories_week, avg_workout_week
        )
        
        return jsonify({
            'success': True,
            'reply': bot_reply
        })
    
    except Exception as e:
        print(f"CHATBOT ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': True,
            'reply': f"Sorry, I encountered an error. Please make sure your profile is complete and try again."
        })


def get_smart_response(message, user, calories_today, workout_today, water_today, bmi, avg_cal_week, avg_workout_week):
    """Improved AI responses with better natural language understanding"""
    message_lower = message.lower()
    
    # Extract user info
    username = user[0] if user and user[0] else "there"
    weight = user[1] if user and user[1] else None
    height = user[2] if user and user[2] else None
    gender = user[3] if user and user[3] else "Not specified"
    goal = user[4] if user and user[4] else None
    fitness_goal = user[6] if user and user[6] else None
    activity_level = user[7] if user and user[7] else None
    health_conditions = (user[8] if user and user[8] else "").lower()
    
    # Calculate calorie needs
    if gender == 'Male':
        base_cal = 2500
    elif gender == 'Female':
        base_cal = 2000
    else:
        base_cal = 2200
    
    if goal == "Weight Loss":
        target_cal = int(base_cal * 0.8)
    elif goal == "Weight Gain":
        target_cal = int(base_cal * 1.2)
    else:
        target_cal = base_cal
    
    
    # ========== DIET / FOOD / MEAL PLANS ==========
    diet_keywords = ['diet', 'meal', 'food', 'eat', 'nutrition', 'plan', 'recipe', 'menu', 
                     'lose weight', 'gain weight', 'fat loss', 'what to eat', 'what should i eat',
                     'meal plan', 'food plan', 'diet chart', 'eating', 'hungry']
    
    if any(keyword in message_lower for keyword in diet_keywords):
        response = f"🥗 **Diet Plan for {username}**\n\n"
        
        # Determine goal from message or profile
        is_weight_loss = goal == "Weight Loss" or any(word in message_lower for word in ['lose', 'loss', 'reduce', 'cut', 'slim', 'fat'])
        is_weight_gain = goal == "Weight Gain" or any(word in message_lower for word in ['gain', 'bulk', 'increase', 'muscle'])
        
        if is_weight_loss:
            response += f"**🎯 Weight Loss Plan** | Target: {target_cal} kcal/day\n"
            response += f"Current: {calories_today} kcal today | Weekly avg: {int(avg_cal_week)} kcal\n\n"
            
            response += "**📅 Daily Meal Schedule:**\n\n"
            response += "🌅 **Breakfast (7-8 AM)** - 350 kcal\n"
            response += "   • 2 boiled eggs + 1 banana + green tea\n"
            response += "   OR 1 cup oats with milk + apple\n\n"
            
            response += "☕ **Mid-Morning (10:30 AM)** - 150 kcal\n"
            response += "   • 1 fruit + 10 almonds\n"
            response += "   OR low-fat yogurt\n\n"
            
            response += "🍛 **Lunch (12:30-1:30 PM)** - 450 kcal\n"
            response += "   • 2 roti + dal + salad\n"
            response += "   OR brown rice + grilled chicken + veggies\n\n"
            
            response += "🍵 **Evening (4 PM)** - 100 kcal\n"
            response += "   • Green tea + 2 biscuits OR 1 fruit\n\n"
            
            response += "🌙 **Dinner (7-8 PM)** - 400 kcal\n"
            response += "   • Grilled chicken/paneer + 1 roti + soup\n"
            response += "   OR fish + salad + vegetables\n\n"
            
            response += "💡 **Weight Loss Tips:**\n"
            response += "✓ Drink 8-10 glasses of water daily\n"
            response += "✓ Avoid fried foods, sugary drinks, white rice\n"
            response += "✓ Eat slowly and chew properly\n"
            response += "✓ No eating after 8 PM\n"
            if calories_today > 0:
                diff = target_cal - calories_today
                if diff > 0:
                    response += f"✓ You can eat {diff} more kcal today\n"
                else:
                    response += f"⚠️ You're {abs(diff)} kcal over - do 30 min walk!\n"
        
        elif is_weight_gain:
            response += f"**💪 Weight Gain Plan** | Target: {target_cal} kcal/day\n"
            response += f"Current: {calories_today} kcal today | Weekly avg: {int(avg_cal_week)} kcal\n\n"
            
            response += "**📅 Daily Meal Schedule:**\n\n"
            response += "🌅 **Breakfast (7 AM)** - 600 kcal\n"
            response += "   • 3 eggs + 3 bread slices + banana shake\n"
            response += "   OR 2 parathas + curd + milk\n\n"
            
            response += "☕ **Mid-Morning (10 AM)** - 300 kcal\n"
            response += "   • Protein shake + handful of nuts\n"
            response += "   OR peanut butter sandwich + juice\n\n"
            
            response += "🍛 **Lunch (1 PM)** - 800 kcal\n"
            response += "   • 2 cups rice + chicken curry + dal\n"
            response += "   OR 3 rotis + paneer + vegetables\n\n"
            
            response += "🍵 **Evening (4 PM)** - 350 kcal\n"
            response += "   • Sandwich + milk\n"
            response += "   OR samosa + juice\n\n"
            
            response += "🌙 **Dinner (8 PM)** - 700 kcal\n"
            response += "   • 2 rotis with ghee + chicken/fish + rice + curd\n\n"
            
            response += "🌜 **Before Bed (10 PM)** - 200 kcal\n"
            response += "   • Milk with protein powder OR banana shake\n\n"
            
            response += "💡 **Weight Gain Tips:**\n"
            response += "✓ Eat every 2-3 hours\n"
            response += "✓ Add ghee, butter, nuts to meals\n"
            response += "✓ Drink milk 2-3 times daily\n"
            response += "✓ Eat calorie-dense foods\n"
            if calories_today > 0:
                response += f"✓ You need {target_cal - calories_today} more kcal today!\n"
        
        else:
            response += f"**⚖️ Balanced Diet Plan** | Target: {target_cal} kcal/day\n\n"
            response += "**General Healthy Diet:**\n\n"
            response += "🌅 **Breakfast:** Eggs/oats + fruits (300-400 kcal)\n"
            response += "🍛 **Lunch:** Rice/roti + dal + veggies (450-550 kcal)\n"
            response += "🍵 **Snacks:** Fruits, nuts, yogurt (200-300 kcal)\n"
            response += "🌙 **Dinner:** Light meal + salad (400-500 kcal)\n\n"
            
            response += "💡 **Healthy Eating Tips:**\n"
            response += "✓ Balance proteins, carbs, and fats\n"
            response += "✓ Eat 5-6 small meals daily\n"
            response += "✓ Include vegetables in every meal\n"
            response += "✓ Stay hydrated - 2-3L water\n"
            response += f"✓ Today's intake: {calories_today} kcal"
        
        return response
    
    
    # ========== WORKOUT / EXERCISE ==========
    workout_keywords = ['workout', 'exercise', 'gym', 'training', 'fitness', 'routine',
                        'cardio', 'strength', 'yoga', 'running', 'jogging', 'swimming',
                        'weight training', 'how to exercise', 'physical activity']
    
    if any(keyword in message_lower for keyword in workout_keywords):
        response = f"💪 **Workout Plan for {username}**\n\n"
        
        is_fat_loss = fitness_goal == "Fat loss" or any(word in message_lower for word in ['lose', 'loss', 'fat', 'cardio'])
        is_muscle = fitness_goal == "Muscle gain" or any(word in message_lower for word in ['muscle', 'gain', 'strength', 'bulk'])
        
        if is_fat_loss:
            response += f"**🔥 Fat Loss Program** | Activity: {activity_level or 'Moderate'}\n"
            response += f"Today: {workout_today} kcal burnt | Weekly avg: {int(avg_workout_week)} kcal\n\n"
            
            response += "**6 Days/Week Plan:**\n\n"
            response += "**MON, WED, FRI - CARDIO (40 min)**\n"
            response += "• Brisk walking/jogging: 30-40 min\n"
            response += "• OR Cycling: 30-40 min\n"
            response += "• OR Swimming: 30 min\n"
            response += "• Burns: 300-400 kcal ✓\n\n"
            
            response += "**TUE, THU, SAT - STRENGTH (30 min)**\n"
            response += "• Squats: 3 sets × 15 reps\n"
            response += "• Push-ups: 3 sets × 10 reps\n"
            response += "• Lunges: 3 sets × 12 each leg\n"
            response += "• Planks: 3 sets × 45 sec\n"
            response += "• Burpees: 3 sets × 10 reps\n"
            response += "• Burns: 250-300 kcal ✓\n\n"
            
            response += "**SUNDAY - REST**\n"
            response += "• Light yoga/stretching (optional)\n\n"
            
            response += "💡 **Fat Loss Tips:**\n"
            response += "✓ Do cardio in the morning (empty stomach)\n"
            response += "✓ Exercise 5-6 days per week\n"
            response += "✓ Combine with calorie deficit diet\n"
            if calories_today > 0:
                net_cal = calories_today - workout_today
                response += f"✓ Your net calories today: {net_cal} kcal\n"
        
        elif is_muscle:
            response += f"**💪 Muscle Building Program**\n"
            response += f"Today: {workout_today} kcal burnt\n\n"
            
            response += "**5 Days/Week Plan:**\n\n"
            response += "**MON - CHEST & TRICEPS**\n"
            response += "• Bench press: 4 × 8-10 reps\n"
            response += "• Push-ups: 3 × 12 reps\n"
            response += "• Chest flyes: 3 × 10 reps\n"
            response += "• Tricep dips: 3 × 10 reps\n\n"
            
            response += "**TUE - BACK & BICEPS**\n"
            response += "• Deadlifts: 4 × 6-8 reps\n"
            response += "• Pull-ups: 3 × 8 reps\n"
            response += "• Barbell rows: 3 × 10 reps\n"
            response += "• Bicep curls: 3 × 12 reps\n\n"
            
            response += "**WED - REST**\n\n"
            
            response += "**THU - LEGS**\n"
            response += "• Squats: 4 × 10 reps\n"
            response += "• Leg press: 3 × 12 reps\n"
            response += "• Lunges: 3 × 12 each leg\n"
            response += "• Calf raises: 4 × 15 reps\n\n"
            
            response += "**FRI - SHOULDERS & ABS**\n"
            response += "• Military press: 4 × 8-10 reps\n"
            response += "• Lateral raises: 3 × 12 reps\n"
            response += "• Planks: 3 × 60 sec\n"
            response += "• Crunches: 3 × 20 reps\n\n"
            
            response += "**SAT, SUN - REST**\n\n"
            
            response += "💡 **Muscle Gain Tips:**\n"
            response += "✓ Lift heavy weights (8-12 reps)\n"
            response += "✓ Eat in calorie surplus (+500 kcal)\n"
            response += "✓ Protein: 1.5-2g per kg body weight\n"
            response += "✓ Rest 48 hours between same muscles\n"
        
        else:
            response += f"**🏃 General Fitness Program**\n"
            response += f"Activity: {activity_level or 'Moderate'} | Today: {workout_today} kcal\n\n"
            
            response += "**5 Days/Week Plan:**\n\n"
            response += "**MON, WED, FRI - CARDIO (30 min)**\n"
            response += "• Walking/jogging/cycling\n"
            response += "• Burns: 250-300 kcal\n\n"
            
            response += "**TUE, THU - STRENGTH (25 min)**\n"
            response += "• Squats: 3 × 15 reps\n"
            response += "• Push-ups: 3 × 10 reps\n"
            response += "• Lunges: 3 × 12 reps\n"
            response += "• Planks: 3 × 30 sec\n"
            response += "• Burns: 200-250 kcal\n\n"
            
            response += "**SAT, SUN - ACTIVE REST**\n"
            response += "• Yoga/stretching/walking\n\n"
            
            response += "💡 **Fitness Tips:**\n"
            response += "✓ Exercise 4-5 days minimum\n"
            response += "✓ Mix cardio and strength training\n"
            response += "✓ Stay consistent\n"
            response += f"✓ Today's burnt: {workout_today} kcal"
        
        # Health conditions
        if health_conditions:
            response += "\n\n⚕️ **Your Health Notes:**\n"
            if "diabetes" in health_conditions:
                response += "• Walk 15 min after meals\n"
            if "knee" in health_conditions or "joint" in health_conditions:
                response += "• Avoid high-impact (do swimming/cycling)\n"
            if "pcos" in health_conditions:
                response += "• Mix cardio + strength (30 min each)\n"
        
        return response
    
    
    # ========== BREAKFAST ==========
    if 'breakfast' in message_lower or 'morning' in message_lower:
        response = f"🌅 **Breakfast Ideas for {username}**\n\n"
        
        if goal == "Weight Loss" or 'lose' in message_lower or 'diet' in message_lower:
            response += "**Low-Calorie Options (300-350 kcal):**\n\n"
            response += "**Option 1: Indian**\n"
            response += "• Vegetable poha/upma (250 kcal)\n"
            response += "• Green tea\n\n"
            
            response += "**Option 2: Eggs**\n"
            response += "• 3 egg whites + veggies omelette (150 kcal)\n"
            response += "• 2 brown bread (140 kcal)\n\n"
            
            response += "**Option 3: Healthy**\n"
            response += "• 2 moong dal chillas (280 kcal)\n"
            response += "• Mint chutney + 1 fruit\n"
        
        elif goal == "Weight Gain" or 'gain' in message_lower or 'bulk' in message_lower:
            response += "**High-Calorie Options (550-600 kcal):**\n\n"
            response += "**Option 1: Indian**\n"
            response += "• 2 aloo parathas with ghee (500 kcal)\n"
            response += "• Curd (100 kcal)\n\n"
            
            response += "**Option 2: Eggs**\n"
            response += "• 3 whole eggs + 3 bread + butter (550 kcal)\n"
            response += "• Banana shake (200 kcal)\n\n"
            
            response += "**Option 3: Heavy**\n"
            response += "• Upma with ghee (400 kcal)\n"
            response += "• 1 glass milk (150 kcal)\n"
        
        else:
            response += "**Balanced Options (400 kcal):**\n\n"
            response += "• 2 idlis + sambar + chutney (280 kcal)\n"
            response += "• OR 1 cup oats + milk + fruits (350 kcal)\n"
            response += "• OR 2 eggs + 2 toast (320 kcal)\n"
            response += "• OR 1 paratha + curd (400 kcal)\n"
        
        response += f"\n💡 Today's intake: {calories_today} kcal"
        return response
    
    
    # ========== BMI / HEALTH / STATUS ==========
    health_keywords = ['bmi', 'health', 'status', 'check', 'weight status', 'am i healthy', 
                       'my health', 'body status', 'fitness status']
    
    if any(keyword in message_lower for keyword in health_keywords):
        response = f"📊 **Health Report for {username}**\n\n"
        
        if weight and height:
            response += f"**Physical Stats:**\n"
            response += f"• Weight: {weight} kg\n"
            response += f"• Height: {height} cm\n"
            response += f"• BMI: {bmi:.1f}\n"
            
            if bmi < 18.5:
                response += f"• Status: Underweight ⚠️\n\n"
                response += "**Recommendations:**\n"
                response += "✓ Eat 500 kcal more daily\n"
                response += "✓ Do strength training\n"
                response += "✓ Eat nuts, dried fruits, ghee\n"
            
            elif 18.5 <= bmi < 25:
                response += f"• Status: Normal / Healthy ✅\n\n"
                response += "**Great! Keep it up:**\n"
                response += "✓ Continue balanced diet\n"
                response += "✓ Exercise 4-5 days/week\n"
                response += "✓ Stay hydrated\n"
            
            elif 25 <= bmi < 30:
                response += f"• Status: Overweight ⚠️\n\n"
                response += "**Recommendations:**\n"
                response += "✓ Create 500 kcal deficit\n"
                response += "✓ Do cardio 40-50 min daily\n"
                response += "✓ Reduce sugar and fried food\n"
                response += "✓ Target: Lose 0.5-1 kg/week\n"
            
            else:
                response += f"• Status: Obese 🚨\n\n"
                response += "**Important:**\n"
                response += "✓ Consult a doctor first\n"
                response += "✓ Start slow (walking, swimming)\n"
                response += "✓ Create 700 kcal deficit\n"
                response += "✓ Get professional help\n"
        else:
            response += "⚠️ **Profile Incomplete**\n\n"
            response += "Please update weight & height in Profile!\n\n"
        
        response += f"\n**Today's Activity:**\n"
        response += f"• Food eaten: {calories_today} kcal\n"
        response += f"• Exercise done: {workout_today} kcal burnt\n"
        response += f"• Net calories: {calories_today - workout_today} kcal\n"
        response += f"• Water drunk: {water_today} ml / 2000 ml\n"
        
        if health_conditions and health_conditions != "none":
            response += f"\n**Health Conditions:** {health_conditions}"
        
        return response
    
    
    # ========== WATER / HYDRATION ==========
    water_keywords = ['water', 'hydration', 'drink', 'thirsty', 'how much water',
                      'should i drink', 'hydrate']
    
    if any(keyword in message_lower for keyword in water_keywords):
        water_left = max(0, 2000 - water_today)
        glasses = int(water_left / 250)
        
        response = f"💧 **Hydration Status**\n\n"
        response += f"**Today:** {water_today} ml / 2000 ml target\n"
        response += f"**Remaining:** {water_left} ml\n\n"
        
        if water_left > 0:
            response += f"**You need: {glasses} more glasses** (250ml each)\n\n"
            
            response += "**Drink at these times:**\n"
            response += "• 7 AM - After waking up\n"
            response += "• 9 AM - Mid-morning\n"
            response += "• 12 PM - Before lunch\n"
            response += "• 3 PM - Afternoon\n"
            response += "• 6 PM - Evening\n"
            response += "• 8 PM - After dinner\n\n"
            
            response += "💡 **Hydration Tips:**\n"
            response += "✓ Carry water bottle everywhere\n"
            response += "✓ Drink before you feel thirsty\n"
            response += "✓ Add lemon/mint for taste\n"
            response += "✓ More water during workouts\n"
        else:
            response += "**🎉 Excellent! Goal achieved!**\n\n"
            response += "**Benefits:**\n"
            response += "✓ Better metabolism\n"
            response += "✓ Glowing skin\n"
            response += "✓ More energy\n"
            response += "✓ Better digestion\n"
        
        return response
    
    
    # ========== CALORIES ==========
    calorie_keywords = ['calorie', 'calories', 'how much should i eat', 'daily calories',
                        'calorie intake', 'how many calories', 'kcal']
    
    if any(keyword in message_lower for keyword in calorie_keywords):
        response = f"📊 **Calorie Guide for {username}**\n\n"
        
        response += f"**Your Details:**\n"
        response += f"• Gender: {gender}\n"
        response += f"• Goal: {goal or 'Maintain'}\n"
        response += f"• Activity: {activity_level or 'Moderate'}\n\n"
        
        response += f"**Daily Needs:**\n"
        response += f"• Maintenance: {base_cal} kcal (to maintain weight)\n"
        response += f"• Your Target: {target_cal} kcal (for your goal)\n\n"
        
        response += "**Macro Split:**\n"
        if goal == "Weight Loss":
            response += "• Protein: 30% (~150g) - High\n"
            response += "• Carbs: 40% (~180g) - Moderate\n"
            response += "• Fats: 30% (~60g) - Moderate\n"
        elif goal == "Weight Gain":
            response += "• Protein: 25% (~180g)\n"
            response += "• Carbs: 50% (~360g) - High\n"
            response += "• Fats: 25% (~80g)\n"
        else:
            response += "• Protein: 25% (~125g)\n"
            response += "• Carbs: 50% (~275g)\n"
            response += "• Fats: 25% (~60g)\n"
        
        response += f"\n**Today's Status:**\n"
        response += f"• Eaten: {calories_today} kcal\n"
        response += f"• Burnt: {workout_today} kcal\n"
        response += f"• Net: {calories_today - workout_today} kcal\n"
        
        if calories_today > 0:
            diff = calories_today - target_cal
            if diff > 0:
                response += f"\n⚠️ {diff} kcal over! Walk {int(diff/5)} min to burn it"
            else:
                response += f"\n✅ On track! {abs(diff)} kcal under target"
        
        return response
    
    
    # ========== GREETINGS / HELP ==========
    greeting_keywords = ['hi', 'hello', 'hey', 'help', 'start', 'what can you do',
                         'guide', 'how to use', 'commands']
    
    if any(keyword in message_lower for keyword in greeting_keywords) or len(message_lower) < 10:
        response = f"👋 **Hi {username}! I'm Your AI Fitness Coach**\n\n"
        
        response += "**I can help you with:**\n\n"
        response += "🥗 **Diet Plans**\n"
        response += "   Ask: 'diet plan', 'what to eat', 'meal plan'\n\n"
        
        response += "💪 **Workout Routines**\n"
        response += "   Ask: 'workout plan', 'exercise routine'\n\n"
        
        response += "📊 **Health Check**\n"
        response += "   Ask: 'my BMI', 'health status', 'am I healthy'\n\n"
        
        response += "💧 **Water Tracking**\n"
        response += "   Ask: 'water intake', 'hydration'\n\n"
        
        response += "🔥 **Calorie Info**\n"
        response += "   Ask: 'how many calories', 'calorie needs'\n\n"
        
        response += "🍳 **Meal Ideas**\n"
        response += "   Ask: 'breakfast ideas', 'what to eat'\n\n"
        
        if calories_today > 0 or workout_today > 0:
            response += f"**Your Today's Stats:**\n"
            response += f"• Calories eaten: {calories_today} kcal\n"
            response += f"• Calories burnt: {workout_today} kcal\n"
            response += f"• Water drunk: {water_today} ml\n\n"
        
        response += "**Just type naturally!** For example:\n"
        response += "• 'I want to lose weight'\n"
        response += "• 'Give me workout for fat loss'\n"
        response += "• 'What should I eat for breakfast'\n"
        response += "• 'Am I healthy?'\n"
        
        return response
    
    
    # ========== DEFAULT / DIDN'T UNDERSTAND ==========
    response = f"🤔 I'm not sure I understood that, {username}.\n\n"
    response += "**I can help you with:**\n"
    response += "• Diet plans (say: 'diet plan' or 'meal plan')\n"
    response += "• Workouts (say: 'workout' or 'exercise')\n"
    response += "• Health check (say: 'my BMI' or 'health status')\n"
    response += "• Water intake (say: 'water' or 'hydration')\n"
    response += "• Calories (say: 'calories' or 'how much to eat')\n"
    response += "• Breakfast ideas (say: 'breakfast')\n\n"
    response += "Try asking in a simple way! 😊"
    
    return response

@app.route('/notifications')
def notifications():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT id, message, type, is_read, created_at FROM notifications WHERE user_id=? ORDER BY created_at DESC LIMIT 50",
             (user_id,))
    notifs = c.fetchall()
    
    c.execute("UPDATE notifications SET is_read=1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()
    
    return render_template('notifications.html', notifications=notifs)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    if request.method == 'POST':
        water_time = request.form.get('water_reminder_time')
        sleep_time = request.form.get('sleep_reminder_time')
        
        conn = get_db_conn()
        c = conn.cursor()
        c.execute("UPDATE users SET water_reminder_time=?, sleep_reminder_time=? WHERE id=?",
                 (water_time, sleep_time, user_id))
        conn.commit()
        conn.close()
        
        flash("✅ Reminder settings updated", "success")
        return redirect(url_for('settings'))
    
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT water_reminder_time, sleep_reminder_time FROM users WHERE id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    
    water_time = row[0] if row else "09:00"
    sleep_time = row[1] if row else "22:00"
    
    return render_template('settings.html', water_time=water_time, sleep_time=sleep_time)

@app.route('/premium')
def premium():
    return render_template('premium.html')

@app.route('/process_payment', methods=['POST'])
def process_payment():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    plan_type = request.form.get('plan_type')
    
    if plan_type == 'monthly':
        amount = 49
        days_add = 30
    elif plan_type == 'yearly':
        amount = 499
        days_add = 365
    else:
        flash("Invalid plan", "danger")
        return redirect(url_for('premium'))
    
    premium_expiry = (date.today() + timedelta(days=days_add)).isoformat()
    transaction_id = f"TXN_{user_id}_{int(datetime.now().timestamp())}"
    
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET is_premium=1, premium_expiry=? WHERE id=?", (premium_expiry, user_id))
    c.execute("INSERT INTO payment_logs (user_id, amount, plan_type, payment_status, transaction_id, payment_date) VALUES (?, ?, ?, ?, ?, ?)",
             (user_id, amount, plan_type, "SUCCESS", transaction_id, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    
    add_notification(user_id, f"🎉 Premium activated! Access until {premium_expiry}", "success")
    flash(f"✅ Premium {plan_type} activated! Access until {premium_expiry}", "success")
    
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)