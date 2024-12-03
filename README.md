# Social Media API
RESTful API for a social media platform. 
Users can create profiles, follow other users, create and retrieve posts, 
manage likes and comments, and perform basic social media actions.


## Installing using GitHub

Python3 must be already installed

``` shel
git clone https://github.com/AndreiVed/Social-Media-API
cd social-media-api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 
```

## Getting access

* create user via /api/users/register/
* get access token via /api/users/login/

## Features

User Registration and Authentication:
* Register with email and password to create an account.
* Logins with credentials and receive a token for authentication.
* Logouts and invalidate their token.

User Profile:
* Create and update profile, including profile picture, bio, and other details.
* Retrieve their own profile and view profiles of other users.
* Search for users by username or other criteria.

Follow/Unfollow:
* Follow and unfollow other users.
* View the list of users they are following and the list of users following them.

Post Creation and Retrieval:
* Create new posts with text content and optional media attachments (e.g., images). (Adding images is optional task)
* Retrieve their own posts and posts of users they are following.
* Retrieve posts by hashtags or other criteria.

Likes and Comments (Optional):
* Like and dislike posts. 
* View the list of posts they have liked. 
* Add comments to posts and view comments on posts.
