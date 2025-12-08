import os
import json
import re

from allauth.account.views import PasswordChangeView
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from groq import Groq
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, CreateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.urls import reverse_lazy, reverse
from django.db.models import Sum, Count

from .models import Trip, Profile
from .forms import TripForm, UserUpdateForm, ProfileUpdateForm, CustomSignUpForm


# 1. Landing Page
class HomeView(TemplateView):
    template_name = 'home.html'


class SignUpView(CreateView):
    form_class = CustomSignUpForm
    success_url = reverse_lazy('login')
    template_name = 'account/signup.html'  # <-- Papka nomini 'account' qiling


# 3. Dashboard
class TripListView(LoginRequiredMixin, ListView):
    model = Trip
    template_name = 'my_plans.html'
    context_object_name = 'trips'
    login_url = '/accounts/login/'

    def get_queryset(self):
        queryset = Trip.objects.filter(user=self.request.user).order_by('-created_at')

        # SEARCH
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(destination__icontains=search_query)

        # FILTER
        budget_filter = self.request.GET.get('budget')
        if budget_filter:
            queryset = queryset.filter(budget_type=budget_filter)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_trips = self.get_queryset()

        # Stats...
        total = user_trips.aggregate(Sum('budget_amount'))['budget_amount__sum']
        context['total_budget'] = total if total else 0
        context['favorites_count'] = user_trips.filter(is_favorite=True).count()

        # Top Destination...
        top_dest_data = user_trips.values('destination') \
            .annotate(num_trips=Count('destination')) \
            .order_by('-num_trips') \
            .first()
        context['top_destination'] = top_dest_data['destination'] if top_dest_data else "No trips yet"

        # --- O'ZGARTIRILGAN QISM ---
        context['u_form'] = UserUpdateForm(instance=self.request.user)

        # 1. try/except o'rniga MANA BUNISINI ISHLATAMIZ:
        # Bu kod: "Profilni top, agar yo'q bo'lsa, shu zahoti yangisini yaratib ber" deydi.
        # Beton yechim!
        profile, created = Profile.objects.get_or_create(user=self.request.user)

        # 2. Endi bizda aniq profil bor, shuni formaga beramiz
        context['p_form'] = ProfileUpdateForm(instance=profile)
        # ---------------------------

        context['password_change_form'] = PasswordChangeForm(self.request.user)
        return context



class TripCreateView(LoginRequiredMixin, CreateView):
    model = Trip
    form_class = TripForm
    template_name = 'trip_new.html'
    login_url = '/accounts/login/'

    def form_valid(self, form):
        form.instance.user = self.request.user

        # Ma'lumotlarni olamiz
        days = form.cleaned_data['duration_days']
        budget_type = form.cleaned_data['budget_type']
        destination = form.cleaned_data['destination']
        interests = form.cleaned_data['interests']

        cost_map = {'Economy': 100, 'Standard': 250, 'Luxury': 500}
        form.instance.budget_amount = cost_map.get(budget_type, 200) * days

        # --- GROQ AI LOGIC ---
        try:
            api_key = getattr(settings, 'GROQ_API_KEY', None)

            if api_key:
                client = Groq(api_key=api_key)


                prompt = f"""
                                Act as a local travel expert. Generate a {days}-day itinerary for {destination}.
                                Budget Level: {budget_type}. Interests: {interests}.

                                CRITICAL INSTRUCTIONS FOR COST CALCULATION:
                                1. Calculate TOTAL COST for ONE PERSON (Excluding Flights).
                                2. Be CONSERVATIVE and REALISTIC. Do not overestimate.
                                3. Logic:
                                   - Economy: Hostels/Budget Hotels, Street Food, Public Transport. (~$50-$100/day excluding accommodation)
                                   - Standard: 3-Star Hotels, Casual Dining, Mix of Taxi/Metro.
                                   - Luxury: 4-5 Star Hotels, Fine Dining, Private Transport.

                                4. RETURN ONLY RAW JSON. Format:
                                {{
                                  "estimated_cost": 800,  <-- Example: Moderate price for {days} days
                                  "currency": "USD",
                                  "days": [
                                    {{
                                      "day": 1,
                                      "title": "Title",
                                      "activities": [
                                        {{
                                          "time": "09:00",
                                          "title": "Activity",
                                          "description": "Short desc",
                                          "location": "Loc",
                                          "type": "morning",
                                          "icon": "coffee", 
                                          "cost": "$10"
                                        }}
                                      ]
                                    }}
                                  ]
                                }}
                                """
                chat_completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "You are a JSON generator."},
                        {"role": "user", "content": prompt}
                    ],
                    model="llama-3.3-70b-versatile",
                    temperature=0.5,
                    response_format={"type": "json_object"}
                )

                ai_reply = chat_completion.choices[0].message.content
                clean_json = ai_reply.replace("```json", "").replace("```", "").strip()
                json_data = json.loads(clean_json)

                # 2. ITINERARYNI SAQLASH
                form.instance.itinerary = json.dumps(json_data)

                # 3. NARXNI YANGILASH (Agar AI to'g'ri bersa)
                try:
                    raw_cost = json_data.get('estimated_cost')
                    if raw_cost:
                        # Har qanday belgilarni olib tashlab, faqat raqamni olamiz
                        cost_str = str(raw_cost)
                        clean_cost = re.sub(r'[^\d]', '', cost_str)

                        final_cost = int(clean_cost)

                        # Agar narx 0 dan katta bo'lsa, o'sha narxni olamiz!
                        if final_cost > 0:
                            form.instance.budget_amount = final_cost
                            print(f"AI narxi qabul qilindi: ${final_cost}")
                except Exception as cost_e:
                    print(f"Narxni o'qishda xato: {cost_e}")
                    # Xato bo'lsa, tepadagi Fixed narx o'zgarishsiz qoladi

            else:
                form.instance.itinerary = ""

        except Exception as e:
            print(f"AI Error: {e}")
            form.instance.itinerary = ""
            # Xato bo'lsa ham Fixed narx qolaveradi

        return super().form_valid(form)

    def get_success_url(self):
        return reverse('trip_detail', kwargs={'pk': self.object.pk})

