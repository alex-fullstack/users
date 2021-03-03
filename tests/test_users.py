
async def test_01_registration(client):
    new_user = {'email': 'new-user@mail.com', 'password': '123', 'first_name': 'first', 'last_name': 'last'}
    response = await client.post('/users', json=new_user)

    assert response.status != 404, \
        'Страница `/users` не найдена, проверьте этот адрес в *routers.py*'
    assert response.status == 200, \
        'Проверьте, что при POST запросе `/users` ' \
        'без токена авторизации возвращается статус 200'
    data = await response.json()

    assert type(data.get('id')) == int, \
        'Проверьте, что при POST запросе `/users` возвращаете данные объекта. ' \
        'Значение `id` нет или не является целым числом.'
    assert data.get('email') == new_user['email'], \
        'Проверьте, что при POST запросе `/users` возвращаете данные объекта. ' \
        'Значение `email` неправильное.'
    assert data.get('first_name') == new_user['first_name'], \
        'Проверьте, что при POST запросе `/users` возвращаете данные объекта. ' \
        'Значение `first_name` неправильное.'
    assert data.get('last_name') == new_user['last_name'], \
        'Проверьте, что при POST запросе `/users` возвращаете данные объекта. ' \
        'Значение `last_name` неправильное.'
