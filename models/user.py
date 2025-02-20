# user.py
class User:
    def __init__(self, user_id: int, name: str, height: float, weight: float, age: int, activity_level: str, workouts_per_week: int):
        self.user_id = user_id
        self.name = name
        self.height = height
        self.weight = weight
        self.age = age
        self.activity_level = activity_level
        self.workouts_per_week = workouts_per_week

    def update_weight(self, new_weight: float):
        self.weight = new_weight

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "name": self.name,
            "height": self.height,
            "weight": self.weight,
            "age": self.age,
            "activity_level": self.activity_level,
            "workouts_per_week": self.workouts_per_week
        }