# 5. Detail View (MUHIM QISM)
class TripDetailView(LoginRequiredMixin, DetailView):
    model = Trip
    template_name = 'trip_detail.html'
    context_object_name = 'trip'
    login_url = '/accounts/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 1. JSON ni shu yerda Python Dictionaryga aylantiramiz
        # Shunda template ichida 'load' qilish shart emas
        try:
            if self.object.itinerary:
                context['itinerary_data'] = json.loads(self.object.itinerary)
            else:
                context['itinerary_data'] = None
        except Exception as e:
            print(f"JSON Parse Error: {e}")
            context['itinerary_data'] = None

        # 2. Interests stringini array (ro'yxat) qilamiz
        if self.object.interests:
            context['clean_interests'] = [x.strip() for x in self.object.interests.split(',')]

        return context



# 1. DELETE TRIP (Sahifaga o'tadigan qilish)
@login_required
def delete_trip(request, pk):
    trip = get_object_or_404(Trip, pk=pk, user=request.user)

    if request.method == 'POST':
        # Agar "Yes, Delete" tugmasi bosilsa o'chiramiz
        trip.delete()
        return redirect('my_plans_list')

    # Agar shunchaki kirilsa, Delete sahifasini ko'rsatamiz
    return render(request, 'trip_delete.html', {'trip': trip})


# 2. SHARE OPTIONS (Yangi sahifa: Linkni ko'rsatish uchun)
@login_required
def share_trip_options(request, pk):
    trip = get_object_or_404(Trip, pk=pk, user=request.user)
    # To'liq share linkni yasaymiz
    share_url = request.build_absolute_uri(reverse('trip_share', args=[trip.share_uuid]))

    return render(request, 'trip_share.html', {
        'trip': trip,
        'share_url': share_url
    })


def public_trip_detail(request, share_uuid):
    trip = get_object_or_404(Trip, share_uuid=share_uuid)
    # Detail View logikasini qaytaramiz (JSON parse)
    itinerary_data = None
    try:
        if trip.itinerary:
            itinerary_data = json.loads(trip.itinerary)
    except:
        pass

    clean_interests = []
    if trip.interests:
        clean_interests = [x.strip() for x in trip.interests.split(',')]

    return render(request, 'trip_detail.html', {
        'trip': trip,
        'itinerary_data': itinerary_data,
        'clean_interests': clean_interests,
        'is_public': True
    })


# 9. Like (Toggle Favorite)
# trips/views.py ichida:

@login_required
@require_POST
def toggle_favorite(request, pk):
    trip = get_object_or_404(Trip, pk=pk, user=request.user)
    trip.is_favorite = not trip.is_favorite
    trip.save()

    # YANGI QO'SHILGAN QISM: Foydalanuvchining jami likelarini sanaymiz
    new_total_favorites = Trip.objects.filter(user=request.user, is_favorite=True).count()

    return JsonResponse({
        'status': 'ok',
        'is_favorite': trip.is_favorite,
        'new_total': new_total_favorites  # <--- Buni front-endga yuboramiz
    })



@login_required
def profile_edit(request):
    if request.method == 'POST':
        # 1. Formalarni ma'lumotlar bilan to'ldiramiz
        u_form = UserUpdateForm(request.POST, instance=request.user)

        # MUHIM: Rasm yuklanishi uchun 'request.FILES' shu yerda turibdi, tegmadim!
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

        # 2. Validatsiyani tekshiramiz
        if u_form.is_valid() and p_form.is_valid():

            # --- YANGI QISM: O'zgarish borligini tekshirish ---
            if u_form.has_changed() or p_form.has_changed():
                u_form.save()
                p_form.save()
                # Faqat o'zgarish bo'lsa xabar chiqaramiz
                messages.success(request, 'Your profile has been updated!')

            # Agar o'zgarish bo'lmasa, 'else' shart emas,
            # shunchaki xabar qo'shilmaydi va kod pastga tushib redirect bo'ladi.

            return redirect('my_plans_list')
        else:
            # Agar xatolik bo'lsa (masalan email formati noto'g'ri)
            messages.error(request, 'Please correct the errors below.')
            return redirect('my_plans_list')

    # POST bo'lmasa (GET so'rovda)
    return redirect('my_plans_list')

@require_POST
@login_required
def ajax_password_change(request):
    form = PasswordChangeForm(request.user, request.POST)

    if form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)  # Sessiyani yangilash
        return JsonResponse({'status': 'success', 'message': 'Password updated successfully!'})
    else:
        # Xatolarni oddiy matn qilib jo'natamiz
        return JsonResponse({
            'status': 'error',
            'errors': form.errors.get_json_data()  # Xatolarni to'liq olamiz
        }, status=400)