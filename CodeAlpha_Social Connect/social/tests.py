from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from social.models import Profile, Post, Comment, Like, Follow

class SocialPlatformTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create test users
        self.user1 = User.objects.create_user(
            username='alice',
            email='alice@example.com',
            password='Password123!',
            first_name='Alice',
            last_name='Wonder'
        )
        self.user2 = User.objects.create_user(
            username='bob',
            email='bob@example.com',
            password='Password123!',
            first_name='Bob',
            last_name='Builder'
        )

        # Ensure profiles
        self.profile1, _ = Profile.objects.get_or_create(user=self.user1)
        self.profile1.bio = 'Alice bio'
        self.profile1.location = 'Wonderland'
        self.profile1.save()

        self.profile2, _ = Profile.objects.get_or_create(user=self.user2)
        self.profile2.bio = 'Bob bio'
        self.profile2.location = 'Builder city'
        self.profile2.save()

        # Create a sample post
        self.post1 = Post.objects.create(author=self.user1, content='Hello from Alice!')

    # 1. User Registration, Login, Logout
    def test_user_registration(self):
        response = self.client.post(reverse('register'), {
            'username': 'charlie',
            'email': 'charlie@example.com',
            'first_name': 'Charlie',
            'last_name': 'Chaplin',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='charlie').exists())
        charlie = User.objects.get(username='charlie')
        self.assertTrue(hasattr(charlie, 'profile'))

    def test_user_login_and_logout(self):
        # Login
        login_success = self.client.login(username='alice', password='Password123!')
        self.assertTrue(login_success)

        # Feed access authenticated
        feed_resp = self.client.get(reverse('feed'))
        self.assertEqual(feed_resp.status_code, 200)

        # Logout
        logout_resp = self.client.post(reverse('logout'))
        self.assertEqual(logout_resp.status_code, 302)

    # 2. Profiles and Profile Editing
    def test_profile_view_and_editing(self):
        self.client.login(username='alice', password='Password123!')
        
        # View profile
        resp = self.client.get(reverse('profile', kwargs={'username': 'alice'}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Alice bio')

        # Edit profile
        edit_resp = self.client.post(reverse('edit_profile'), {
            'username': 'alice',
            'email': 'alice_updated@example.com',
            'first_name': 'Alice',
            'last_name': 'Wonderland',
            'bio': 'Updated bio text',
            'location': 'New Location',
        })
        self.assertEqual(edit_resp.status_code, 302)
        self.profile1.refresh_from_db()
        self.assertEqual(self.profile1.bio, 'Updated bio text')
        self.assertEqual(self.profile1.location, 'New Location')

    # 3. Post Creation, Editing, Deletion & Authorization
    def test_post_lifecycle_and_authorization(self):
        self.client.login(username='alice', password='Password123!')

        # Create Post
        create_resp = self.client.post(reverse('create_post'), {
            'content': 'A brand new post by Alice'
        })
        self.assertEqual(create_resp.status_code, 302)
        new_post = Post.objects.filter(content='A brand new post by Alice').first()
        self.assertIsNotNone(new_post)
        self.assertEqual(new_post.author, self.user1)

        # Edit own post
        edit_resp = self.client.post(reverse('edit_post', kwargs={'post_id': new_post.id}), {
            'content': 'Edited content by Alice'
        })
        self.assertEqual(edit_resp.status_code, 302)
        new_post.refresh_from_db()
        self.assertEqual(new_post.content, 'Edited content by Alice')

        # User2 tries to edit User1's post (Authorization check)
        self.client.logout()
        self.client.login(username='bob', password='Password123!')
        unauth_edit = self.client.post(reverse('edit_post', kwargs={'post_id': new_post.id}), {
            'content': 'Hacked by Bob'
        })
        self.assertEqual(unauth_edit.status_code, 302)
        new_post.refresh_from_db()
        self.assertEqual(new_post.content, 'Edited content by Alice')  # Content unchanged!

        # User2 tries to delete User1's post (Authorization check)
        unauth_delete = self.client.post(reverse('delete_post', kwargs={'post_id': new_post.id}))
        self.assertEqual(unauth_delete.status_code, 302)
        self.assertTrue(Post.objects.filter(id=new_post.id).exists())  # Post still exists!

        # User1 deletes own post
        self.client.logout()
        self.client.login(username='alice', password='Password123!')
        auth_delete = self.client.post(reverse('delete_post', kwargs={'post_id': new_post.id}))
        self.assertEqual(auth_delete.status_code, 302)
        self.assertFalse(Post.objects.filter(id=new_post.id).exists())

    # 4. Likes & Unlikes with Count and Constraint
    def test_like_unlike_and_constraint(self):
        self.client.login(username='bob', password='Password123!')

        # Like post via AJAX
        like_resp = self.client.post(
            reverse('toggle_like', kwargs={'post_id': self.post1.id}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(like_resp.status_code, 200)
        data = like_resp.json()
        self.assertTrue(data['liked'])
        self.assertEqual(data['likes_count'], 1)
        self.assertEqual(self.post1.likes_count, 1)

        # Unlike post
        unlike_resp = self.client.post(
            reverse('toggle_like', kwargs={'post_id': self.post1.id}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        data2 = unlike_resp.json()
        self.assertFalse(data2['liked'])
        self.assertEqual(data2['likes_count'], 0)
        self.assertEqual(self.post1.likes_count, 0)

        # Database constraint test: prevent duplicate likes directly
        Like.objects.create(post=self.post1, user=self.user2)
        with self.assertRaises(IntegrityError):
            Like.objects.create(post=self.post1, user=self.user2)

    # 5. Comments & Moderation
    def test_comments_and_deletion(self):
        self.client.login(username='bob', password='Password123!')

        # Add comment
        comment_resp = self.client.post(
            reverse('add_comment', kwargs={'post_id': self.post1.id}),
            {'content': 'Great post Alice!'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(comment_resp.status_code, 200)
        c_data = comment_resp.json()
        self.assertTrue(c_data['success'])
        self.assertEqual(self.post1.comments_count, 1)

        comment_id = c_data['comment_id']

        # Delete own comment
        del_resp = self.client.post(
            reverse('delete_comment', kwargs={'comment_id': comment_id}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(del_resp.status_code, 200)
        self.assertEqual(self.post1.comments_count, 0)

    # 6. Follow, Unfollow, Counters & Constraints
    def test_follow_unfollow_and_constraints(self):
        self.client.login(username='bob', password='Password123!')

        # Follow Alice
        follow_resp = self.client.post(
            reverse('toggle_follow', kwargs={'username': 'alice'}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(follow_resp.status_code, 200)
        f_data = follow_resp.json()
        self.assertTrue(f_data['is_following'])
        self.assertEqual(f_data['followers_count'], 1)

        # Unfollow Alice
        unfollow_resp = self.client.post(
            reverse('toggle_follow', kwargs={'username': 'alice'}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        uf_data = unfollow_resp.json()
        self.assertFalse(uf_data['is_following'])
        self.assertEqual(uf_data['followers_count'], 0)

        # User cannot follow themselves
        self_follow_resp = self.client.post(
            reverse('toggle_follow', kwargs={'username': 'bob'}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(self_follow_resp.status_code, 400)

        # Direct model validation test: self-follow raises ValidationError
        self_follow_model = Follow(follower=self.user2, following=self.user2)
        with self.assertRaises(ValidationError):
            self_follow_model.clean()

    # 7. Feed Filtering and Search
    def test_feed_filtering_and_search(self):
        self.client.login(username='bob', password='Password123!')
        
        # Follow Alice
        Follow.objects.create(follower=self.user2, following=self.user1)

        # Following feed includes Alice's post
        following_feed = self.client.get(reverse('feed') + '?tab=following')
        self.assertEqual(following_feed.status_code, 200)
        self.assertContains(following_feed, 'Hello from Alice!')

        # Search query finds post
        search_resp = self.client.get(reverse('feed') + '?q=Alice')
        self.assertEqual(search_resp.status_code, 200)
        self.assertContains(search_resp, 'Hello from Alice!')
