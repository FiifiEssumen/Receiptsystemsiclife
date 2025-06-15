from django.contrib import admin

# from django.contrib import admin
from .models import Student, Payment

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'program', 'email', 'parents_name', 'created_at']
    list_filter = ['program', 'created_at']
    search_fields = ['student_name', 'email', 'parents_name']
    date_hierarchy = 'created_at'

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['receipt_number', 'student', 'amount', 'payment_method', 'status', 'payment_date']
    list_filter = ['status', 'payment_method', 'payment_date']
    search_fields = ['receipt_number', 'student__student_name']
    date_hierarchy = 'payment_date'
    readonly_fields = ['receipt_number', 'payment_date']
