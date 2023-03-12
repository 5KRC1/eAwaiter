from bs4 import BeautifulSoup

from datetime import datetime, timedelta
import requests
from utils.exception import ChangingMealsException


class ApiNavigator:
    session = requests.Session()

    def __init__(self, **kwargs):
        username = ""
        password = ""

    def login(self):
        """Logs User In & Creates Session"""
        login_url = "https://www.easistent.com/p/ajax_prijava"
        data = {
            "uporabnik": self.username,
            "geslo": self.password,
            "pin": "",
            "captcha": "",
            "koda": "",
        }
        login = self.session.post(login_url, data=data)
        return login

    def get_menu_ids(self):
        # get menu ids
        meals_url = "https://www.easistent.com/dijaki/ajax_prehrana_obroki_seznam"
        response = self.session.get(meals_url)
        soup = BeautifulSoup(response.content, "html.parser")
        id = "ednevnik-seznam_ur_teden"
        meal_ids = []
        for i in range(6):
            meal_id = soup.find(class_=id).find_all("tr")[i + 1]
            if i == 0:
                meal_id = meal_id.find_all("td")[1].get("id")
            else:
                meal_id = meal_id.findChildren()[0].get("id")
            meal_id = meal_id.split("-")[4]
            meal_ids.append(meal_id)
        return meal_ids

    def get_meal_data(self, week_num: int, meals: dict, monday: datetime) -> list:
        # return all meals for a week
        data = {
            "qversion": 1,  # num of tries
            "teden": week_num,  # num of week before (if 4 will get 5)
            "smer": "naprej",  # direction
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        meals_url = "https://www.easistent.com/dijaki/ajax_prehrana_obroki_seznam"
        site = self.session.post(meals_url, data=data, headers=headers)
        soup = BeautifulSoup(site.content, "html.parser")
        id = "ednevnik-seznam_ur_teden"

        # get meal data
        week_data = (
            []
        )  # [[{meal_text | string, able_to_change | Bool, date | date, meal_id | str, selected | bool}, ...], ...]
        for i in range(5):  # for each day of week
            date = monday + timedelta(days=i)
            day = date.strftime("%Y-%m-%d")

            day_data = []  # each day (5meals)
            for meal_id in list(meals.keys()):
                meal_html_id = f"{id}-td-malica-{meal_id}-{day}-0"  # class of meal tags
                meal_container = soup.find("td", id=meal_html_id).find(
                    "div"
                )  # found in all meals

                """
                if not 3rd div:
                    is_past => look     # unable to change
                        if more than 2 elements
                            is_selected
                        else 
                            is_normal

                else
                    is_present or future or future_loaded => look
                        if not 3rd div
                            future_not_loaded => no data
                            
                        if 1st element in 3rd div == a  # able to change
                            future loaded normal
                            
                        if 1st element in 3rd div == image
                            is_selected (future or present)
                            
                            check day differance
                                if differance more than 8 days    # able to change
                                else        # unable to change
                            
                        if 1st element in 3rd div == span   # unable to change
                            normal present
                """
                if len(meal_container.find_all("div")) < 2:
                    # holidays
                    changable = False
                    selected = False
                    meal_text = ""
                    meal_data = {
                        "meal_text": meal_text,
                        "meal_id": meal_id,
                        "date": day,
                        "changable": changable,
                        "selected": selected,
                    }
                    day_data.append(meal_data)
                    continue

                if len(meal_container.find_all("div")) < 3:
                    # past or future not loaded
                    changable = False
                    selected = True

                    second_div = meal_container.find_all("div")[
                        1
                    ]  # if text => past else future
                    meal_text = second_div.text.strip()
                    if (
                        len(list(meal_container.findChildren(recursive=False))) < 3
                    ):  # if tags => past not selected
                        # if len(second_div.find_all(True)) > 0:  #finds all tags, no text
                        # future => not loaded
                        # meal_text = ""
                        if meal_text == "Prijava":  # future
                            meal_text = ""
                        # past not selected
                        selected = False

                    meal_data = {
                        "meal_text": meal_text,
                        "meal_id": meal_id,
                        "date": day,
                        "changable": changable,
                        "selected": selected,
                    }
                    day_data.append(meal_data)
                    continue

                second_div = meal_container.find_all("div")[
                    1
                ]  # if text => past else future
                meal_text = second_div.text.strip()

                third_div = meal_container.find_all("div")[2]
                if len(list(third_div.findChildren(recursive=False))) < 3:
                    # future normal or present
                    selected = False
                    changable = False

                    if (
                        third_div.find_all(True)[0].text == "Prijava"
                    ):  # present would be "Izbira menija ni več mogoča"
                        changable = True

                    meal_data = {
                        "meal_text": meal_text,
                        "meal_id": meal_id,
                        "date": day,
                        "changable": changable,
                        "selected": selected,
                    }
                    day_data.append(meal_data)
                    continue

                # selected present or future
                # check day differance -> more than 8  is changable
                today = datetime.today()
                changable = True
                selected = True
                if (date - today).days <= 8:
                    # present => not able to change
                    changable = False
                if (
                    third_div.find_all("span")[0].text.strip() == "Odjavljen"
                ):  # could also be Prijavljen, Naročen
                    selected = False
                meal_data = {
                    "meal_text": meal_text,
                    "meal_id": meal_id,
                    "date": day,
                    "changable": changable,
                    "selected": selected,
                }
                day_data.append(meal_data)
            week_data.append(day_data)
        return week_data

    def prijava_odjava(self, action: str, meal_id: str, date: datetime) -> bool:
        """
        session = session where logged in
        action = "prijava" or "odjava"
        meal_id = what to change meal to
        date = date of changing menu
        """
        url = "https://www.easistent.com/dijaki/ajax_prehrana_obroki_prijava"
        data = {
            "tip_prehrane": "malica",
            "id_lokacija": "0",
            "akcija": f"{action}",  # either "prijava" or "odjava"
            "id_meni": f"{meal_id}",  # meals ids (see main_screen)
            "datum": f"{date}",  # date (MainScreen().date_of_menu)
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest",
        }
        try:
            response = self.session.post(url, data=data, headers=headers)
            if not response.json()["status"]:  # "ok" if successful "" if unsuccessful
                raise ChangingMealsException(
                    f"Unable to change meal ({action} to '{meal_id}' meal) for {date}!"
                )
            # app.send_notification("Success", "Meal changed", True)
            self.send_mail(f"Meal changed ({action} to '{meal_id}' meal) for {date}!")
            return True
        except Exception as e:
            self.send_mail(e)
            return False

    def send_mail(self, message: str):
        print(message)
