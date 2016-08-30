from django.shortcuts import render

import rmapp.models as models


# Create your views here.
# Index that provides a description of the API
def index(request):

    tuples = []

    users = models.User.objects.all()
    for user in users:
        tokens = models.Token.objects.filter(user_id=user.id).all()
        tuple = {
            "user": user,
            "tokens": tokens
        }
        tuples += [tuple]

    return render(request, "demo.html", {"tuples": tuples})


# Create your views here.
# Index that provides a description of the API
def users(request):

    tuples = []

    users = models.User.objects.all()
    for user in users:
        tokens = models.Token.objects.filter(user_id=user.id).all()
        tuple = {
            "user": user,
            "tokens": tokens
        }
        tuples += [tuple]

    return render(request, "users.html", {"tuples": tuples})
