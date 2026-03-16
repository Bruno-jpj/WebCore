from django.test import TestCase
from django.contrib.auth.models import User

# tests.py is the file where you write unit tests for your app

# specific app: python manage.py test myapp
# generic: python manage.py test

# best practice: split tests into multiple files by creating a tests/ directory instead of a single tests.py file

class UserModelTest(TestCase):
    def create(self):
        
        # create a test user
        self.user = User.objects.create_user(username="testuser", password="pass1234")
    
    def test_user_creation(self):
        
        # Test that the user is created correctly
        self.assertEqual(self.user.username, "testuser")
        self.assertTrue(self.user.check_password("pass1234"))

    def test_user_str_method(self):
        
        # Test the string representation of the user
        self.assertEqual(str(self.user), "testuser")

'''
example procedure:

> python manage.py test myapp
-- with this commando will excecute all just the tests.py or every test_*.py in your tests/ subdir; 
-- this appens because 'myapp' is the app name you give it to him when you created the app
-- when you execute the test command he knows where to search and what to do [only if you named the dir and files correctly].
-- so the print response would be like:

Found 1 test(s).
.
----------------------------------------------------------------------
Ran 1 test in 0.001s

OK

-- or you can be more specific and giving only that test to try

> python manage.py test myapp.tests.SimpleTest.test_addition
'''
