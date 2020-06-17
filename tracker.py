import csv
from collections import defaultdict
import datetime

from colorama import Fore, Back, Style
import numpy as np


# nutriens i care about
NUTRIENTS = {
    1008: 'Calories',
    1005: 'Total Carbs',
    1004: 'Total Fat',
    1003: 'Protein',
    2000: 'Sugar',
    1079: 'Fiber',
}

# default list of available units (used if not in database)
FALLBACK_UNITS = {
    'gram': 1,
    'kg': 1000,
    'cup': 150,
    'oz': 28.3,
    'lb': 454,
}


def get_info(food: int):
    '''get the nutrient info of a food'''
    info = defaultdict(lambda: 0)
    with open('data/food_nutrient.csv', 'r') as f:
        reader = csv.reader(f)
        next(reader) # remove the first line, the header
        for line in reader:
            food_ID = int(line[1])
            nutrient_ID = int( line[2])
            amount = float(line[3])
            if food_ID == food and amount > 0:
                info[nutrient_ID] = amount
    return info


def get_conversion_factor(food: int, unit: str):
    '''get the food in unit and convert it into gram'''
    valid_unit = []
    with open('data/food_portion.csv', 'r') as f:
        reader = csv.reader(f)
        next(reader) # remove the first line, the header
        for line in reader:
            food_ID = int(line[1])
            quantity = float(line[3])
            modifier = (line[6])
            gram = float(line[7])
            
            if food_ID == food:
                valid_unit.append(modifier)
                if unit in modifier:
                    return gram / quantity

    print(f'{Fore.GREEN}{unit}{Style.RESET_ALL} was not found for food {food}, attempting fallback')
    if unit in FALLBACK_UNITS:
        return FALLBACK_UNITS[unit]

    raise ValueError(f'{Fore.GREEN}{unit}{Style.RESET_ALL} was not found for food {food}. Valid options: {valid_unit}')


def lookup_food(name: str):
    '''get the food ID of the food, and default unit if available'''
    with open('foodID.txt', 'r') as f:
        for line in f:
            food, ID, *data = line.strip().split()
            if name == food:
                return [int(ID), *data]
    raise ValueError(f'{Fore.GREEN}{name}{Style.RESET_ALL} is not in the database.')


def process_line(line):
    '''get the nutrients of the corrosponding food, in array'''
    components = line.strip().split() # line.strip delet the spance before and after the line 
    
    if len(components) == 3:
        # If 3 parts, assume they are amount, unit, food
        amount, unit, food = components
        food_ID = lookup_food(food)[0]
    elif len(components) == 2:
        # If 2 parts, assume they are amount+food. Lookup the default unit.
        amount, food = components
        food_ID, unit = lookup_food(food)
    else:
        raise ValueError(f'Error processing line: {line}')

    nutrient_info = get_info(food_ID)
    amount_in_g = get_conversion_factor(food_ID, unit) * float(amount)
    nutrients = np.array([ nutrient_info[key] for key in NUTRIENTS], dtype=float)
    nutrients *= amount_in_g/100

    print(
        ' •',
        amount, unit,
        f'{Fore.GREEN}{food}{Style.RESET_ALL}',
        f'{Style.DIM}({amount_in_g:,.1f} g){Style.RESET_ALL}'
    )
    display_nutrients(nutrients, indent=1)
    return nutrients

def display_nutrients(values, indent=0):
    """Display the given array of nutrient amounts in a nice table."""
    for n, a in zip(NUTRIENTS.values(), values):
        label = f'{Fore.BLUE}{n:13s}{Style.RESET_ALL}'
        amount = f'{a:9,.1f}'
        print('   ' * indent + f'{label}{Style.DIM}│{Style.RESET_ALL}{amount}')
    print()

nutrients = []
filename = datetime.datetime.today().strftime('%Y-%m-%d') + '.txt'
print(f'{Style.DIM}Opening {filename}...{Style.RESET_ALL}')
with open(f'../../what do i eat today/{filename}', 'r') as f:
    for line in f:
        if line.strip():
            nutrients.append(process_line(line))
nutrients = np.array(nutrients)
total = nutrients.sum(axis=0)

print('┏' + '━' * 21 + '┓')
print('┃{:^21s}┃'.format('Total'))
print('┗' + '━' * 21 + '┛')
display_nutrients(total)

###### Calculate body fat change #####
BMR = 1400
calories = total[0]
delta_fat = (calories - BMR)/9
print(
    f'{Fore.BLUE}Body Fat Change:{Style.RESET_ALL} {delta_fat:+6.1f} g',
    f'{Style.DIM}(Assuming BMR of {BMR:.1f} kcal/day){Style.RESET_ALL}'
)
print()

##### Display proportion from carbs, fat, protein #####
BAR_WIDTH = 70
calorie_breakdown = {
    'Carbs': (total[1] * 4, Back.RED),
    'Fat': (total[2] * 9, Back.BLUE),
    'Protein': (total[3] * 4, Back.GREEN),
}

# Display Bar
print(f'{{:^{BAR_WIDTH}s}}'.format('Calorie Breakdown'))
print()
for key, info in calorie_breakdown.items():
    amount, color = info
    proportion = amount/calories
    chars = int(round(BAR_WIDTH * proportion))

    label = f'{key} ({proportion*100:.1f}%)'
    template = f'{color}{Fore.BLACK}{{:^{chars}s}}{Style.RESET_ALL}'
    print(template.format(label), end='')
print()
print()
