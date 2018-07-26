from apiritif import http
from unittest import TestCase


class TestRequests(TestCase):
    def test_get(self):
        http.get('http://blazedemo.com/?tag=get')

    def test_post(self):
        http.post('http://blazedemo.com/?tag=post')

    def test_put(self):
        http.put('http://blazedemo.com/?tag=put')

    def test_patch(self):
        http.patch('http://blazedemo.com/?tag=patch')

    def test_head(self):
        http.head('http://blazedemo.com/?tag=head')

    def test_delete(self):
        http.delete('http://blazedemo.com/?tag=delete')

    def test_options(self):
        http.options('http://blazedemo.com/echo.php?echo=options')

    def test_connect(self):
        target = http.target('http://blazedemo.com/', auto_assert_ok=False)
        target.connect('/echo.php?echo=connect')
