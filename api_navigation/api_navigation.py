from bs4 import BeautifulSoup

from datetime import datetime, timedelta
import requests

class ApiNavigator():
    session = requests.Session()

    def __init__(self, **kwargs):
        username = ""
        password = ""
    
    def login(self):
        '''Logs User In & Creates Session'''
        login_url = "https://www.easistent.com/p/ajax_prijava"
        data = {
                "uporabnik": self.username,
                "geslo": self.password,
                "pin":"",
                "captcha":"",
                "koda":""
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


    def get_meal_data(self, week_num, meals, monday):
        # return all meals + just subbed meals
        """
        returns:

        """
        data = {
                "qversion": 1, #num of tries
                "teden": week_num, #num of week before (if 4 will get 5)
                "smer": "naprej" # direction
                }
        headers = {
                "Content-Type": "application/x-www-form-urlencoded"
                }
        meals_url = "https://www.easistent.com/dijaki/ajax_prehrana_obroki_seznam"
        site = self.session.post(meals_url, data=data, headers=headers)
        soup = BeautifulSoup(site.content, "html.parser")
        id = "ednevnik-seznam_ur_teden"

        # get meals selected
        week_data_selected = []  # [[meal_text | string, able_to_change | Bool, date | date], ...]
        week_data_all = []  # [[[meal_text | string, able_to_change | Bool, date | date], ...], ...]
        for i in range(5):  # for each day of week
            day = monday + timedelta(days=i)
            day = day.strftime("%Y-%m-%d")
            day_data_selected = []
            day_data_all = []
            changed = True
            for meal_id in list(meals.keys()):
                meal_data_all = []
                meal_html_id = f"{id}-td-malica-{meal_id}-{day}-0"
                meal_container = soup.find("td", id=meal_html_id)

                # get meal text && check if holidays
                try:
                    meal_text = meal_container.find("div").find_all("div")[1].text.strip()
                    
                    if meal_text in ["Izbira menija ni več mogoča", "Prijava", "Nepravočasna odjava"]:
                        raise IndexError
                except Exception as e:
                    if e == IndexError:
                        # no meal that day => should already be signed off
                        meal_text = ""
                        changed = False
                        day_data_selected.append(meal_text)
                        day_data_selected.append(changed)
                        day_data_selected.append(day)
                        day_data_selected.append(meal_id)
                        day_data_all.append(day_data_selected)
                        # break
                        continue
                    self.send_mail(e)
                    # break
                    continue
                # get selected meal
                meal_change = meal_container.find("div").find_all("div")[2] # div | could be Naročen(date)Odjava / Odjava
                try:
                    meal_option = meal_change.find("a").text.strip()
                except:
                    meal_option = ""
                if meal_option and meal_option == "Prijava":  # could be "Prijava" or "Odjava"
                    # not selected meal
                    # meal_text = ""
                    # changed = False
                    meal_data_all.append(meal_text)
                    meal_data_all.append(changed)
                    meal_data_all.append(day)
                    meal_data_all.append(meal_id)
                    day_data_all.append(meal_data_all)
                    continue
                # if no selected => prijava settings
                # see if can be changed or just be signed off
                if meal_change.find_all("span")[0].text.strip() in ["Izbira menija ni več mogoča", "Nepravočasna odjava"]:    # could be "Naročen" or "Izbira menija ni več mogoča"
                    changed = False
                day_data_selected.append(meal_text)
                day_data_selected.append(changed)
                day_data_selected.append(day)
                day_data_selected.append(meal_id)
                day_data_all.append(day_data_selected)
                # break
            week_data_selected.append(day_data_selected)
            week_data_all.append(day_data_all)
        return week_data_selected, week_data_all
    

    def prijava_odjava(self, action, meal_id, date):
        '''
        session = session where logged in
        action = "prijava" or "odjava"
        meal_id = what to change meal to
        date = date of changing menu
        '''
        url = "https://www.easistent.com/dijaki/ajax_prehrana_obroki_prijava"
        data = {
                "tip_prehrane": "malica",
                "id_lokacija": "0",
                "akcija": f"{action}", # either "prijava" or "odjava"
                "id_meni": f"{meal_id}", # meals ids (see main_screen)
                "datum": f"{date}" # date (MainScreen().date_of_menu)
                }
        headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Requested-With": "XMLHttpRequest"
                }
        try:
            response = self.session.post(url, data=data, headers=headers)
            if not response.json()["status"]: # "ok" if successful "" if unsuccessful
                raise CustomException(f"Unable to change meal for {date}")
            # app.send_notification("Success", "Meal changed", True)
            self.send_mail(f"Meal changed for {date}")
            return True
        except Exception as e:
            self.send_mail(e)
            return False
    

    def send_mail(self, message):
        print(message)
