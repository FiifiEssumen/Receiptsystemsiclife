from django.shortcuts import render

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.generic import ListView
from .models import Student, Payment
from .forms import StudentForm, PaymentForm

def home(request):
    """Home page view"""
    recent_payments = Payment.objects.filter(status='completed')[:5]
    total_students = Student.objects.count()
    total_payments = Payment.objects.filter(status='completed').count()
    
    context = {
        'recent_payments': recent_payments,
        'total_students': total_students,
        'total_payments': total_payments,
    }
    return render(request, 'receiptsiclife/home.html', context)

def student_create(request):
    """Create new student"""
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            student = form.save()
            messages.success(request, f'Student {student.student_name} created successfully!')
            return redirect('student_list')
    else:
        form = StudentForm()
    
    return render(request, 'receiptsiclife/student_form.html', {'form': form, 'title': 'Add New Student'})

def student_list(request):
    """List all students"""
    students = Student.objects.all().order_by('-created_at')
    return render(request, 'receiptsiclife/student_list.html', {'students': students})

def student_detail(request, pk):
    """Student detail view"""
    student = get_object_or_404(Student, pk=pk)
    payments = student.payments.all().order_by('-payment_date')
    return render(request, 'receiptsiclife/student_detail.html', {
        'student': student,
        'payments': payments
    })

def payment_create(request):
    """Create new payment"""
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.status = 'completed'  # Auto-complete payment
            payment.save()
            messages.success(request, f'Payment of ${payment.amount} recorded successfully!')
            return redirect('payment_list')
    else:
        form = PaymentForm()
    
    return render(request, 'receiptsiclife/payment_form.html', {'form': form, 'title': 'Record New Payment'})

def payment_list(request):
    """List all payments"""
    payments = Payment.objects.all().order_by('-payment_date')
    return render(request, 'receiptsiclife/payment_list.html', {'payments': payments})

def payment_detail(request, pk):
    """Payment detail view"""
    payment = get_object_or_404(Payment, pk=pk)
    return render(request, 'receiptsiclife/payment_detail.html', {'payment': payment})

def download_receipt(request, pk):
    """Download PDF receipt"""
    payment = get_object_or_404(Payment, pk=pk)
    
    if payment.status != 'completed':
        messages.error(request, 'Receipt can only be generated for completed payments.')
        return redirect('payment_detail', pk=pk)
    
    # Generate PDF
    pdf_buffer = payment.generate_pdf_receipt()
    
    # Return PDF response
    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="receipt_{payment.receipt_number}.pdf"'
    
    return response
