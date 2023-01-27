from django.shortcuts import render
from drowsiness_detection.models import drowsiness_history
from django.contrib.auth.decorators import login_required

# Create your views here.


@login_required(login_url="/accounts/login")
def generate_hist(request):
    items = drowsiness_history.objects.all()
    dct = {}
    for i in items:
        if i.USERNAME not in dct:
            dct[i.USERNAME] = 1
        else:
            dct[i.USERNAME] += 1
    x_val = list(dct.keys())
    y_val = list(dct.values())
    dct1 = {}
    dct2 = {}
    for i in items:
        if i.TIME.date() not in dct1:
            dct1[i.TIME.date()] = 1
        else:
            dct1[i.TIME.date()] += 1
    for i in items:
        if(i.TIME.hour >= 4 and i.TIME.hour < 12):
            if("morning" not in dct2):
                dct2['morning'] = 1
            else:
                dct2["morning"] += 1
        elif(i.TIME.hour >= 12 and i.TIME.hour < 17):
            if("afternoon" not in dct2):
                dct2['afternoon'] = 1
            else:
                dct2["afternoon"] += 1
        elif(i.TIME.hour >= 17 and i.TIME.hour < 19):
            if("evening" not in dct2):
                dct2['evening'] = 1
            else:
                dct2["evening"] += 1
        else:
            if("night" not in dct2):
                dct2['night'] = 1
            else:
                dct2["night"] += 1
    x_val1 = list(dct1.keys())
    y_val1 = list(dct1.values())
    x_val2 = list(dct2.keys())
    y_val2 = list(dct2.values())
    val = {'x': x_val, 'y': y_val, 'x1': x_val1,
           'y1': y_val1, 'x2': x_val2, 'y2': y_val2}
    return render(request, "admin_dashboard.html", val)
