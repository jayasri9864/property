from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login


from datetime import date
import random
import string
import json

from .models import UserRegister, BuyerListing, TenantListing, Transaction, Property, House, Payment
from .forms import BuyerListingForm, TenantListingForm


def home(request):
    return render(request, 'home.html')


def buy(request):
    return render(request, 'buy.html')


def signup(request):
    if request.method == "POST":
        name        = request.POST.get('name')
        email       = request.POST.get('email')
        password    = request.POST.get('password')
        role        = request.POST.get('role')
        age         = request.POST.get('age')
        profile_pic = request.FILES.get('profile_pic')

        if not age or not age.isdigit():
            return HttpResponse("Valid age is required")

        if role not in ['admin', 'seller', 'buyer', 'tenant']:
            return HttpResponse("Invalid role")

        UserRegister.objects.create(
            name=name,
            email=email,
            password=make_password(password),
            role=role,
            age=age,
            profile_pic=profile_pic
        )
        return redirect('login')

    return render(request, 'signup.html')


def sell(request):
    if request.method == "POST":

        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@gmail.com', 'is_staff': True}
        )

        if 'buyer_submit' in request.POST:
            buyer_form = BuyerListingForm(request.POST, request.FILES)
            if buyer_form.is_valid():

                # ✅ FIX 1: Duplicate check — same house_name + location இருந்தா save பண்ணாதே
                house_name = buyer_form.cleaned_data.get('house_name', '').strip()
                location   = buyer_form.cleaned_data.get('location', '').strip()

                already_exists = BuyerListing.objects.filter(
                    house_name__iexact=house_name,
                    location__iexact=location
                ).exists()

                if not already_exists:
                    buyer = buyer_form.save()

                    prop, _ = Property.objects.get_or_create(
                        name=buyer.house_name,
                        defaults={
                            'location': buyer.location,
                            'price':    buyer.price,
                            'status':   'available',
                        }
                    )
                    prop.status = 'available'
                    prop.save()

                # ✅ FIX 2: PRG pattern — POST உடனே redirect, page reload duplicate தடுக்க
                return redirect('property:sell')

        elif 'tenant_submit' in request.POST:
            tenant_form = TenantListingForm(request.POST, request.FILES)
            if tenant_form.is_valid():

                # ✅ FIX 1: Duplicate check — same house_name + location இருந்தா save பண்ணாதே
                house_name = tenant_form.cleaned_data.get('house_name', '').strip()
                location   = tenant_form.cleaned_data.get('location', '').strip()

                already_exists = TenantListing.objects.filter(
                    house_name__iexact=house_name,
                    location__iexact=location
                ).exists()

                if not already_exists:
                    tenant = tenant_form.save()

                    prop, _ = Property.objects.get_or_create(
                        name=tenant.house_name,
                        defaults={
                            'location': tenant.location,
                            'price':    tenant.rent_amount,
                            'status':   'available',
                        }
                    )
                    prop.status = 'available'
                    prop.save()

                # ✅ FIX 2: PRG pattern — POST உடனே redirect
                return redirect('property:sell')

    # GET — listings காட்டு
    context = {
        'buyer_listings':  BuyerListing.objects.all(),
        'tenant_listings': TenantListing.objects.all(),
    }
    return render(request, 'sell.html', context)


def submit_buyer(request):
    if request.method == 'POST':
        form = BuyerListingForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('buyer_detail')
    return redirect('buyer_detail')


def submit_tenant(request):
    if request.method == 'POST':
        form = TenantListingForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('buyer_detail')
    return redirect('buyer_detail')


def buyer_detail(request, pk):
    listing = get_object_or_404(BuyerListing, pk=pk)
    return render(request, 'buyer_detail.html', {'listing': listing})


def tenant_detail(request, pk):
    listing = get_object_or_404(TenantListing, pk=pk)
    rules   = [r.strip() for r in listing.tenant_rules.replace('\n', ',').split(',') if r.strip()]
    return render(request, 'tenant_detail.html', {'listing': listing, 'rules': rules})


def admin_dashboard(request):

    if not request.session.get('is_admin'):
        return redirect("property:login")

    today = date.today()

    today_bought = Transaction.objects.filter(
        transaction_type='buy',
        transaction_date__date=today
    )

    today_rented = Transaction.objects.filter(
        transaction_type='rent',
        transaction_date__date=today
    )

    total_properties = Property.objects.count()
    total_sold       = Property.objects.filter(status='sold').count()
    total_rented_p   = Property.objects.filter(status='rented').count()
    total_available  = Property.objects.filter(status='available').count()
    total_users      = User.objects.filter(is_staff=False).count()

    recent_transactions = Transaction.objects.all().order_by('-transaction_date')[:10]

    buyer_listings  = BuyerListing.objects.all().order_by('-created_at')
    tenant_listings = TenantListing.objects.all().order_by('-created_at')

    context = {
        'today_bought':       today_bought,
        'today_rented':       today_rented,
        'today_bought_count': today_bought.count(),
        'today_rented_count': today_rented.count(),

        'total_properties': total_properties,
        'total_sold':       total_sold,
        'total_rented':     total_rented_p,
        'total_available':  total_available,
        'total_users':      total_users,

        'recent_transactions': recent_transactions,
        'today':               today,

        'buyer_listings':        buyer_listings,
        'tenant_listings':       tenant_listings,
        'buyer_listings_count':  buyer_listings.count(),
        'tenant_listings_count': tenant_listings.count(),
    }

    return render(request, 'admin_dashboard.html', context)

def login_view(request):
    if request.method == "POST":
        role     = request.POST.get("role")
        email    = request.POST.get("email")
        password = request.POST.get("password")

        if role == "admin":
            if email == "admin@gmail.com" and password == "admin123":
                request.session['is_admin'] = True
                return redirect("property:admin_dashboard")
            else:
                return render(request, "login.html", {"error": "Invalid Admin credentials"})

        elif role == "user":
            from django.contrib.auth.hashers import check_password, make_password

            user = UserRegister.objects.filter(email=email).first()

            if user is None:
                # ✅ புதுசா வந்தா — auto create
                user = UserRegister.objects.create(
                    name=email.split('@')[0],
                    email=email,
                    password=make_password(password),
                    role='tenant',
                )

            if check_password(password, user.password):
                request.session['is_user'] = True
                request.session['user_id'] = user.id
                return redirect("property:rent_dashboard")
            else:
                return render(request, "login.html", {"error": "Invalid password"})

    return render(request, "login.html")
def rent_dashboard(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('property:login')

    user = UserRegister.objects.filter(id=user_id).first()
    if not user:
        return redirect('property:login')

    house           = House.objects.filter(user=user).first()
    payments        = []
    payment_summary = {'eb': 0, 'water': 0, 'rent': 0, 'total': 0}

    if house:
        payments = Payment.objects.filter(house=house).order_by('-paid_on')
        for p in payments:
            payment_summary[p.bill_type] += float(p.amount)
            payment_summary['total']     += float(p.amount)

    context = {
        'user':            user,
        'house':           house,
        'payments':        payments,
        'payment_summary': payment_summary,
        'months': [
            'January', 'February', 'March', 'April',
            'May', 'June', 'July', 'August',
            'September', 'October', 'November', 'December'
        ],
        'years': list(range(2023, 2030)),
    }
    return render(request, 'rent_dashboard.html', context)


def create_house(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('property:login')

    if request.method == "POST":
        user     = UserRegister.objects.filter(id=user_id).first()
        existing = House.objects.filter(user=user).first()
        if existing:
            messages.warning(request, f"House ID ஏற்கனவே உள்ளது: {existing.house_id} ⚠️")
            return redirect('property:rent_dashboard')

        tenant_name  = request.POST.get('tenant_name', '').strip()
        phone        = request.POST.get('phone', '').strip()
        address      = request.POST.get('address', '').strip()
        city         = request.POST.get('city', '').strip()
        floor_unit   = request.POST.get('floor_unit', '').strip()
        monthly_rent = request.POST.get('monthly_rent', '0').strip()

        if not all([tenant_name, phone, address, city]):
            messages.error(request, "அனைத்து விவரங்களையும் நிரப்பவும் ❌")
            return redirect('property:rent_dashboard')

        suffix   = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        house_id = f"HSE-{suffix}-{str(user_id).zfill(3)}"

        House.objects.create(
            user=user,
            house_id=house_id,
            tenant_name=tenant_name,
            phone=phone,
            address=address,
            city=city,
            floor_unit=floor_unit,
            monthly_rent=monthly_rent or 0,
        )
        messages.success(request, f"House ID வெற்றிகரமாக உருவாக்கப்பட்டது: {house_id} ✅")
        return redirect('property:rent_dashboard')

    return redirect('property:rent_dashboard')


def pay_bill(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('property:login')

    if request.method == "POST":
        user         = UserRegister.objects.filter(id=user_id).first()
        house_id_str = request.POST.get('house_id', '').strip()
        bill_type    = request.POST.get('bill_type', '').strip()
        amount       = request.POST.get('amount', '0').strip()
        month        = request.POST.get('month', '').strip()
        year         = request.POST.get('year', '').strip()
        units_used   = request.POST.get('units_used', None)

        house = House.objects.filter(house_id=house_id_str, user=user).first()
        if not house:
            messages.error(request, "Invalid House ID ❌")
            return redirect('property:rent_dashboard')

        if not all([bill_type, amount, month, year]):
            messages.error(request, "அனைத்து விவரங்களையும் நிரப்பவும் ❌")
            return redirect('property:rent_dashboard')

        already_paid = Payment.objects.filter(
            house=house, bill_type=bill_type, month=month, year=int(year)
        ).first()

        if already_paid:
            messages.warning(request,
                f"⚠️ {month} {year} — {bill_type.upper()} ஏற்கனவே pay செய்யப்பட்டது! "
                f"(₹{already_paid.amount}) | {already_paid.payment_id}")
            return redirect('property:rent_dashboard')

        pay_id = "PAY-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

        Payment.objects.create(
            user=user,
            house=house,
            bill_type=bill_type,
            amount=float(amount),
            month=month,
            year=int(year),
            units_used=int(units_used) if units_used and units_used.isdigit() else None,
            payment_id=pay_id,
        )

        bill_label = {'rent': 'Rent', 'eb': 'EB Bill', 'water': 'Water Bill'}.get(bill_type, bill_type)
        messages.success(request,
            f"✅ {bill_label} ({month} {year}) — ₹{float(amount):,.2f} successfully completed | {pay_id}")
        return redirect('property:rent_dashboard')

    return redirect('property:rent_dashboard')


def logout_view(request):
    request.session.flush()
    return redirect('property:login')


# ============================================================
# ✅ FIXED: save_transaction — Buy பண்ணா BuyerListing delete,
#                              Rent பண்ணா TenantListing delete
# ============================================================
@csrf_exempt
def save_transaction(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except Exception:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        property_name    = data.get('property', '').strip()
        property_loc     = data.get('propertyLoc', '').strip()
        amount           = data.get('amount', 0)
        transaction_type = data.get('transaction_type', 'buy')
        user_email       = data.get('userEmail', '')
        user_name        = data.get('user', '')

        # Property record — get_or_create
        prop, _ = Property.objects.get_or_create(
            name=property_name,
            defaults={
                'location': property_loc,
                'price':    amount,
                'status':   'available',
            }
        )

        # ✅ Status update
        if transaction_type == 'buy':
            prop.status = 'sold'
        else:
            prop.status = 'rented'
        prop.save()

        # User record — get_or_create
        user, _ = User.objects.get_or_create(
            email=user_email,
            defaults={
                'username':   user_email,
                'first_name': user_name,
            }
        )

        # Transaction save
        Transaction.objects.create(
            user=user,
            property=prop,
            amount=amount,
            transaction_type=transaction_type,
            status='completed',
            transaction_date=timezone.now(),
        )

        # ✅ FIX: Buy பண்ணா BuyerListing-ல் உள்ள அனைத்து same-name entries delete
        if transaction_type == 'buy':
            BuyerListing.objects.filter(
                house_name__iexact=property_name
            ).delete()

        # ✅ FIX: Rent பண்ணா TenantListing-ல் உள்ள அனைத்து same-name entries delete
        elif transaction_type == 'rent':
            TenantListing.objects.filter(
                house_name__iexact=property_name
            ).delete()

        return JsonResponse({'success': True})

    return JsonResponse({'error': 'Invalid method'}, status=400)


# ============================================================
# ✅ புதிய view: DB-ல் உள்ள existing duplicates ஒரே நேரத்தில் clean பண்ண
#    URL: /clean-duplicates/  (ஒரு முறை மட்டும் run பண்ணுங்க!)
# ============================================================
def clean_duplicate_listings(request):
    if not request.session.get('is_admin'):
        return redirect("property:login")

    # BuyerListing duplicates — house_name + location same ஆனா latest மட்டும் வையுங்க
    seen_buyer = set()
    buyer_deleted = 0
    for listing in BuyerListing.objects.order_by('id'):
        key = (listing.house_name.strip().lower(), listing.location.strip().lower())
        if key in seen_buyer:
            listing.delete()
            buyer_deleted += 1
        else:
            seen_buyer.add(key)

    # TenantListing duplicates — house_name + location same ஆனா latest மட்டும் வையுங்க
    seen_tenant = set()
    tenant_deleted = 0
    for listing in TenantListing.objects.order_by('id'):
        key = (listing.house_name.strip().lower(), listing.location.strip().lower())
        if key in seen_tenant:
            listing.delete()
            tenant_deleted += 1
        else:
            seen_tenant.add(key)

    return HttpResponse(
        f"✅ Cleanup complete!<br>"
        f"BuyerListing duplicates deleted: <b>{buyer_deleted}</b><br>"
        f"TenantListing duplicates deleted: <b>{tenant_deleted}</b>"
    )


def buyer_posts_list(request):
    if not request.session.get('is_admin'):
        return redirect("property:login")
    listings = BuyerListing.objects.all().order_by('-created_at')
    return render(request, 'buyer_posts_list.html', {'listings': listings})


def tenant_posts_list(request):
    if not request.session.get('is_admin'):
        return redirect("property:login")
    listings = TenantListing.objects.all().order_by('-created_at')
    return render(request, 'tenant_posts_list.html', {'listings': listings})