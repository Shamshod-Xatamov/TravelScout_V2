import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import Story, StoryImage, Comment

from .forms import StoryForm
@login_required
def stories_feed(request):
    stories = Story.objects.all()
    stories_data = []

    for story in stories:
        images = [img.image.url for img in story.images.all()]

        comments = []
        for c in story.comments.all():
            comments.append({
                'id': c.id,
                'author': c.author.username,
                'authorAvatar': c.author.profile.profile_picture.url if hasattr(c.author,
                                                                                'profile') and c.author.profile.profile_picture else None,
                'text': c.text,
                'timestamp': c.get_date()
            })

        user_avatar = None
        if hasattr(story.author, 'profile') and story.author.profile.profile_picture:
            user_avatar = story.author.profile.profile_picture.url

        stories_data.append({
            'id': story.id,
            'share_uuid': str(story.share_uuid),  # <--- UUID NI STRING QILIB BERAMIZ
            'author': story.author.username,
            'authorId': story.author.id,
            'authorAvatar': user_avatar,
            'location': story.location,
            'date': story.get_date(),
            'title': story.title,
            'content': story.content,
            'images': images,
            'likes': story.likes.count(),
            'views': story.views_count,
            'comments': comments,
            'isLiked': request.user in story.likes.all(),
            'isSaved': request.user in story.saved_by.all(),
        })

    context = {
        'stories_json': json.dumps(stories_data),
        'current_user_id': request.user.id,
        'current_user_name': request.user.username
    }
    return render(request, 'stories/feed.html', context)


# stories/views.py

# ... tepadagi kodlar ...

# PUBLIC DETAIL VIEW (UUID BILAN)
from django.shortcuts import render, get_object_or_404
from .models import Story


def story_detail(request, uuid):
    # 1. Storyni topamiz
    story = get_object_or_404(Story, share_uuid=uuid)

    # 2. View Count Logikasi (O'zgarishsiz qoldi)
    session_key = f'viewed_story_{story.id}'
    if not request.session.get(session_key):
        story.views_count += 1
        story.save()
        request.session[session_key] = True
        request.session.modified = True

    # 3. Avatar Logikasi
    user_avatar = None
    if hasattr(story.author, 'profile') and story.author.profile.profile_picture:
        user_avatar = story.author.profile.profile_picture.url

    # --- 4. ENG MUHIM JOYI: USER HOLATINI TEKSHIRISH ---
    is_liked = False
    is_saved = False

    if request.user.is_authenticated:
        # User bu hikoyaga like bosganmi?
        is_liked = story.likes.filter(id=request.user.id).exists()

        # User bu hikoyani saqlaganmi? (saved_by - modeldagi related_name ga qarab o'zgarishi mumkin)
        # Agar modelda related_name='saved_stories' bo'lsa, story.saved_stories.filter(...) bo'ladi.
        # Odatda ko'p ishlatiladigan variant:
        is_saved = story.saved_by.filter(id=request.user.id).exists()

    # 5. Rasmlar (To'g'ridan-to'g'ri obyektni beramiz, shunda template .url qilib oladi)
    images = story.images.all()

    # Kommentariyalarni eng yangisidan boshlab olamiz
    comments = story.comments.all().order_by('-created_at')

    context = {
        'story': story,
        'images': story.images.all(),
        'comments': comments,  # <--- MANA SHU KERAK
        'is_liked': is_liked,
        'is_saved': is_saved,
    }

    return render(request, 'stories/detail.html', context)
# --- API ENDPOINTS ---

@login_required
@require_POST
def create_story(request):
    try:
        title = request.POST.get('title')
        location = request.POST.get('location')
        content = request.POST.get('content')
        images = request.FILES.getlist('images')

        story = Story.objects.create(
            author=request.user,
            title=title,
            location=location,
            content=content
        )

        for image in images:
            StoryImage.objects.create(story=story, image=image)

        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
@require_POST
def toggle_like(request, story_id):
    story = get_object_or_404(Story, id=story_id)
    if request.user in story.likes.all():
        story.likes.remove(request.user)
        liked = False
    else:
        story.likes.add(request.user)
        liked = True
    return JsonResponse({'status': 'success', 'liked': liked})


@login_required
@require_POST
def toggle_save(request, story_id):
    story = get_object_or_404(Story, id=story_id)
    if request.user in story.saved_by.all():
        story.saved_by.remove(request.user)
        saved = False
    else:
        story.saved_by.add(request.user)
        saved = True
    return JsonResponse({'status': 'success', 'saved': saved})


@login_required
@require_POST
def add_comment(request, story_id):
    data = json.loads(request.body)
    text = data.get('text')
    if text:
        story = get_object_or_404(Story, id=story_id)
        Comment.objects.create(story=story, author=request.user, text=text)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)


@login_required
@require_POST
def delete_story(request, story_id):
    story = get_object_or_404(Story, id=story_id, author=request.user)
    story.delete()
    return JsonResponse({'status': 'success'})


# stories/views.py
# ...

@login_required
@require_POST
def edit_story(request, story_id):
    # Faqat o'z hikoyasini edit qilishga ruxsat beramiz
    story = get_object_or_404(Story, id=story_id, author=request.user)

    # Story ma'lumotlarini o'zgartirish uchun Formni to'ldiramiz
    # instance=story o'sha Storyni topib, uning ma'lumotini yangilash uchun
    form = StoryForm(request.POST, instance=story)

    if form.is_valid():
        try:
            form.save()

            # --- MUHIM: RASM UCHUN YANGI MANTIQ ---
            images = request.FILES.getlist('images')

            if images:
                # 1. Eski rasmlarni o'chirish (agar yangi rasm tanlangan bo'lsa)
                story.images.all().delete()

                # 2. Yangi rasmlarni saqlash
                for image in images:
                    StoryImage.objects.create(story=story, image=image)

            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# ...

@login_required
@require_POST
def increment_share_count(request, story_id):
    story = get_object_or_404(Story, id=story_id)
    story.shares_count += 1
    story.save()
    return JsonResponse({'status': 'success', 'shares': story.shares_count})