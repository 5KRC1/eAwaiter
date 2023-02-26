
from bs4 import BeautifulSoup

from datetime import datetime, timedelta
import json
import os

from api_navigation.api_navigation import ApiNavigator
from .helpers import *
from utils.exception import CustomException

FORMAT = "%Y-%m-%d %H:%M:%S"
# api = ApiNavigator()

class Waiter():
    def __init__(self, **kwargs):
        self.failed_login = False
        self.api = ApiNavigator()
        self.username = ""
        self.password = ""
        self.disliked_foods = []
        self.preferred_menu = ""
        

    def login(self):
        self.api.username = self.username
        self.api.password = self.password
        login = self.api.login()
        if not login.json()["status"]:
            self.failed_login = True
            return

        # set school info
        self.set_school_info()


    def set_school_info(self):
        date_today = datetime.now()
        curr_month = int(date_today.strftime("%m"))
        curr_year = int(date_today.strftime("%Y"))

        if not os.path.exists("./school_info.txt"):
            self.school_year, self.meal_ids, self.first_week_school = self.init_school_info()
            return self.init_school_info()   # if fails => [], [], ""

        with open("school_info.txt") as f:
            school_info = f.readlines()
            school_info = school_info[0].split("; ")

        # check if data valid
        if curr_month < 9:  # if earlier than september => start of school was year before (curr year - 1)
            school_start_year = curr_year - 1
        else:
            school_start_year = curr_year

        if school_start_year != json.loads(school_info[0])[0]:
            os.remove("school_info.txt")
            return self.set_school_info()

        self.school_year, self.meal_ids, self.first_week_school = json.loads(school_info[0]), json.loads(school_info[1]), datetime.strptime(school_info[2], FORMAT)
        return json.loads(school_info[0]), json.loads(school_info[1]), datetime.strptime(school_info[2], FORMAT)


    def init_school_info(self):
        if self.failed_login:
            return [], [], ""
        date_today = datetime.now()
        curr_month = int(date_today.strftime("%m"))
        curr_year = int(date_today.strftime("%Y"))
        session = self.api.session
        meal_ids = self.api.get_menu_ids()
        meals = {
                meal_ids[0]: "food-drumstick-outline",
                meal_ids[1]: "carrot",
                meal_ids[2]: "food",
                meal_ids[3]: "food-croissant",
                meal_ids[4]: "bowl-mix-outline",
                meal_ids[5]: "basketball"
                }

        # get first day of school && set school year
        if curr_month < 9:  # if earlier than september => start of school was year before (curr year - 1)
            school_start_year = curr_year - 1
        else:
            school_start_year = curr_year

        first_day_school = datetime(school_start_year, 9, 1)    # 1st September == first day of school
        first_week_school = get_monday(first_day_school)

        # set school year
        school_year = [school_start_year, school_start_year + 1]
        school_year_str = json.dumps(school_year)

        meals_str = json.dumps(meals) # reformat meals

        # save to DB
        with open('school_info.txt', 'w') as f:
            data = f"{school_year_str}; {meals_str}; {first_week_school}"
            f.write(data)
        # return info
        return school_year, meals, first_week_school

    
    def service(self):
        self.api.send_mail("Service started!")
    
        # login
        if self.failed_login:
            raise CustomException("Failed to login! Check your credentials!")
        try:
            session = self.api.session
    
            # get info (school)
            if not self.meal_ids:
                raise CustomException("No meal_ids!")

            if self.disliked_foods and self.preferred_menu:
                self.disliked_foods_changer(1)

            if self.favourite_foods and self.default_menu:
                self.favourite_foods_changer()

            if self.disliked_foods:
                self.disliked_foods_changer(2)
    
            self.api.send_mail("service did well")
            return
    
        except Exception as e:
            self.api.send_mail(e)
            return


    def disliked_foods_changer(self, week):
        next_week_num, monday = weeks_in_advance(week, self.first_week_school)

        # get meal data
        meals_data = self.api.get_meal_data(next_week_num, self.meals, monday)[0]

        # get preffered meal
        # if Odjava set to selected meal for the day
        selected_menu = list(self.meals.keys())[int(self.preferred_menu) - 1]

        # compare disliked foods with menus
        for meal_data in meals_data:
            for disliked_food in self.disliked_foods:
                if disliked_food.upper() in meal_data[0]:

                    if not meal_data[1]:
                        break
                    # prijava / odjava
                    success = self.api.prijava_odjava("prijava", selected_menu, meal_data[2])
                    if not success:
                        self.api.prijava_odjava("odjava", meal_data[3], meal_data[2])
                    break


    def favourite_foods_changer(self):
        next_week_num, monday = weeks_in_advance(2, self.first_week_school)

        # get meal data
        meals_data = self.api.get_meal_data(next_week_num, self.meals, monday)[1]

        # get default meal
        # if Odjava => prijavi na prvega in odjavi
        selected_menu = list(self.meals.keys())[int(self.default_menu) - 1]

        # compare favourite foods with menus
        for i in range(5):
            is_subbed = False
            for meal_data in meals_data[i]:    # loop through meals
                for favourite_food in self.favourite_foods:
                    if favourite_food.upper() in meal_data[0]:
                        if not meal_data[1]:
                            break
                        # prijava / odjava
                        success = self.api.prijava_odjava("prijava", meal_data[3], meal_data[2])
                        if success:
                            is_subbed = True
                        break
                if is_subbed:
                    break
            if is_subbed:
                continue
            success = self.api.prijava_odjava("prijava", selected_menu, meals_data[i][0][2])
