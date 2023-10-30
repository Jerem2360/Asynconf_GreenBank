import json


class Vehicle:
    def __init__(self, energy_type, kilometers, vehicle_type, assembling_year, passenger_count):
        self.energy = energy_type
        self.kilometers = kilometers
        self.type = vehicle_type
        self.year = assembling_year
        self.passenger_count = passenger_count

    def calculate_grade(self):
        with open("data/energy_grades.json") as fs:
            energy_grades = json.load(fs)
        energy_grade = energy_grades.get(self.energy, None)

        with open("data/kilometer_grades.json") as fs:
            kilometer_grades = json.load(fs)
        kilometer_grade = None
        for k, v in kilometer_grades.items():
            if (self.kilometers / 1000) < int(k):
                kilometer_grade = v
                break

        with open("data/vehicle_grades.json") as fs:
            vehicle_grades = json.load(fs)
        vehicle_grade = vehicle_grades.get(self.type, None)

        with open("data/year_grades.json") as fs:
            year_grades = json.load(fs)
        year_grade = None
        for k, v in year_grades.items():
            if self.year < int(k):
                year_grade = v
                break

        return energy_grade + kilometer_grade + vehicle_grade + year_grade

    def calculate_base_borrowing_rate(self):
        grade = self.calculate_grade()

        with open("data/base_borrowing_rates.json") as fs:
            rates = json.load(fs)
        rate = None
        for k, v in rates.items():
            if grade <= int(k):
                rate = v
                break

        return rate

    def calculate_borrowing_rate(self):
        base_rate = self.calculate_base_borrowing_rate()

        with open("data/passenger_borrowing_rates.json") as fs:
            passenger_rates = json.load(fs)

        rate_addition = passenger_rates.get(str(self.passenger_count), None)

        return base_rate + rate_addition

