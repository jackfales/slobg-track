from django.shortcuts import render, redirect

from .forms import SignUpForm, ProfileForm, VolunteerRecordForm, FilterForm
from .models import VolunteerRecord
from django.conf import settings
# Signup/Login stuff
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
# Csv stuff
from django.http import HttpResponse
import csv
from django.db.models import Sum


# Email Receipt Stuff
from django.core import mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags


#Export to csv function
def export_csv(request, start_date, end_date):
   print(request)
   response = HttpResponse(content_type='text/csv')
   response['Content-Disposition'] = 'attachment; filename="volunteer_history: {} to {}.csv"'.format(start_date, end_date)
   print(start_date)
   print(end_date)
   writer = csv.writer(response)
   writer.writerow(['Volunteer', 'Date', 'Hours', 'Description', 'Supervisor'])

   if(request.user.is_superuser):
      records = VolunteerRecord.objects.all().filter(date__range=[start_date, end_date])
   else:
      records = VolunteerRecord.objects.filter(owner=request.user, date__range=[start_date, end_date])

   for record in records:
      volunteer = record.owner.first_name + ' ' + record.owner.last_name
      date = record.date
      hours = record.hours
      desc = record.activity
      supervisor = record.supervisor

      writer.writerow((volunteer, date, hours, desc, supervisor))
   
   return response

@login_required
def export(request):
   if request.method == "POST":
      form = FilterForm(request.POST)
      if form.is_valid():
         start = form.cleaned_data['start_date']
         end = form.cleaned_data['end_date']
         response = export_csv(request, start, end)
         return response
      else:
         print("form not valid")
   else:
      form = FilterForm()
   return render(request, 'export.html', {'form':form})


def landing(request):
   return render(request, 'landing.html')

def signup(request):
   if request.method == "POST":
      user_form = SignUpForm(request.POST)
      # profile_form = ProfileForm(request.POST)
      if user_form.is_valid():
         user_form.save()
         # profile_form.save()
         username = user_form.cleaned_data.get('username')
         raw_password = user_form.cleaned_data.get('password1')
         user = authenticate(username=username, password=raw_password)
         login(request, user)
         return redirect('/add_individual_hours')
      else:
         print("form not valid")
   else:
      user_form = SignUpForm()
      # profile_form = ProfileForm()
   return render(request, "signup.html", {
         "user_form" : user_form,
         # "profile_form" : profile_form
      })


@login_required
def home(request):
   return redirect('add_individual_hours')

@login_required
def success(request):
    return render(request, "success.html")

@login_required
def add_individual_hours(request):
   if request.method == "POST":
      form = VolunteerRecordForm(request.POST)
      if form.is_valid():
            # Set user field in the form here
            print("before commit false")
            record = form.save(commit = False)
            print("after", record)
            record.owner = request.user
            record.save()
            print("success")
            subject = 'SLO Botanical Garden - Tracking Form Receipt'
            html_message = render_to_string('email_template.html', {'form': form.cleaned_data}) 
            plain_message = strip_tags(html_message)
            from_email = settings.DEFAULT_FROM_EMAIL
            to = request.user.email
            mail.send_mail(subject, plain_message, from_email, [to], html_message=html_message)
            return redirect('/success')
      else:
         print("form not valid")
   else:
      form = VolunteerRecordForm()

   return render(request, "add_individual_hours.html", {"form": form})



# @login_required
# def add_group_hours(request):
#    form = GroupVolunteerForm(request.POST or None)
#    if form.is_valid():
#       form = GroupVolunteerForm()
#       form.save()
#    context = {
#       'form': form
#    }
#    return render(request, 'group_sign_in.html', {})

@login_required
def history(request):
   current_user = request.user
   if current_user.is_staff:
      records = VolunteerRecord.objects.all()
   else:
      records = VolunteerRecord.objects.filter(owner = current_user)
   return render(request, "history.html", {"records" : records})


@login_required
def profile(request):
   current_user = request.user
   hours = VolunteerRecord.objects.filter(
      owner = current_user).all().aggregate(
         total_hours=Sum('hours'))['total_hours'] or 0
   return render(request, "profile.html", {'hours' : hours, 'user': current_user})

@login_required
def update_profile(request):
   if request.method == "POST":
      user_form = SignUpForm(request.POST, instance=request.user)
      profile_form = ProfileForm(request.POST, instance=request.user.profile)
      if user_form.is_valid() and profile_form.is_valid():
         user_form.save()
         profile_form.save()
         print("Profile successfully updated.")
         return redirect('/profile')
      else:
         print("user_form or profile_form not valid.")
   else:
        user_form = SignUpForm(instance=request.user)
        profile_form = ProfileForm(instance=request.user.profile)
   return render(request, 'update_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })
