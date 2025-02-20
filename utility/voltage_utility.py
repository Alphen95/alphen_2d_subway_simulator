from pprint import pprint

#утилита-ленивка для высчета вольтажей
#в планах интегрировать в основной редачер

engine_resistance = 0.2
positions = {
    "0":{"base_voltage":0,"ballast_resistance":10,"engines_engaged":4,"coil_engagement":100},
    "1":{"base_voltage":750,"ballast_resistance":4.96,"engines_engaged":4,"coil_engagement":35},
    "2":{"base_voltage":750,"ballast_resistance":4.96,"engines_engaged":4,"coil_engagement":100},
    "3":{"base_voltage":750,"ballast_resistance":3.96,"engines_engaged":4,"coil_engagement":100},
    "4":{"base_voltage":750,"ballast_resistance":3.17,"engines_engaged":4,"coil_engagement":100},
    "5":{"base_voltage":750,"ballast_resistance":2.60,"engines_engaged":4,"coil_engagement":100},
    "6":{"base_voltage":750,"ballast_resistance":2.24,"engines_engaged":4,"coil_engagement":100},
    "7":{"base_voltage":750,"ballast_resistance":1.89,"engines_engaged":4,"coil_engagement":100},
    "8":{"base_voltage":750,"ballast_resistance":1.71,"engines_engaged":4,"coil_engagement":100},
    "9":{"base_voltage":750,"ballast_resistance":1.52,"engines_engaged":4,"coil_engagement":100},
    "10":{"base_voltage":750,"ballast_resistance":1.30,"engines_engaged":4,"coil_engagement":100},
    "11":{"base_voltage":750,"ballast_resistance":1.07,"engines_engaged":4,"coil_engagement":100},
    "12":{"base_voltage":750,"ballast_resistance":0.851,"engines_engaged":4,"coil_engagement":100},
    "13":{"base_voltage":750,"ballast_resistance":0.627,"engines_engaged":4,"coil_engagement":100},
    "14":{"base_voltage":750,"ballast_resistance":0.444,"engines_engaged":4,"coil_engagement":100},
    "15":{"base_voltage":750,"ballast_resistance":0.260,"engines_engaged":4,"coil_engagement":100},
    "16":{"base_voltage":750,"ballast_resistance":0.130,"engines_engaged":4,"coil_engagement":100},
    "17":{"base_voltage":750,"ballast_resistance":0.0,"engines_engaged":4,"coil_engagement":100},
    "18":{"base_voltage":750,"ballast_resistance":0.0,"engines_engaged":4,"coil_engagement":100},

    "19":{"base_voltage":750,"ballast_resistance":1.21,"engines_engaged":2,"coil_engagement":100},
    "20":{"base_voltage":750,"ballast_resistance":1.21,"engines_engaged":2,"coil_engagement":100},
    "21":{"base_voltage":750,"ballast_resistance":0.946,"engines_engaged":2,"coil_engagement":100},
    "22":{"base_voltage":750,"ballast_resistance":0.762,"engines_engaged":2,"coil_engagement":100},
    "23":{"base_voltage":750,"ballast_resistance":0.762,"engines_engaged":2,"coil_engagement":100},
    "24":{"base_voltage":750,"ballast_resistance":0.762,"engines_engaged":2,"coil_engagement":100},
    "25":{"base_voltage":750,"ballast_resistance":0.538,"engines_engaged":2,"coil_engagement":100},
    "26":{"base_voltage":750,"ballast_resistance":0.314,"engines_engaged":2,"coil_engagement":100},
    "27":{"base_voltage":750,"ballast_resistance":0.314,"engines_engaged":2,"coil_engagement":100},
    "28":{"base_voltage":750,"ballast_resistance":0.314,"engines_engaged":2,"coil_engagement":100},
    "29":{"base_voltage":750,"ballast_resistance":0.130,"engines_engaged":2,"coil_engagement":100},
    "30":{"base_voltage":750,"ballast_resistance":0.0,"engines_engaged":2,"coil_engagement":100},
    "31":{"base_voltage":750,"ballast_resistance":0.0,"engines_engaged":2,"coil_engagement":100},
    "32":{"base_voltage":750,"ballast_resistance":0.0,"engines_engaged":2,"coil_engagement":78},
    "33":{"base_voltage":750,"ballast_resistance":0.0,"engines_engaged":2,"coil_engagement":55},
    "34":{"base_voltage":750,"ballast_resistance":0.0,"engines_engaged":2,"coil_engagement":44},
    "35":{"base_voltage":750,"ballast_resistance":0.0,"engines_engaged":2,"coil_engagement":35},
    "36":{"base_voltage":750,"ballast_resistance":0.0,"engines_engaged":2,"coil_engagement":35},
}

for position in positions:
    voltage = (positions[position]["base_voltage"]-(positions[position]["base_voltage"]/(positions[position]["ballast_resistance"]+engine_resistance*positions[position]["engines_engaged"])*positions[position]["ballast_resistance"]))/positions[position]["engines_engaged"]
    coils = positions[position]["coil_engagement"]
    positions[position] = {"voltage":round(voltage,2),"coil_engagement":coils}

pprint(positions,sort_dicts=False)