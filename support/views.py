import json
from django.shortcuts import render
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from .forms import SupportForm

def support_page(request):
    if request.method == "POST":
        try:
            # JSON ma'lumotni o'qish
            data = json.loads(request.body)
            form = SupportForm(data)

            if form.is_valid():
                # Ma'lumotlarni olish
                name = form.cleaned_data['name']
                email = form.cleaned_data['email']
                subject = form.cleaned_data['subject']
                message_text = form.cleaned_data['message']

                # 1. Email yuborish logikasi (Hozircha konsolga chiqaramiz)
                full_message = f"From: {name} <{email}>\n\nMessage:\n{message_text}"
                print(f"--- NEW SUPPORT MESSAGE ---\n{full_message}\n---------------------------")

                # Agar haqiqiy email jo'natmoqchi bo'lsangiz, buni yoqasiz:
                # send_mail(
                #     subject=f"Support: {subject}",
                #     message=full_message,
                #     from_email=settings.DEFAULT_FROM_EMAIL,
                #     recipient_list=[settings.EMAIL_HOST_USER], # O'zingizga boradi
                #     fail_silently=False,
                # )

                return JsonResponse({'status': 'success', 'message': 'Message sent successfully!'})
            else:
                return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return render(request, 'support/support.html')