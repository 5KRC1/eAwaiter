from bs4 import BeautifulSoup

from datetime import datetime, timedelta
import json
import os

from api_navigation.api_navigation import ApiNavigator
from .helpers import *
from utils.exception import UserLoginException, MealFetchingException

FORMAT = "%Y-%m-%d %H:%M:%S"
# api = ApiNavigator()


class Waiter:
    def __init__(self, **kwargs):
        self.failed_login = False
        self.api: ApiNavigator = ApiNavigator()
        self.username: str = ""
        self.password: str = ""
        self.disliked_foods: list = []
        self.preferred_menu: str = ""
        self.favourite_foods: list = []
        self.default_menu: str = ""
        self.overwrite_unchangable: bool = False

    def login(self):
        self.api.username = self.username
        self.api.password = self.password
        login = self.api.login()
        if not self.username and not self.password:
            raise UserLoginException("Please fill in the Login form!")
        """
        status: "hide_pin" => when username correct but password wrong
        """
        """
        status: "" => either completely wrong credentials, or wrong login 3x
            {
            'status': '',
            'message': '',
            'errfields': {
                'captcha': 'Ker ste se že več kot trikrat neuspešno prijavili, pokažite, da niste robot.'
                },
            'data': {
                'reset_form': False, 'require_captcha': True
                }
            }

            {
            'status': '',
            'message': 'Preostalo vam je še 9 neuspešnih prijav!',
            'errfields': {
                'profil': 'Dostop trenutno ni mogoč zaradi prehoda v novo šolsko leto 2022/2023.
                            Izvaja se prenos paketov eAsistenta za starše. Hvala za razumevanje.'
                },
            'data': {
                'reset_form': True,
                'require_captcha': False
                }
            }
        """
        # failed to login
        if login.json()["status"] in ["", "hide_pin"]:
            self.failed_login = True
            # captcha => make them login on web
            if list(login.json()["errfields"].keys())[0] == "captcha":
                raise UserLoginException(
                    "Login failed too many times, please try logging in on the web!"
                )
            # else
            raise UserLoginException("Check your credentials and try again!")
        # succeeded to login
        """
        status: "ok" => when login correct
        """
        # set school info
        self.set_school_info()

    def set_school_info(self):
        date_today = datetime.now()
        curr_month = int(date_today.strftime("%m"))
        curr_year = int(date_today.strftime("%Y"))

        if not os.path.exists("./school_info.txt"):
            (
                self.school_year,
                self.meals,
                self.first_week_school,
            ) = self.init_school_info()
            return self.init_school_info()  # if fails => [], [], ""

        with open("school_info.txt") as f:
            school_info = f.readlines()
            school_info = school_info[0].split("; ")

        # check if data valid
        if (
            curr_month < 9
        ):  # if earlier than september => start of school was year before (curr year - 1)
            school_start_year = curr_year - 1
        else:
            school_start_year = curr_year

        if school_start_year != json.loads(school_info[0])[0]:
            os.remove("school_info.txt")
            return self.set_school_info()

        self.school_year, self.meals, self.first_week_school = (
            json.loads(school_info[0]),
            json.loads(school_info[1]),
            datetime.strptime(school_info[2], FORMAT),
        )
        return (
            json.loads(school_info[0]),
            json.loads(school_info[1]),
            datetime.strptime(school_info[2], FORMAT),
        )

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
            meal_ids[5]: "basketball",
        }

        # get first day of school && set school year
        if (
            curr_month < 9
        ):  # if earlier than september => start of school was year before (curr year - 1)
            school_start_year = curr_year - 1
        else:
            school_start_year = curr_year

        first_day_school = datetime(
            school_start_year, 9, 1
        )  # 1st September == first day of school
        first_week_school = get_monday(first_day_school)

        # set school year
        school_year = [school_start_year, school_start_year + 1]
        school_year_str = json.dumps(school_year)

        meals_str = json.dumps(meals)  # reformat meals

        # save to DB
        with open("school_info.txt", "w") as f:
            data = f"{school_year_str}; {meals_str}; {first_week_school}"
            f.write(data)
        # return info
        return school_year, meals, first_week_school

    def service(self):
        # TODO: check if changable and if overwrite
        self.api.send_mail("Service started!")

        # login
        if self.failed_login:
            raise UserLoginException("Failed to login!")
        try:
            session = self.api.session

            # get info (school)
            if not self.meals:
                raise MealFetchingException("No meals' ids!")

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

    def disliked_foods_changer(self, week: int):
        next_week_num, monday = weeks_in_advance(week, self.first_week_school)

        # get meal data
        # meals_data = self.api.get_meal_data(next_week_num, self.meals, monday)[0]
        meals_data = get_selected(
            self.api.get_meal_data(next_week_num, self.meals, monday)
        )

        # get preffered meal
        # if Odjava set to selected meal for the day
        check_odjava = False
        if int(self.preferred_menu) == 0:
            check_odjava = True
        selected_menu = list(self.meals.keys())[int(self.preferred_menu) - 1]

        # compare disliked foods with menus
        for meal_data in meals_data:
            for disliked_food in self.disliked_foods:
                if disliked_food.upper() in meal_data["meal_text"]:
                    if not meal_data["changable"] and not self.overwrite_unchangable:
                        break
                    # prijava / odjava
                    if selected_menu == "Odjava":
                        self.api.prijava_odjava(
                            "odjava", meal_data["meal_id"], meal_data["date"]
                        )
                        break
                    success = self.api.prijava_odjava(
                        "prijava", selected_menu, meal_data["date"]
                    )
                    if not success:
                        self.api.prijava_odjava(
                            "odjava", meal_data["meal_id"], meal_data["date"]
                        )
                    break

    def favourite_foods_changer(self):
        next_week_num, monday = weeks_in_advance(2, self.first_week_school)

        # get meal data
        # meals_data = self.api.get_meal_data(next_week_num, self.meals, monday)[1]
        meals_data = self.api.get_meal_data(next_week_num, self.meals, monday)

        # get default meal
        # if Odjava => prijavi na prvega in odjavi
        check_odjava = False
        if int(self.default_menu) == 0:
            check_odjava = True
        selected_menu = list(self.meals.keys())[int(self.default_menu) - 1]

        # compare favourite foods with menus
        for i in range(5):
            is_subbed = False
            for meal_data in meals_data[i]:  # loop through meals
                for favourite_food in self.favourite_foods:
                    if favourite_food.upper() in meal_data["meal_text"]:
                        if (
                            not meal_data["changable"]
                            and not self.overwrite_unchangable
                        ):
                            break
                        # prijava / odjava
                        success = self.api.prijava_odjava(
                            "prijava", meal_data["meal_id"], meal_data["date"]
                        )
                        if success:
                            is_subbed = True
                        break
                if is_subbed:
                    break
            if is_subbed:
                continue
            if check_odjava:
                # success = self.api.prijava_odjava("prijava", meal_data[i][0]["meal_id"], meals_data[i][0]["date"])
                success = self.api.prijava_odjava(
                    "odjava", meal_data[i][0]["meal_id"], meals_data[i][0]["date"]
                )
                continue
            success = self.api.prijava_odjava(
                "prijava", selected_menu, meals_data[i][0]["date"]
            )
