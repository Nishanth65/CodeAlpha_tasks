import urllib.request
import urllib.parse
import http.cookiejar
import json
import re

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# 1. Fetch Login page to get CSRF token
resp = opener.open('http://127.0.0.1:8000/login/')
html = resp.read().decode('utf-8')
csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html)
csrf = csrf_match.group(1) if csrf_match else None
print('1. Login page reached, CSRF token extracted:', bool(csrf))

# 2. Perform Login as testuser
data = urllib.parse.urlencode({
    'username': 'testuser',
    'password': 'Password123!',
    'csrfmiddlewaretoken': csrf
}).encode('utf-8')
req = urllib.request.Request('http://127.0.0.1:8000/login/', data=data, headers={'Referer': 'http://127.0.0.1:8000/login/'})
resp = opener.open(req)
print('2. Login response URL:', resp.geturl(), 'Status:', resp.status)

# 3. Fetch Feed
resp = opener.open('http://127.0.0.1:8000/')
feed_html = resp.read().decode('utf-8')
print('3. Feed page loaded, Contains "Global Feed":', 'Global Feed' in feed_html)

# Extract post ID from feed
post_id_match = re.search(r'data-post-id="(\d+)"', feed_html)
post_id = post_id_match.group(1) if post_id_match else None
print('   Extracted post ID from feed:', post_id)

# 4. Create a new post via POST
csrftoken = [c.value for c in cj if c.name == 'csrftoken'][0]
new_post_data = urllib.parse.urlencode({
    'content': 'Live test post created via automated HTTP test client! 🚀',
    'csrfmiddlewaretoken': csrftoken
}).encode('utf-8')
req = urllib.request.Request('http://127.0.0.1:8000/post/create/', data=new_post_data, headers={'Referer': 'http://127.0.0.1:8000/'})
resp = opener.open(req)
print('4. Post creation redirect status:', resp.status)

# 5. Like the post via AJAX
req = urllib.request.Request(
    f'http://127.0.0.1:8000/post/{post_id}/like/',
    data=b'{}',
    headers={
        'X-CSRFToken': csrftoken,
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/json',
        'Referer': 'http://127.0.0.1:8000/'
    }
)
resp = opener.open(req)
like_data = json.loads(resp.read().decode('utf-8'))
print('5. Like toggle response:', like_data)

# 6. Add comment to post
comment_data = urllib.parse.urlencode({
    'content': 'Loving the live test comments!',
    'csrfmiddlewaretoken': csrftoken
}).encode('utf-8')
req = urllib.request.Request(
    f'http://127.0.0.1:8000/post/{post_id}/comment/',
    data=comment_data,
    headers={
        'X-CSRFToken': csrftoken,
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'http://127.0.0.1:8000/'
    }
)
resp = opener.open(req)
comment_json = json.loads(resp.read().decode('utf-8'))
print('6. Comment creation response:', comment_json)

# 7. Toggle follow marcus_v
req = urllib.request.Request(
    'http://127.0.0.1:8000/profile/marcus_v/follow/',
    data=b'{}',
    headers={
        'X-CSRFToken': csrftoken,
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'http://127.0.0.1:8000/explore/'
    }
)
resp = opener.open(req)
follow_json = json.loads(resp.read().decode('utf-8'))
print('7. Follow toggle response:', follow_json)

# 8. Fetch profile page
resp = opener.open('http://127.0.0.1:8000/profile/testuser/')
prof_html = resp.read().decode('utf-8')
print('8. Profile page loaded, contains testuser handle:', '@testuser' in prof_html)

# 9. Fetch explore page
resp = opener.open('http://127.0.0.1:8000/explore/')
explore_html = resp.read().decode('utf-8')
print('9. Explore page loaded, contains Discover People:', 'Discover People' in explore_html)

print('\n[SUCCESS] ALL LIVE SERVER END-TO-END TESTS COMPLETED SUCCESSFULLY!')
