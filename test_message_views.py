"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data
app.app_context().push()
db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        self.testuser_id = 2222
        self.testuser.id = self.testuser_id

        db.session.commit()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res
    
    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")
            
    def test_no_session(self):
        with self.client as c:
            res = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            self.assertEqual(res.status_code,200)
            self.assertIn("Access unauthorized", str(res.data))
            
    def test_add_invalid_user(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 909090
            res = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            self.assertEqual(res.status_code,200)
            self.assertIn("Access unauthorized", str(res.data))
        
    def test_message_show(self):
        msg1 = Message(id=5555, text="test show message or not", user_id=self.testuser_id)
        db.session.add(msg1)
        db.session.commit()
        
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            msg2 = Message.query.get(5555)
            
            res = c.get(f'/messages/{msg2.id}')
            self.assertEqual(res.status_code, 200)
            self.assertIn(msg2.text, str(res.data))
            
    def test_invalid_message_show(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            res = c.get(f'/messages/67890')
            self.assertNotEqual(res.status_code, 200)
            
    def test_message_delete(self):
        msg3 = Message(id=6666, text="test message delete or not", user_id=self.testuser_id)
        db.session.add(msg3)
        db.session.commit()
        
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            res = c.post(f'/messages/6666/delete', follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            
            msgT = Message.query.get(6666)
            self.assertIsNone(msgT)
            
    def test_logging_in_unauthorized_message_delete(self):
        """A logging in none message owner should not able to delete message"""
        testuser2 = User.signup(username="testuser2",
                                    email="testuser2@email.com",
                                    password="testuser2password",
                                    image_url=None)
        testuser2.id = 8989
        
        msg3 = Message(id=6666, text="test message delete or not", user_id=self.testuser_id)
        db.session.add_all([testuser2, msg3])
        db.session.commit()
        
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 8989
            
            res = c.post(f'/messages/6666/delete', follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            
            msgT = Message.query.get(6666)
            self.assertIsNone(msgT)
            
    def test_message_delete_not_logging_in(self):
        """A not logging should not able to delete any message"""
        
        msg3 = Message(id=6666, text="test message delete or not", user_id=self.testuser_id)
        db.session.add(msg3)
        db.session.commit()
        
        with self.client as c:
            res = c.post(f'/messages/6666/delete', follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            
            msgT = Message.query.get(6666)
            self.assertIsNotNone(msgT)