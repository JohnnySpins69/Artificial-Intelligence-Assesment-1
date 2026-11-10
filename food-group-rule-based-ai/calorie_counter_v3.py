# ==========================================================
#  DAILY CALORIE COUNTER  (version_3 )
#  What it does: you type in how many calories you want to eat
#  today, then you add the foods you ate and it keeps a running
#  total and tells you how many calories you have left.
#  It uses the FOOD-DATA-GROUP1-5.csv files for the food info.
#
#  NOTE: I got help from Claude (Anthropic) to write this and then I checked it and changed bits myself.
# ==========================================================
 
import glob   # lets me search a folder for files that match a name pattern
import os     # used to join the folder name and file name together properly
import re     # "regular expressions", I use this to read things like "150g" or "0.2 kg"
import pandas as pd   # pandas = the library for working with tables (like Excel but in python)
 
# 1. SETTINGS
# This is the name of the folder where the 5 csv files are.
# "." would mean the same folder as this script. If it can't find the files
# then this is the line to change (can also use the full path, like
# FOLDER = r"C:\Users\YourName\Documents\FINAL FOOD DATASET")
FOLDER = "FINAL FOOD DATASET"
 
# How many grams are in each unit. I use this to turn everything into grams
# because the dataset gives calories per 100 g.
GRAMS_PER_UNIT = {
    "g": 1,           # grams  
    "kg": 1000,       # kilogram
    "oz": 28.3495,    # ounces
    "lb": 453.592,    # pounds
}
 
# Other ways people might type the units (so "kilos" and "pounds" work as well).
UNIT_NAMES = {
    "g": "g", "gram": "g", "grams": "g",
    "kg": "kg", "kilo": "kg", "kilos": "kg", "kilogram": "kg", "kilograms": "kg",
    "oz": "oz", "ounce": "oz", "ounces": "oz",
    "lb": "lb", "lbs": "lb", "pound": "lb", "pounds": "lb",
}
 
# 2. LOAD THE DATA
# glob finds all the files in the folder that start with FOOD-DATA-GROUP and end in .csv
files = sorted(glob.glob(os.path.join(FOLDER, "FOOD-DATA-GROUP*.csv")))
 
# If it found nothing then the folder name is probably wrong, so stop and say why
if not files:
    raise SystemExit(f"No FOOD-DATA-GROUP*.csv files found in '{FOLDER}'. "
                     "Check the FOLDER name at the top, or use the full path to the folder.")
 
# Read each csv and stick them all together into one big table (stacked on top of each other)
foods = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
 
# Some csv files have a blank first column called "Unnamed: 0", we don't need it so remove it
foods = foods.loc[:, ~foods.columns.str.contains("^Unnamed")]
 
# Remove any food that appears twice
foods = foods.drop_duplicates()
print(f"Loaded {len(foods)} foods from {len(files)} files.")
 
 
def find_col(*words):
    """Looks through the column names and returns the first one that has all the words in it.
    I did it like this so it still works if the column is called 'Caloric Value' or 'calories' etc."""
    for col in foods.columns:
        if all(w in col.lower() for w in words):
            return col
    return None   # nothing matched
 
 
# Work out which columns are the food name and the calories
NAME = find_col("food") or foods.columns[0]   # if no "food" column just use the first one
CAL = find_col("calor")
if CAL is None:
    print("Columns found:", list(foods.columns))
    raise SystemExit("Couldn't find a calories column. Check the column list above.")
 
foods[NAME] = foods[NAME].astype(str)   # make sure the names are text so searching works
print(f"Using '{NAME}' for food names and '{CAL}' for calories (values are per 100 g).\n")
 
