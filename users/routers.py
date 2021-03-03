# routes.py
from .views import profile, login, prolong, registration, change_profile, logout


def setup_routes(app):
    app.router.add_post('/users', registration)
    app.router.add_get('/users/{user_id}', profile)
    app.router.add_patch('/users/{user_id}', change_profile)
    app.router.add_post('/login', login)
    app.router.add_get('/logout', logout)
    app.router.add_post('/prolong', prolong)
