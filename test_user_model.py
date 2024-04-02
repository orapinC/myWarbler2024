"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py
#    also test passed with 
#    FLASK_ENV=production python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows

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
app.app_context().push()
db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    #####
    ## setup & tear down
    #####
    def setUp(self):
        """Create test client, add sample data."""

        #User.query.delete()
        #Message.query.delete()
        #Follows.query.delete()
        db.drop_all()
        db.create_all()
        
        user1 = User.signup("test1", "user1@gmail.com","password1", None)
        userid1 = 1111
        user1.id = userid1
        
        user2 = User.signup("test2", "user2@gmail.com","password2", None)
        userid2 = 2222
        user2.id = userid2
        
        db.session.commit()
        
        user1 = User.query.get_or_404(userid1)
        user2 = User.query.get_or_404(userid2)
        
        self.user1 = user1
        self.userid1 = userid1
        
        self.user2 = user2
        self.userid2 = userid2
        
        self.client = app.test_client()
    
    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res
        
    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)
        
    ######
    ## test: is_following
    ######
    
    def test_is_following(self):
        self.user1.following.append(self.user2)
        db.session.commit()
        
        self.assertTrue(self.user1.is_following(self.user2))
        self.assertFalse(self.user2.is_following(self.user1))
        
    def test_is_followed_by(self):
        self.user1.following.append(self.user2)
        db.session.commit()
        
        self.assertTrue(self.user2.is_followed_by(self.user1))
        self.assertFalse(self.user1.is_followed_by(self.user2))
        
    def test_user_follow(self):
        self.user1.following.append(self.user2)
        db.session.commit()
        
        self.assertEqual(len(self.user1.followers),0)
        self.assertEqual(len(self.user1.following),1)
        self.assertEqual(len(self.user2.followers),1)
        self.assertEqual(len(self.user2.following),0)
        
        self.assertEqual(self.user2.followers[0].id, self.user1.id)
        self.assertEqual(self.user1.following[0].id, self.user2.id)
        
    #####
    ## test: User.signup
    #####
    def test_valid_signup(self):
        user_test = User.signup("user3","user3@email.com","password3",None)
        userid = 3333
        user_test.id = userid
        db.session.commit()
    
        user_test = User.query.get_or_404(userid)
        self.assertIsNotNone(user_test)
        self.assertEqual(user_test.username,"user3")
        self.assertEqual(user_test.email,"user3@email.com")
        self.assertNotEqual(user_test.password,"password3")
        #test bcrypt strings start with $2b$
        self.assertTrue(user_test.password.startswith("$2b$"))
    
    def test_invalid_username_signup(self):
        invalid = User.signup(None, "none@email.com","password", None)
        userid = 4444
        invalid.id = userid
        with self.assertRaises(exc.IntegrityError) as Context:
            db.session.commit()
    
    def test_invalid_email_signup(self):
        invalid = User.signup('Invalid', None,"password", None)
        userid = 5555
        invalid.id = userid
        with self.assertRaises(exc.IntegrityError) as Context:
            db.session.commit()
            
    def test_invalid_password_signup(self):
        with self.assertRaises(ValueError) as Context:
            User.signup("Invalid", "invalid@email.com","", None)
        
        with self.assertRaises(ValueError) as Context:
            User.signup("Invalid", "invalid@email.com",None, None)
            
    #####
    ## test: User.authenticate
    #####
    def test_authenticate(self):
        userT = User.authenticate(self.user1.username, "password1")
        self.assertIsNotNone(userT)
        self.assertEqual(userT.id, self.userid1)
        
    def test_invalid_username_autheticate(self):
        self.assertFalse(User.authenticate("notinthedb","password"))
    
    def test_wrong_password_autheticate(self):
        self.assertFalse(User.authenticate("self.user1.username","password"))
        
        