from django.shortcuts import render, redirect
from django.contrib.auth.models import User, auth
from django.contrib import messages

# Create your views here.


def password_check(passwd):

    SpecialSym = ['$', '@', '#', '%']
    val = True

    if len(passwd) < 6:
        val = [False, 'length_at_least_6']
        return val

    if len(passwd) > 20:
        val = [False, 'length_atmost_8']
        return val

    if not any(char.isdigit() for char in passwd):
        val = [False, 'at_least_one_num']

    if not any(char.isupper() for char in passwd):
        val = [False, 'at_least_one_upper']

    if not any(char.islower() for char in passwd):
        val = [False, 'at_least_one_lower']
        return val
    if not any(char in SpecialSym for char in passwd):
        val = [False, 'at_least_one_special']
        return val
    return [val, ""]


def register(request):
    if request.user.is_authenticated:
        return redirect("/")

    if(request.method == 'POST'):
        first_name = request.POST["first_name"]
        last_name = request.POST["last_name"]
        user_name = request.POST["user_name"]
        email = request.POST["email_id"]
        password1 = request.POST["password1"]
        password2 = request.POST["password2"]
        mat = password_check(password1)
        print("value of val", mat)
        if(password1 != password2):
            return render(request, 'register.html', {"password_match_error": True})
        elif(mat[0] == False):
            return render(request, 'register.html', {mat[1]: True})
        elif(User.objects.filter(username=user_name).exists()):
            return render(request, 'register.html', {"username_error": True})
        elif(User.objects.filter(email=email).exists()):
            return render(request, 'register.html', {"email_error": True})
        else:
            user = User.objects.create_user(
                username=user_name, password=password1, email=email, first_name=first_name, last_name=last_name)
            user.save()
            messages.info(request, "User Created")
            return redirect('login')
    else:
        return render(request, "register.html")


def login(request):
    if request.user.is_authenticated:
        return redirect("/")

    if(request.method == 'POST'):
        user_name = request.POST["user_name"]
        password = request.POST["password"]
        user = auth.authenticate(username=user_name, password=password)
        if(user is not None):
            auth.login(request, user)
            messages.info(request, 'Login Successful')
            return redirect("/")
        else:
            messages.info(request, 'Invalid Credentials')
            return redirect('login')
    else:
        return render(request, "login.html")


def logout(request):
    if request.user.is_authenticated:
        auth.logout(request)
    return redirect("/")
