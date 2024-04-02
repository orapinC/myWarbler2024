"""User views tests."""

# run these tests like:
#
#    python -m unittest test_user_views.py
#    FLASK_ENV=production python -m unittest test_user_views.py


import os
from unittest import TestCase

from models import db, connect_db, User, Message, Follows, Likes
from bs4 import BeautifulSoup

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


class UserViewTestCase(TestCase):
    """Test views for user."""

    #####
    ## setup & tear down
    #####
    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()
        
        self.client = app.test_client()
        
        self.userT = User.signup("userT", "userT@email.com", "password", None)
        self.userT_id = 9999
        self.userT.id = self.userT_id
        
        self.user1 = User.signup("test1", "user1@gmail.com","password1", None)
        self.user1_id = 1111
        self.user1.id = self.user1_id
        
        self.user2 = User.signup("test2", "user2@gmail.com","password2", None)
        self.user2_id = 2222
        self.user2.id = self.user2_id
        
        self.user3 = User.signup("test3", "user3@gmail.com","password3", None)
        self.user3_id = 3333
        self.user3.id = self.user3_id
        
        self.user4 = User.signup("test4", "user4@gmail.com","password4", None)
        self.user4_id = 4444
        self.user4.id = self.user4_id
        
        db.session.commit()
        
    
    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res
        
    def test_users_index(self):
        with self.client as c:
            res = c.get('/users')
            
            self.assertIn("@userT", str(res.data))
            self.assertIn("@test1", str(res.data))
            self.assertIn("@test2", str(res.data))
            self.assertIn("@test3", str(res.data))
            self.assertIn("@test4", str(res.data))
    
    def test_users_search(self):
        with self.client as c:
            res = c.get('/users?q=test')       
    
            self.assertIn("@test1", str(res.data))
            self.assertIn("@test2", str(res.data))
            self.assertIn("@test3", str(res.data))
            self.assertIn("@test4", str(res.data))
            
            self.assertNotIn("@userT", str(res.data))
            
    def test_users_show(self):
        with self.client as c:
            res = c.get(f'/users/{self.userT_id}')
            
            self.assertEqual(res.status_code, 200)
            self.assertIn("@userT", str(res.data))
            
    def setup_likes(self):
        msg1 = Message(text="first message", user_id=self.userT_id)
        msg2 = Message(text="second message", user_id=self.userT_id)
        msg3 = Message(id=123, text="user1 is here", user_id=self.user1_id)
        db.session.add_all([msg1,msg2,msg3])
        db.session.commit()
        
        liked1 = Likes(user_id=self.userT_id, message_id=123)
        db.session.add(liked1)
        db.session.commit()
    
    def test_user_show_with_likes(self):
        self.setup_likes()
        
        with self.client as c:
            res = c.get(f"/users/{self.userT_id}")
            self.assertEqual(res.status_code,200)
            
            self.assertIn("@userT", str(res.data))
            soup = BeautifulSoup(str(res.data), 'html.parser')
            found=soup.find_all("li", {"class": "stat"})
            self.assertEqual(len(found),4)
            
            #test for a count of 2 messages
            self.assertIn("2", found[0].text)
            ##test for a count of 0 following
            self.assertIn("0", found[1].text)
            ##test for a count of 1 followed
            self.assertIn("0", found[2].text)
            #test for a count of 1 liked
            self.assertIn("1", found[3].text)  
            
    def test_add_like(self):
        msg = Message(id=234, text="Hello world!", user_id=self.user2_id)
        db.session.add(msg)
        db.session.commit()
        
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.userT_id
                
            res = c.post('/users/add_like/234', follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            
            likes = Likes.query.filter(Likes.message_id==234).all()
            self.assertEqual(len(likes),1)
            self.assertEqual(likes[0].user_id, self.userT_id)
        
    def test_remove_like(self):
        self.setup_likes()  
        
        msg = Message.query.filter(Message.text=="user1 is here").one()
        self.assertIsNotNone(msg)
        self.assertNotEqual(msg.user_id, self.userT_id)
        
        liked = Likes.query.filter(
            Likes.user_id==self.userT_id and Likes.message_id==msg.id).one()
        self.assertIsNotNone(1)
        
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.userT_id
            
            res = c.post(f"/users/add_like/{msg.id}", follow_redirects=True)
            self.assertEqual(res.status_code,200)
            
            liked = Likes.query.filter(Likes.message_id==msg.id).all()
            self.assertEqual(len(liked),0)
            
    def test_unauthenticated_like(self):
        self.setup_likes()  
        
        msg = Message.query.filter(Message.text=="user1 is here").one()
        self.assertIsNotNone(msg)
        
        like_count = Likes.query.count()
        
        with self.client as c:
            
            res = c.post(f"/users/add_like/{msg.id}", follow_redirects=True)
            self.assertEqual(res.status_code,200)
            self.assertIn("Access unauthorized", str(res.data))
            self.assertEqual(like_count, Likes.query.count())
        
    def setup_followers(self):
        f1 = Follows(user_being_followed_id=self.user1_id, user_following_id=self.userT_id)  
        f2 = Follows(user_being_followed_id=self.user2_id, user_following_id=self.userT_id)
        f3 = Follows(user_being_followed_id=self.userT_id, user_following_id=self.user3_id)   
        db.session.add_all([f1,f2,f3])
        db.session.commit()
        
    def test_user_show_with_follows(self):
        self.setup_followers()
        
        with self.client as c:
            res = c.get(f"/users/{self.userT_id}")
            self.assertEqual(res.status_code,200)
            
            self.assertIn("@userT", str(res.data))
            soup = BeautifulSoup(str(res.data), 'html.parser')
            found=soup.find_all("li", {"class": "stat"})
            self.assertEqual(len(found),4)
            soup2 = BeautifulSoup(str(res.data), 'html.parser')
            found2=soup.find_all("li", {"class": "list-group-item"})
            self.assertEqual(len(found2),0)
            
            #test for a count of 0 messages
            self.assertIn("0", found[0].text)
            #test for a count of 2 following
            self.assertIn("2", found[1].text)
            #test for a count of 1 followed
            self.assertIn("1", found[2].text)
            #test for a count of 0 liked
            self.assertIn("0", found[3].text)
                    

    def test_show_following(self):
        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.userT_id
            
            res = c.get(f"/users/{self.userT_id}/following")
            self.assertEqual(res.status_code,200)
            self.assertIn("@test1", str(res.data))
            self.assertIn("@test2", str(res.data))
            self.assertNotIn("@test3", str(res.data))
            self.assertNotIn("@test4", str(res.data))
        
    def test_show_followed(self):
        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.userT_id
            
            res = c.get(f"/users/{self.userT_id}/followers")
            self.assertEqual(res.status_code,200)
            self.assertIn("@test3", str(res.data))
            self.assertNotIn("@test1", str(res.data))
            self.assertNotIn("@test2", str(res.data))
            self.assertNotIn("@test4", str(res.data))
            
    def test_unauthorized_following_page_access(self):
        self.setup_followers()
        with self.client as c:
            
            res = c.get(f"/users/{self.userT_id}/following", follow_redirects=True)
            self.assertEqual(res.status_code,200)
            self.assertNotIn("@test1", str(res.data))
            self.assertIn("Access unauthorized", str(res.data))
            
    def test_unauthorized_followers_page_access(self):
        self.setup_followers()
        with self.client as c:
            
            res = c.get(f"/users/{self.userT_id}/followers", follow_redirects=True)
            self.assertEqual(res.status_code,200)
            self.assertNotIn("@test3", str(res.data))
            self.assertIn("Access unauthorized", str(res.data))
