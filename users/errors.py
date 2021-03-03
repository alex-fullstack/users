class HttpError(Exception):
    status = 0
    message = ''

    def __str__(self):
        return str(self.message)


class UserNotFoundError(HttpError):
    def __init__(self, user_id: int):
        self.message = f'user with id={user_id} not found'
        self.status = 404


class UserCreateError(HttpError):
    def __init__(self, email: str):
        self.message = f'can\'t create user with email={email}'
        self.status = 400


class WrongCredentialsError(HttpError):
    def __init__(self, email: str):
        self.message = f'wrong credentials for user with email={email}'
        self.status = 400
