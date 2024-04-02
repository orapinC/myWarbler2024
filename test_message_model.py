"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows, Likes

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app
from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data
## need to use ".push()", "with app.app_context():"" is not working
app.app_context().push()
db.create_all()

class MessageModelTestCase(TestCase):
    """Test views for messages."""

    #####
    ## setup & tear down
    #####
    def setUp(self):
        """Create test client and add to db."""

        db.drop_all()
        db.create_all()
        
        u = User.signup("test", "test@email.com","password", None)
        self.uid = 56789
        u.id = self.uid
        
        db.session.commit()
        
        self.u = User.query.get_or_404(self.uid)
        
        self.client = app.test_client()
    
    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res
        
    def test_message_model(self):
        """Does basic model work?"""
        msg = Message(
            text = "Testing a warbler message",
            user_id = self.uid
        )
        
        db.session.add(msg)
        db.session.commit()
        
        self.assertEqual(len(self.u.messages),1)
        self.assertEqual(self.u.messages[0].text,"Testing a warbler message")
        
    def test_message_like(self):
        msg1 = Message(
            text = "test one",
            user_id = self.uid
        )
        
        msg2 = Message(
            text = "test two",
            user_id = self.uid
        )
        
        u2= User.signup("user2","user2@email.com","password2", None)
        u2id = 9999
        u2.id = u2id
        
        db.session.add_all([msg1, msg2, u2])
        db.session.commit()
        
        u2.likes.append(msg1)
        db.session.commit()
        
        u2liked = Likes.query.filter(Likes.user_id == u2.id).all()
        self.assertEqual(len(u2liked),1)
        self.assertEqual(u2liked[0].message_id, msg1.id)