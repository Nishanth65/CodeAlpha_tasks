/**
 * Social Connect - Vanilla JavaScript Interactions
 * Handles AJAX likes, follows, comments, image preview, dropdowns & toast messages.
 */

document.addEventListener('DOMContentLoaded', () => {
    // -----------------------------------------------------------
    // Helper: CSRF Token Getter
    // -----------------------------------------------------------
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie('csrftoken');

    // -----------------------------------------------------------
    // 1. Interactive Image Upload Preview
    // -----------------------------------------------------------
    const imageInput = document.getElementById('post-image-input');
    const imagePreviewWrapper = document.getElementById('image-preview-wrapper');
    const imagePreviewImg = document.getElementById('image-preview-img');
    const removeImageBtn = document.getElementById('remove-image-btn');

    if (imageInput && imagePreviewWrapper && imagePreviewImg) {
        imageInput.addEventListener('change', function () {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function (e) {
                    imagePreviewImg.src = e.target.result;
                    imagePreviewWrapper.style.display = 'block';
                };
                reader.readAsDataURL(file);
            }
        });

        if (removeImageBtn) {
            removeImageBtn.addEventListener('click', function () {
                imageInput.value = '';
                imagePreviewImg.src = '';
                imagePreviewWrapper.style.display = 'none';
            });
        }
    }

    // -----------------------------------------------------------
    // 2. AJAX Like / Unlike Toggle
    // -----------------------------------------------------------
    document.addEventListener('click', async (e) => {
        const likeBtn = e.target.closest('.js-like-btn');
        if (!likeBtn) return;

        e.preventDefault();
        const postId = likeBtn.dataset.postId;
        const likeUrl = likeBtn.dataset.url;
        const countSpan = likeBtn.querySelector('.js-like-count');

        try {
            const response = await fetch(likeUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    if (data.liked) {
                        likeBtn.classList.add('liked');
                    } else {
                        likeBtn.classList.remove('liked');
                    }
                    if (countSpan) {
                        countSpan.textContent = data.likes_count;
                    }
                }
            }
        } catch (err) {
            console.error('Error toggling like:', err);
        }
    });

    // -----------------------------------------------------------
    // 3. AJAX Follow / Unfollow Toggle
    // -----------------------------------------------------------
    document.addEventListener('click', async (e) => {
        const followBtn = e.target.closest('.js-follow-btn');
        if (!followBtn) return;

        e.preventDefault();
        const url = followBtn.dataset.url;
        const username = followBtn.dataset.username;

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    if (data.is_following) {
                        followBtn.classList.remove('follow-state');
                        followBtn.classList.add('following-state');
                        followBtn.textContent = 'Following';
                    } else {
                        followBtn.classList.remove('following-state');
                        followBtn.classList.add('follow-state');
                        followBtn.textContent = 'Follow';
                    }

                    // Update follower count on profile page if present
                    const followersCountEl = document.getElementById(`followers-count-${username}`);
                    if (followersCountEl) {
                        followersCountEl.textContent = data.followers_count;
                    }
                }
            }
        } catch (err) {
            console.error('Error toggling follow:', err);
        }
    });

    // -----------------------------------------------------------
    // 4. AJAX Inline Comment Submission
    // -----------------------------------------------------------
    document.addEventListener('submit', async (e) => {
        const commentForm = e.target.closest('.js-comment-form');
        if (!commentForm) return;

        e.preventDefault();
        const input = commentForm.querySelector('.comment-input');
        const content = input.value.trim();
        if (!content) return;

        const url = commentForm.action;
        const formData = new FormData(commentForm);
        const postId = commentForm.dataset.postId;
        const commentList = document.getElementById(`comments-list-${postId}`);
        const commentsCountEl = document.getElementById(`comments-count-${postId}`);

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            });

            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    input.value = '';

                    // If comments list exists, append new comment
                    if (commentList) {
                        const newCommentItem = document.createElement('div');
                        newCommentItem.className = 'comment-item';
                        newCommentItem.id = `comment-${data.comment_id}`;
                        newCommentItem.innerHTML = `
                            <img src="${data.author_avatar}" class="user-avatar-xs" alt="${data.author}">
                            <div class="comment-body">
                                <div class="comment-header">
                                    <a href="/profile/${data.author}/" class="comment-author-name">@${data.author}</a>
                                    <span class="comment-time">${data.created_at}</span>
                                </div>
                                <p class="comment-text">${escapeHtml(data.content)}</p>
                            </div>
                        `;
                        commentList.appendChild(newCommentItem);
                    }

                    if (commentsCountEl) {
                        commentsCountEl.textContent = data.comments_count;
                    }
                }
            }
        } catch (err) {
            console.error('Error adding comment:', err);
        }
    });

    // -----------------------------------------------------------
    // 5. Post Dropdown Menus (Edit / Delete)
    // -----------------------------------------------------------
    document.addEventListener('click', (e) => {
        const menuBtn = e.target.closest('.js-menu-btn');
        const allDropdowns = document.querySelectorAll('.post-dropdown');

        if (menuBtn) {
            e.stopPropagation();
            const dropdown = menuBtn.nextElementSibling;
            allDropdowns.forEach(d => {
                if (d !== dropdown) d.classList.remove('show');
            });
            dropdown.classList.toggle('show');
        } else {
            allDropdowns.forEach(d => d.classList.remove('show'));
        }
    });

    // -----------------------------------------------------------
    // 6. Toast Messages Auto-Dismiss
    // -----------------------------------------------------------
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateX(30px)';
            setTimeout(() => alert.remove(), 400);
        }, 4500);

        const closeBtn = alert.querySelector('.alert-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => alert.remove());
        }
    });

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
});
