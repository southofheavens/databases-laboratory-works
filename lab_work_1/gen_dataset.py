import csv
import random
import time

def generate_instrument_data(num_records):
    instrument_types = ["electric guitar", "acoustic guitar", "bass guitar", "piano", "keyboard", "drums", "violin", "cello", "trumpet", "saxophone", "flute", "clarinet"]
    instrument_families = ["stringed", "keyboard", "percussion", "woodwind", "brass"]
    manufacturers = ["Fender", "Gibson", "Yamaha", "Steinway", "Pearl", "Selmer", "Martin", "Taylor", "Roland", "Korg"]
    countries = ["USA", "Japan", "Germany", "China", "Italy", "France", "UK", "Korea"]

    data = []
    for i in range(num_records):
        name = f"{random.choice(manufacturers)} {random.choice(instrument_types).title()} Model {random.randint(100, 999)}"
        instrument_type = random.choice(instrument_types)
        family = random.choice(instrument_families)
        manufacturer = random.choice(manufacturers)
        origin_country = random.choice(countries)
        year = random.randint(1900, 2023)
        price = round(random.uniform(50, 10000), 2)
        description = f"A {manufacturer} {instrument_type} made in {origin_country} in {year}."

        data.append([name, instrument_type, family, manufacturer, origin_country, year, price, description])

    return data


def write_to_csv(data, filename="musical_instruments.csv"):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["name", "type", "family", "manufacturer", "origin_country", "year_introduced", "price", "description"])
        writer.writerows(data)


if __name__ == "__main__":
    num_records = 5500000
    start_time = time.time()
    print(f"Генерация {num_records} записей...")
    data = generate_instrument_data(num_records)
    print(f"Запись в CSV...")
    write_to_csv(data)
    end_time = time.time()
    print(f"Готово! Время выполнения: {end_time - start_time:.2f} секунд")
