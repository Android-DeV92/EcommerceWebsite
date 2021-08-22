import json
from math import ceil
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from .Paytm import Checksum
from .models import Product, Contact, Order, OrderUpdate, Register

MERCHANT_KEY = 're4IKy2WlZxGssBe';


# Create your views here.
def front(request):
    return render(request, 'front.html')


def products(request):
    allProds = []
    catProds = Product.objects.values('category', 'id')
    cats = {item['category'] for item in catProds}
    for cat in cats:
        prod = Product.objects.filter(category=cat)
        n = len(prod)
        nSlides = n // 4 + ceil((n / 4) - (n // 4))
        allProds.append([prod, range(1, nSlides), nSlides])
    params = {'allProds': allProds}
    return render(request, 'products.html', params)


def boxoffour(request):
    # products = Product.objects.all()
    # print(products)
    # n = len(products)
    # nSlides = n // 4 + ceil((n / 4) - (n // 4))

    allProds = []
    catProds = Product.objects.values('category', 'id')
    cats = {item['category'] for item in catProds}
    for cat in cats:
        prod = Product.objects.filter(category=cat)
        n = len(prod)
        nSlides = n // 4 + ceil((n / 4) - (n // 4))
        allProds.append([prod, range(1, nSlides), nSlides])

    # params = {'no_of_slides': nSlides, 'range': range(1, nSlides), 'product': products}
    # allProds = [[products, range(1, nSlides), nSlides],
    #             [products, range(1, nSlides), nSlides]]
    params = {'allProds': allProds}
    return render(request, 'boxoffour.html', params)


def login(request):
    if request.method == 'GET':
        return render(request, 'login.html')
    else:
        username = request.POST.get("username")
        password = request.POST.get("password")
        res = Register(username=username, password=password)
        if len(res) > 0:
            return render(request, 'front.html', {'output': "Login Successful"})
        else:
            return render(request, 'login.html', {'output': "Login Failed!!!"})


def register(request):
    if request.method == 'GET':
        return render(request, 'register.html')
    else:
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        phone = request.POST.get("phone")
        register = Register(username=username, email=email, password=password, phone=phone)
        register.save()
    return render(request, 'login.html', {'output': "Register Successfully"})


@login_required()
def user_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse('login'))


def about(request):
    return render(request, 'about.html')


def contact(request):
    if request.method == "POST":
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        desc = request.POST.get('desc', '')
        print(name, email, phone, desc)
        contact = Contact(name=name, email=email, phone=phone, desc=desc)
        contact.save()
    return render(request, 'contact.html')


def tracker(request):
    if request.method == "POST":
        orderId = request.POST.get('orderId', '')
        email = request.POST.get('email', '')
        try:
            order = Order.objects.filter(order_id=orderId, email=email)
            if len(order) > 0:
                update = OrderUpdate.objects.filter(order_id=orderId)
                updates = []
                for item in update:
                    updates.append({'text': item.update_desc, 'time': item.timestamp})
                    response = json.dumps([updates, order[0].items_json], default=str)
                return HttpResponse(response)
            else:
                return HttpResponse('{}')
        except Exception as e:
            return HttpResponse('{}')

    return render(request, 'tracker.html')


def searchMatch(query, item):
    # return true only if query matches the item
    if query in item.desc.lower() or query in item.product_name.lower() or query in item.category.lower() or query in item.subcategory.lower():
        return True
    else:
        return False


def search(request):
    query = request.GET.get('search')
    allProds = []
    catprods = Product.objects.values('category', 'id')
    cats = {item['category'] for item in catprods}
    for cat in cats:
        prodtemp = Product.objects.filter(category=cat)
        prod = [item for item in prodtemp if searchMatch(query, item)]

        n = len(prod)
        nSlides = n // 4 + ceil((n / 4) - (n // 4))
        if len(prod) != 0:
            allProds.append([prod, range(1, nSlides), nSlides])
    params = {'allProds': allProds, "msg": ""}
    if len(allProds) == 0 or len(query) < 4:
        params = {'msg': "Please make sure to enter relevant search query"}
    return render(request, 'search.html', params)


def productView(request, myid):
    # fetch the product using id
    product = Product.objects.filter(id=myid)
    return render(request, 'prodView.html', {'product': product[0]})


def checkout(request):
    if request.method == "POST":
        items_json = request.POST.get('itemsJson', '')
        amount = request.POST.get('amount', '')
        fname = request.POST.get('fname', '')
        lname = request.POST.get('lname', '')
        username = request.POST.get('username', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        add1 = request.POST.get('add1', '')
        add2 = request.POST.get('add2', '')
        country = request.POST.get('country', '')
        state = request.POST.get('state', '')
        zip_code = request.POST.get('zip_code', '')
        order = Order(items_json=items_json, amount=amount, fname=fname, lname=lname, username=username, email=email,
                      phone=phone, add1=add1,
                      add2=add2, country=country, state=state, zip_code=zip_code)
        order.save()
        update = OrderUpdate(order_id=order.order_id, update_desc="the Order has been placed Successfully...")
        update.save()
        thank = True
        id = order.order_id
        # return render(request, 'checkout.html', {'thank': thank, 'id': id})
        # # request paytm to transfer the amount to your account after payment by user.
        param_dict = {

            'MID': 'UQyjWv73914192289471',
            'ORDER_ID': str(order.order_id),
            'TXN_AMOUNT': str(amount),
            'CUST_ID': email,
            'INDUSTRY_TYPE_ID': 'Retail',
            'WEBSITE': 'WEBSTAGING',
            'CHANNEL_ID': 'WEB',
            'CALLBACK_URL': 'http://127.0.0.1:8000/handlerequest/',

        }
        param_dict['CHECKSUMHASH'] = Checksum.generate_checksum(param_dict, MERCHANT_KEY)
        return render(request, 'paytm.html', {'param_dict': param_dict})
    return render(request, 'checkout.html')


def boxcheckout(request):
    if request.method == "POST":
        items_json = request.POST.get('itemsJson', '')
        amount = request.POST.get('amount', '')
        fname = request.POST.get('fname', '')
        lname = request.POST.get('lname', '')
        username = request.POST.get('username', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        add1 = request.POST.get('add1', '')
        add2 = request.POST.get('add2', '')
        country = request.POST.get('country', '')
        state = request.POST.get('state', '')
        zip_code = request.POST.get('zip_code', '')
        order = Order(items_json=items_json, amount=amount, fname=fname, lname=lname, username=username, email=email,
                      phone=phone, add1=add1,
                      add2=add2, country=country, state=state, zip_code=zip_code)
        order.save()
        update = OrderUpdate(order_id=order.order_id, update_desc="Your Order has been placed Successfully...")
        update.save()
        thank = True
        id = order.order_id
        # return render(request, 'boxcheckout.html', {'thank': thank, 'id': id})
        # request paytm to transfer the amount to your account after payment by user.
        param_dict = {

            'MID': 'UQyjWv73914192289471',
            'ORDER_ID': str(order.order_id),
            'TXN_AMOUNT': str(amount),
            'CUST_ID': email,
            'INDUSTRY_TYPE_ID': 'Retail',
            'WEBSITE': 'WEBSTAGING',
            'CHANNEL_ID': 'WEB',
            'CALLBACK_URL': 'http://127.0.0.1:8000/handlerequest/',

        }
        param_dict['CHECKSUMHASH'] = Checksum.generate_checksum(param_dict, MERCHANT_KEY)
        return render(request, 'paytm.html', {'param_dict': param_dict})
    return render(request, 'boxcheckout.html')


@csrf_exempt
def handlerequest(request):
    # paytm will send you post request here
    # return HttpResponse('Done')
    form = request.POST
    response_dict = {}
    for i in form.keys():
        response_dict[i] = form[i]
        if i == 'CHECKSUMHASH':
            checksum = form[i]

    verify = Checksum.verify_checksum(response_dict, MERCHANT_KEY, checksum)
    if verify:
        if response_dict['RESPCODE'] == '01':
            print('order successful')
        else:
            print('order was not successful because' + response_dict['RESPMSG'])
    return render(request, 'paymentstatus.html', {'response': response_dict})
