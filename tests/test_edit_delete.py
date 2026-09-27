import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app import app

SID = '11111111-1111-4111-8111-111111111111'


class EditDeleteTests(unittest.TestCase):
    def setUp(self):
        config = patch.dict(app.config, TESTING=True, SECRET_KEY='test-secret')
        config.start()
        self.addCleanup(config.stop)
        mock = patch('app.get_supabase')
        self.backend = mock.start().return_value
        self.addCleanup(mock.stop)
        self.backend.auth.get_user.return_value = SimpleNamespace(user=SimpleNamespace(id='owner', email='owner@example.com'))
        self.table = self.backend.table.return_value
        self.record = dict(id=SID, subject='Physics', minutes=60, study_date='2026-09-27', notes=None)
        self.read = self.table.select.return_value.eq.return_value.eq.return_value.execute
        self.read.return_value = SimpleNamespace(data=[self.record])
        self.update = self.table.update.return_value.eq.return_value.eq.return_value.execute
        self.update.return_value = SimpleNamespace(data=[self.record])
        self.delete = self.table.delete.return_value.eq.return_value.eq.return_value.execute
        self.delete.return_value = SimpleNamespace(data=[self.record])
        self.client = app.test_client()
        with self.client.session_transaction() as sess:
            sess.update(access_token='token', csrf_token='csrf')
        self.form = dict(csrf_token='csrf', subject='Math', minutes='45', study_date='2026-09-26', notes='Review', user_id='attacker')

    def test_edit_prefills_and_updates_only_allowed_fields_with_owner_filter(self):
        page = self.client.get('/edit/' + SID)
        self.assertEqual(page.status_code, 200)
        self.assertIn(b'value="Physics"', page.data)
        self.assertNotIn(b'>None</textarea>', page.data)
        response = self.client.post('/edit/' + SID, data=self.form)
        self.assertEqual(response.location, '/')
        self.table.update.assert_called_once_with(dict(subject='Math', minutes=45, study_date='2026-09-26', notes='Review'))
        self.table.update.return_value.eq.assert_called_once_with('id', SID)
        self.table.update.return_value.eq.return_value.eq.assert_called_once_with('user_id', 'owner')
        self.table.select.return_value.eq.return_value.eq.assert_called_with('user_id', 'owner')

    def test_missing_or_other_users_record_cannot_be_read_changed_or_deleted(self):
        self.read.return_value.data = []
        self.assertEqual(self.client.get('/edit/' + SID).status_code, 404)
        self.assertEqual(self.client.post('/edit/' + SID, data=self.form).status_code, 404)
        self.assertEqual(self.client.post('/delete/' + SID, data=self.form).status_code, 404)
        self.table.update.assert_not_called()
        self.table.delete.assert_not_called()

    def test_delete_is_post_only_and_owner_scoped(self):
        self.assertEqual(self.client.get('/delete/' + SID).status_code, 405)
        self.assertEqual(self.client.post('/delete/' + SID, data=self.form).location, '/')
        self.table.delete.return_value.eq.assert_called_once_with('id', SID)
        self.table.delete.return_value.eq.return_value.eq.assert_called_once_with('user_id', 'owner')

    def test_invalid_edit_retains_submitted_values(self):
        for field, value in [('minutes', '0'), ('subject', ' '), ('study_date', 'invalid'), ('notes', 'x'*5001)]:
            response = self.client.post('/edit/' + SID, data={**self.form, field: value})
            self.assertEqual(response.status_code, 400)
        self.table.update.assert_not_called()
        response = self.client.post('/edit/' + SID, data={**self.form, 'minutes': '0'})
        self.assertIn(b'value="Math"', response.data)

    def test_csrf_auth_and_malformed_id(self):
        for route in ('edit', 'delete'):
            self.assertEqual(self.client.post('/' + route + '/' + SID).status_code, 400)
            self.assertEqual(self.client.post('/' + route + '/bad-id', data=self.form).status_code, 404)
        with self.client.session_transaction() as sess:
            sess.pop('access_token')
        for route in ('edit', 'delete'):
            self.assertEqual(self.client.post('/' + route + '/' + SID, data=self.form).location, '/login')
        self.table.update.assert_not_called()
        self.table.delete.assert_not_called()

    def test_concurrently_removed_record_does_not_report_success(self):
        self.update.return_value.data = []
        self.delete.return_value.data = []
        for route in ('edit', 'delete'):
            self.assertEqual(self.client.post('/' + route + '/' + SID, data=self.form).status_code, 404)

    def test_database_failure_retains_edit_and_hides_diagnostics(self):
        self.update.side_effect = RuntimeError('private diagnostic')
        response = self.client.post('/edit/' + SID, data=self.form)
        self.assertEqual(response.status_code, 503)
        self.assertIn(b'value="Math"', response.data)
        self.assertNotIn(b'private diagnostic', response.data)
        self.delete.side_effect = RuntimeError('private diagnostic')
        self.table.select.return_value.eq.return_value.order.return_value.order.return_value.execute.return_value = SimpleNamespace(data=[])
        response = self.client.post('/delete/' + SID, data=self.form)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn(b'Study session deleted.', response.data)
