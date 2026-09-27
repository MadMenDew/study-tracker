import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app import app


class StudySessionTests(unittest.TestCase):
    def setUp(self):
        config = patch.dict(app.config, TESTING=True, SECRET_KEY='test-secret')
        config.start()
        self.addCleanup(config.stop)
        backend = patch('app.get_supabase')
        self.backend = backend.start().return_value
        self.addCleanup(backend.stop)
        self.backend.auth.get_user.return_value = SimpleNamespace(user=SimpleNamespace(id='owner', email='owner@example.com'))
        self.table = self.backend.table.return_value
        self.query = self.table.select.return_value.eq.return_value
        self.result = self.query.order.return_value.order.return_value.execute
        self.result.return_value = SimpleNamespace(data=[])
        self.client = app.test_client()
        with self.client.session_transaction() as sess:
            sess.update(access_token='owner-token', csrf_token='csrf')
        self.form = dict(csrf_token='csrf', subject='Physics', minutes='60', study_date='2026-09-25', notes='Practice')

    def test_save_uses_verified_owner_and_redirects(self):
        self.form['user_id'] = 'someone-else'
        response = self.client.post('/add', data=self.form)
        self.assertEqual(response.location, '/')
        self.table.insert.assert_called_once_with(dict(user_id='owner', subject='Physics', minutes=60, study_date='2026-09-25', notes='Practice'))
        self.backend.postgrest.auth.assert_called_with('owner-token')

    def test_read_is_filtered_and_escapes_content(self):
        self.result.return_value.data = [dict(id='11111111-1111-4111-8111-111111111111', subject='<script>alert(1)</script>', minutes=60, study_date='2026-09-25', notes='<b>notes</b>')]
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.table.select.return_value.eq.assert_called_once_with('user_id', 'owner')
        self.assertIn(b'60 minutes', response.data)
        self.assertIn(b'&lt;script&gt;', response.data)
        self.assertNotIn(b'<script>', response.data)

    def test_invalid_values_never_insert_and_preserve_form(self):
        for field, value in [('subject', ' '), ('subject', 'x'*121), ('minutes', '0'), ('minutes', '-5'), ('minutes', '1.5'), ('minutes', '1441'), ('minutes', 'abc'), ('study_date', '2026-02-30'), ('study_date', ''), ('notes', 'x'*5001)]:
            with self.subTest(field=field, value=value[:20]):
                data = {**self.form, field: value}
                response = self.client.post('/add', data=data)
                self.assertEqual(response.status_code, 400)
        self.table.insert.assert_not_called()
        response = self.client.post('/add', data={**self.form, 'minutes': '0'})
        self.assertIn(b'value="Physics"', response.data)
        self.assertIn(b'Practice</textarea>', response.data)

    def test_empty_notes_and_trimmed_subject(self):
        self.client.post('/add', data={**self.form, 'notes': ' ', 'subject': ' Physics '})
        payload = self.table.insert.call_args.args[0]
        self.assertEqual(payload['subject'], 'Physics')
        self.assertIsNone(payload['notes'])

    def test_auth_and_csrf_are_required(self):
        self.assertEqual(self.client.post('/add', data={**self.form, 'csrf_token': 'wrong'}).status_code, 400)
        with self.client.session_transaction() as sess:
            sess.pop('access_token')
        self.assertEqual(self.client.post('/add', data=self.form).location, '/login')
        self.table.insert.assert_not_called()

    def test_read_failure_is_not_empty_state(self):
        self.result.side_effect = RuntimeError('private diagnostic')
        response = self.client.get('/')
        self.assertEqual(response.status_code, 503)
        self.assertIn(b'temporarily unavailable', response.data)
        self.assertNotIn(b'No study sessions yet', response.data)
        self.assertNotIn(b'private diagnostic', response.data)

    def test_save_failure_retains_input_without_success_message(self):
        self.table.insert.return_value.execute.side_effect = RuntimeError('private diagnostic')
        response = self.client.post('/add', data=self.form)
        self.assertEqual(response.status_code, 503)
        self.assertIn(b'value="Physics"', response.data)
        self.assertNotIn(b'Study session added.', response.data)

    def test_saved_record_is_read_on_refresh_and_another_user_has_different_filter(self):
        records = []
        self.table.insert.side_effect = lambda payload: SimpleNamespace(execute=lambda: records.append({**payload, 'id': '11111111-1111-4111-8111-111111111111'}))
        def filtered(column, owner):
            query = MagicMock()
            query.order.return_value.order.return_value.execute.return_value = SimpleNamespace(data=[r for r in records if r['user_id'] == owner])
            return query
        self.table.select.return_value.eq.side_effect = filtered
        self.client.post('/add', data=self.form)
        for _ in range(2):
            self.assertIn(b'<h3>Physics</h3>', self.client.get('/').data)
        self.backend.auth.get_user.return_value.user = SimpleNamespace(id='other', email='other@example.com')
        self.assertNotIn(b'<h3>Physics</h3>', self.client.get('/').data)
        self.table.select.return_value.eq.assert_called_with('user_id', 'other')
