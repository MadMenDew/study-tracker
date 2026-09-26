import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app import app
from supabase_auth.errors import AuthApiError


class AuthenticationTests(unittest.TestCase):
    def setUp(self):
        config = patch.dict(app.config, TESTING=True, SECRET_KEY='test-only-secret')
        config.start()
        self.addCleanup(config.stop)
        self.client = app.test_client()
        mocked = patch('app.get_supabase')
        self.backend = mocked.start().return_value
        self.addCleanup(mocked.stop)
        self.backend.auth.sign_in_with_password.return_value = SimpleNamespace(
            session=SimpleNamespace(access_token='user-token'))
        self.backend.auth.get_user.return_value = SimpleNamespace(
            user=SimpleNamespace(id='user-id', email='student@example.com'))

    def post(self, path, **values):
        with self.client.session_transaction() as sess:
            sess['csrf_token'] = 'test-csrf'
        return self.client.post(path, data={'csrf_token': 'test-csrf', **values})

    def login(self):
        return self.post('/login', email='student@example.com', password='test-password')

    def test_logged_out_dashboard_redirects(self):
        self.assertEqual(self.client.get('/').location, '/login')
        self.backend.auth.get_user.assert_not_called()

    def test_login_dashboard_logout_and_login_again(self):
        self.assertEqual(self.login().location, '/')
        page = self.client.get('/')
        self.assertEqual(page.status_code, 200)
        self.assertIn(b'student@example.com', page.data)
        self.assertEqual(page.headers['Cache-Control'], 'no-store')
        self.backend.auth.get_user.assert_called_with('user-token')
        self.backend.postgrest.auth.assert_called_with('user-token')
        self.assertEqual(self.post('/logout').location, '/login')
        self.backend.auth.admin.sign_out.assert_called_once_with('user-token', scope='local')
        self.assertEqual(self.client.get('/').location, '/login')
        self.assertEqual(self.login().location, '/')

    def test_registration_confirmation_required(self):
        self.backend.auth.sign_up.return_value = SimpleNamespace(session=None)
        response = self.post('/register', email='student@example.com', password='test-password')
        self.assertEqual(response.location, '/login')
        self.assertIn(b'Check your email', self.client.get('/login').data)
        self.assertEqual(self.client.get('/').location, '/login')

    def test_registration_immediate_session(self):
        self.backend.auth.sign_up.return_value = SimpleNamespace(session=SimpleNamespace(access_token='new-token'))
        self.assertEqual(self.post('/register', email='student@example.com', password='test-password').location, '/')
        with self.client.session_transaction() as sess:
            self.assertEqual(sess['access_token'], 'new-token')
            self.assertNotIn('password', sess)

    def test_invalid_credentials_no_authentication(self):
        self.backend.auth.sign_in_with_password.side_effect = RuntimeError('secret diagnostic')
        response = self.login()
        self.assertEqual(response.status_code, 400)
        self.assertNotIn(b'secret diagnostic', response.data)
        self.assertNotIn(b'test-password', response.data)
        self.assertEqual(self.client.get('/').location, '/login')

    def test_expired_or_invalid_token_is_cleared(self):
        self.login()
        self.backend.auth.get_user.side_effect = RuntimeError('expired')
        self.assertEqual(self.client.get('/').location, '/login')
        with self.client.session_transaction() as sess:
            self.assertNotIn('access_token', sess)

    def test_unconfirmed_email_has_actionable_message(self):
        self.backend.auth.sign_in_with_password.side_effect = AuthApiError(
            'private diagnostic', 400, 'email_not_confirmed')
        response = self.login()
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Confirm your email before logging in', response.data)
        self.assertNotIn(b'private diagnostic', response.data)
        self.assertEqual(self.client.get('/').location, '/login')

    def test_csrf_required_for_all_posts(self):
        for path in ('/login', '/register', '/logout'):
            self.assertEqual(self.client.post(path).status_code, 400)
        self.backend.auth.sign_up.assert_not_called()
        self.backend.auth.sign_in_with_password.assert_not_called()

    def test_logout_is_post_only_and_clears_local_state_on_remote_failure(self):
        self.login()
        self.assertEqual(self.client.get('/logout').status_code, 405)
        self.backend.auth.admin.sign_out.side_effect = RuntimeError('offline')
        self.assertEqual(self.post('/logout').location, '/login')
        self.assertEqual(self.client.get('/').location, '/login')

    def test_registration_validation(self):
        for email, password in [('invalid', 'test-password'), ('a@b.com', 'short')]:
            self.assertEqual(self.post('/register', email=email, password=password).status_code, 400)
        self.backend.auth.sign_up.assert_not_called()

    def test_independent_browser_remains_logged_out(self):
        self.login()
        self.assertEqual(app.test_client().get('/').location, '/login')

    def test_cookie_protections(self):
        cookie = self.client.get('/login').headers['Set-Cookie']
        self.assertIn('HttpOnly', cookie)
        self.assertIn('SameSite=Lax', cookie)
