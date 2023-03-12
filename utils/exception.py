class UserLoginException(Exception):
    """Exception when logging in"""

    pass


class MealFetchingException(Exception):
    """Exception when no meal ids fetched"""

    pass


class ChangingMealsException(Exception):
    """Exception when unable to change meal"""

    pass