# 3. ASCII ART AND LAYOUT
# (r""" ... """ means a raw string so the backslashes in the art don't break stuff.) "weird looking but works :D"
BANNER = r"""
+==============================================================+
||  ____        _ _          ____      _            _         ||
|| |  _ \  __ _(_) |_   _   / ___|__ _| | ___  _ __(_) ___    ||
|| | | | |/ _` | | | | | | | |   / _` | |/ _ \| '__| |/ _ \   ||
|| | |_| | (_| | | | |_| | | |__| (_| | | (_) | |  | |  __/   ||
|| |____/ \__,_|_|_|\__, |  \____\__,_|_|\___/|_|  |_|\___|   ||
||                  |___/        C O U N T E R                ||
||                                                            ||"""                                                         
PLATE = r"""||                                                            ||                                                 
||         _.---._                                            ||
||       .'  o o  '.      Let's count what                    ||
||      /     ^     \     you ate today!                      ||
||      |   \___/   |                                         ||
||       \         /                                          ||
||        '._____.'                                           ||
||                                     Sponsored by BIG FOOD  ||
+==============================================================+
"""
LINE = "=" * 56   # just a long line of = signs that I reuse to make boxes
 
 
# 4. FUNCTIONS FOR ASKING THE USER THINGS
# I made these so the program doesn't crash if someone types something silly.
# Each one keeps asking (while True) until the answer is valid.
 
def ask_number(prompt, low, high):
    """Asks for a number between low and high. Keeps asking until it gets a good one.
    Also works with decimals and commas (2000.5 or 2000,5)."""
    while True:
        text = input(prompt).strip().replace(",", ".")   # change comma to dot so python understands it
        try:
            value = float(text)   # try to turn the text into a number
        except ValueError:        # this happens if they typed letters
            print("  [!] That's not a number. Please type digits only, e.g. 2000.")
            continue              # go back to the start of the loop and ask again
        if low <= value <= high:  # check it's in the allowed range
            return value
        print(f"  [!] Please enter a number between {low:g} and {high:g}.")
 
 
def ask_weight(prompt):
    """Asks how much food was eaten and works out the grams.
    You can type: 150  (counts as grams), 150g, 0.2kg, 6oz, 1lb ... and it converts it."""
    # This pattern looks for: a number, then maybe a space, then maybe a unit word.
    pattern = re.compile(r"^\s*(\d+(?:[.,]\d+)?)\s*([a-zA-Z]*)\s*$")
    while True:
        text = input(prompt)
        match = pattern.match(text)
        if not match:
            print("  [!] I didn't get that. Try something like 150, 150g, 0.2kg, 6oz or 1lb.")
            continue
 
        amount = float(match.group(1).replace(",", "."))   # the number part
        unit_text = match.group(2).lower()                  # the unit part (could be empty)
 
        if unit_text == "":
            unit = "g"                         # no unit typed so assume grams
        elif unit_text in UNIT_NAMES:
            unit = UNIT_NAMES[unit_text]       # turn "kilos" into "kg" etc
        else:
            print(f"  [!] I don't know the unit '{unit_text}'. Use g, kg, oz or lb.")
            continue
 
        grams = amount * GRAMS_PER_UNIT[unit]   # convert to grams
 
        if grams < 1 or grams > 5000:           # stops silly numbers like 0 or 900 kg
            print("  [!] That's too small or too big. Please enter between 1 g and 5 kg.")
            continue
 
        if unit != "g":
            print(f"  ({amount:g} {unit} = {grams:.0f} g)")   # show the conversion so they can check it
        return grams
 
 
def ask_choice(prompt, low, high):
    """Like ask_number but only whole numbers. Used when picking from the list."""
    while True:
        text = input(prompt).strip()
        if text.isdigit() and low <= int(text) <= high:   # isdigit() is True if it's only digits
            return int(text)
        print(f"  [!] Please type a whole number from {low} to {high}.")
 
 
def ask_yes_no(prompt):
    """Asks a yes/no question and keeps asking until it gets y or n."""
    while True:
        answer = input(prompt).strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("  [!] Please type y or n.")

 
# 5. FUNCTIONS FOR SHOWING THINGS
def progress_bar(eaten, target, width=30):
    """Makes a bar like [##########--------------------]  35%  to show how much of the target is used."""
    ratio = eaten / target                       # e.g. 700 / 2000 = 0.35
    filled = min(width, int(ratio * width))      # how many # to draw (never more than the width)
    bar = "#" * filled + "-" * (width - filled)  # # for done, - for not done yet
    warn = "  !! OVER" if ratio > 1 else ""      # add a warning if they went past the target
    return f"[{bar}] {ratio * 100:3.0f}%{warn}"
 
 
