from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from social.models import Profile, Post, Comment, Like, Follow

class Command(BaseCommand):
    help = 'Seeds initial sample users, profiles, posts, comments, likes, and follows for testing.'

    def handle(self, *args, **options):
        self.stdout.write("Seeding sample data for Social Connect...")

        # 1. Create sample users
        sample_users = [
            {
                'username': 'alex_dev',
                'email': 'alex@example.com',
                'first_name': 'Alex',
                'last_name': 'Rivera',
                'password': 'Password123!',
                'bio': 'Full-stack engineer & open source enthusiast. Exploring Django and modern web architectures.',
                'location': 'San Francisco, CA',
            },
            {
                'username': 'sophia_ai',
                'email': 'sophia@example.com',
                'first_name': 'Sophia',
                'last_name': 'Chen',
                'password': 'Password123!',
                'bio': 'AI researcher and photographer. Living at the intersection of technology and creativity.',
                'location': 'Seattle, WA',
            },
            {
                'username': 'marcus_v',
                'email': 'marcus@example.com',
                'first_name': 'Marcus',
                'last_name': 'Vance',
                'password': 'Password123!',
                'bio': 'Coffee enthusiast, designer, and minimalist. Building human-first digital experiences.',
                'location': 'New York, NY',
            },
            {
                'username': 'testuser',
                'email': 'testuser@example.com',
                'first_name': 'Demo',
                'last_name': 'Tester',
                'password': 'Password123!',
                'bio': 'Official test account for CodeAlpha submission evaluation.',
                'location': 'Austin, TX',
            }
        ]

        created_users = {}
        for u_data in sample_users:
            user, created = User.objects.get_or_create(
                username=u_data['username'],
                defaults={
                    'email': u_data['email'],
                    'first_name': u_data['first_name'],
                    'last_name': u_data['last_name'],
                }
            )
            if created:
                user.set_password(u_data['password'])
                user.save()
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.bio = u_data['bio']
            profile.location = u_data['location']
            profile.save()
            created_users[u_data['username']] = user
            status_str = "Created" if created else "Found existing"
            self.stdout.write(f"- {status_str} user: @{user.username}")

        alex = created_users['alex_dev']
        sophia = created_users['sophia_ai']
        marcus = created_users['marcus_v']
        demo = created_users['testuser']

        # 2. Create Follow relationships
        follow_pairs = [
            (demo, alex),
            (demo, sophia),
            (alex, sophia),
            (sophia, alex),
            (marcus, demo),
            (marcus, alex),
        ]
        for follower, following in follow_pairs:
            Follow.objects.get_or_create(follower=follower, following=following)
        self.stdout.write("- Created follow relationships.")

        # 3. Create Sample Posts
        posts_data = [
            (alex, "Excited to share that our new web application architecture is complete! Django ORM combined with clean relational MySQL modeling delivers incredible speed and reliability. #webdev #python #django"),
            (sophia, "Morning thoughts: The best user experiences are the ones that feel completely invisible and intuitive. Simplicity is the ultimate sophistication. ☕✨"),
            (marcus, "Just pushed an update to our design system. Subtle gradients, dark aesthetics, and glassmorphism create such an immersive atmosphere."),
            (alex, "Pair programming today was super productive. Code reviews and solid unit tests save hours in debugging down the line."),
            (demo, "Hello everyone on Social Connect! Excited to explore this new social platform built for CodeAlpha Task 2. 🎉"),
        ]

        created_posts = []
        for author, content in posts_data:
            post, _ = Post.objects.get_or_create(author=author, content=content)
            created_posts.append(post)
        self.stdout.write("- Created sample posts.")

        # 4. Create Likes
        if len(created_posts) >= 3:
            Like.objects.get_or_create(post=created_posts[0], user=sophia)
            Like.objects.get_or_create(post=created_posts[0], user=demo)
            Like.objects.get_or_create(post=created_posts[1], user=alex)
            Like.objects.get_or_create(post=created_posts[1], user=marcus)
            Like.objects.get_or_create(post=created_posts[2], user=alex)
            self.stdout.write("- Added sample likes.")

        # 5. Create Comments
        if len(created_posts) >= 2:
            Comment.objects.get_or_create(
                post=created_posts[0],
                author=sophia,
                defaults={'content': 'Completely agree Alex! Django and MySQL are a rock-solid combo.'}
            )
            Comment.objects.get_or_create(
                post=created_posts[0],
                author=demo,
                defaults={'content': 'Looks fantastic! The feed loads instantaneously.'}
            )
            Comment.objects.get_or_create(
                post=created_posts[1],
                author=marcus,
                defaults={'content': 'Spot on Sophia. Good UX is effortless.'}
            )
            self.stdout.write("- Added sample comments.")

        self.stdout.write(self.style.SUCCESS("Sample data seeding completed successfully!"))