def show_status(eaten, target):
    """Prints the progress bar and the calories eaten / left."""
    print(LINE)
    print(" " + progress_bar(eaten, target))
    print(f" Eaten: {eaten:.0f} kcal | Target: {target:.0f} kcal | "
          f"Left: {max(target - eaten, 0):.0f} kcal")   # max(...,0) so "left" never shows a negative
    print(LINE)
 
 
def show_log(log):
    """Prints a table of all the foods that were added."""
    print("\n+----+--------------------------------+--------+---------+")
    print("| #  | Food                           | Grams  |  kcal   |")
    print("+----+--------------------------------+--------+---------+")
    for n, (food, grams, kcal) in enumerate(log, start=1):
        # food[:30] cuts long names to 30 letters so the table doesn't get messy
        print(f"| {n:<2} | {food[:30]:<30} | {grams:>6.0f} | {kcal:>7.0f} |")
    print("+----+--------------------------------+--------+---------+")
 
 
# 6. THE MAIN PART: ONE DAY OF COUNTING
def run_day():
    target = ask_number("How many calories do you want to eat today? (e.g. 2000): ", 500, 10000)
    total = 0   # running total of calories eaten
    log = []    # list that stores everything that was eaten (for the table at the end)
    print("\nType the name of a food, or 'done' when you've finished.")
 
    while True:   # keep going until they type done
        name = input("\nWhat did you eat? > ").strip()
        if name.lower() == "done":
            break
        if len(name) < 2:
            print("  [!] Please type at least 2 letters (or 'done').")
            continue
 
        # Search the food names for what they typed (case=False so "Apple" and "apple" both work)
        # head(8) means only show the first 8 matches so the list isn't massive
        matches = foods[foods[NAME].str.contains(name, case=False, na=False, regex=False)].head(8)
        if matches.empty:
            print("  [!] Couldn't find that. Try a shorter word like 'apple'.")
            continue
 
        print()
        for i, (_, row) in enumerate(matches.iterrows(), start=1):
            print(f"  {i}. {row[NAME]}  ({row[CAL]:.0f} kcal per 100 g)")
        pick = ask_choice("Which one? (number, or 0 to search again): ", 0, len(matches))
        if pick == 0:
            continue                       # go back and search again
        food = matches.iloc[pick - 1]      # pick - 1 because python starts counting at 0
 
        grams = ask_weight("How much did you eat? (e.g. 150, 150g, 0.2kg, 6oz, 1lb): ")
 
        # The data is calories per 100 g so I scale it: (calories / 100) * grams eaten
        # e.g. 52 kcal per 100 g and I ate 150 g -> 52 * 150 / 100 = 78 kcal
        kcal = food[CAL] * grams / 100
        total += kcal
        log.append((food[NAME], grams, kcal))   # save it for the summary table
        print(f"\n  + Added {food[NAME]}: {kcal:.0f} kcal")
        show_status(total, target)
 
    # total calories summary
    print("\n" + LINE)
    print("               YOUR DAY IN REVIEW")
    print(LINE)
    if log:
        show_log(log)
    else:
        print(" You didn't add any food.")
    show_status(total, target)
    if total > target:
        print(f" You went over by {total - target:.0f} kcal.")
    else:
        print(f" You have {target - total:.0f} kcal left. Nice!")
 
 
# 7. START THE PROGRAM
print(BANNER)
print(PLATE)
try:
    while True:
        run_day()
        # ask if they want another go, if not break out of the loop and finish
        if not ask_yes_no("\nTry again with a new day? (y/n): "):
            print("\nThanks for using Daily Calorie Counter. Goodbye!")
            break
        print("\n" + "~" * 56 + "\n")
except (KeyboardInterrupt, EOFError):
    # Ctrl+C (or closing the input) ends up here so it exits nicely instead of a big error
    print("\n\nStopped. Goodbye!")
 