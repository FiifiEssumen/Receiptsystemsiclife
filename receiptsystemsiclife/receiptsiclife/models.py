

from django.db import models

from django.db import models
from django.core.mail import EmailMessage
from django.conf import settings
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from io import BytesIO
import os
from datetime import datetime

class Student(models.Model):
    PROGRAM_CHOICES = [
        ('computer_science', 'Computer Science'),
        ('business_admin', 'Business Administration'),
        ('engineering', 'Engineering'),
        ('medicine', 'Medicine'),
        ('law', 'Law'),
        ('education', 'Education'),
    ]
    
    student_name = models.CharField(max_length=200)
    dob = models.DateField(verbose_name="Date of Birth")
    program = models.CharField(max_length=50, choices=PROGRAM_CHOICES)
    email = models.EmailField()
    parents_name = models.CharField(max_length=200)
    parents_contact = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.student_name} - {self.program}"
    
    class Meta:
        verbose_name = "Student"
        verbose_name_plural = "Students"

class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('mobile_money', 'Mobile Money'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    description = models.TextField(blank=True, null=True)
    receipt_number = models.CharField(max_length=50, unique=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.receipt_number:
            # Generate unique receipt number
            self.receipt_number = f"REC-{datetime.now().strftime('%Y%m%d')}-{self.id or '000'}"
        
        # If payment status changes to completed, generate and send receipt
        if self.status == 'completed' and self.pk:
            old_status = Payment.objects.get(pk=self.pk).status if self.pk else None
            if old_status != 'completed':
                super().save(*args, **kwargs)
                self.generate_and_send_receipt()
                return
        
        super().save(*args, **kwargs)
    
    def generate_pdf_receipt(self):
        """Generate PDF receipt"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)
        
        # Container for PDF elements
        elements = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1,  # Center alignment
            textColor=colors.HexColor('#2E86AB')
        )
        
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.HexColor('#A23B72')
        )
        
        # Title
        title = Paragraph("RECEIPTSICLIFE", title_style)
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        # Receipt header
        receipt_header = Paragraph("PAYMENT RECEIPT", header_style)
        elements.append(receipt_header)
        elements.append(Spacer(1, 20))
        
        # Receipt details table
        receipt_data = [
            ['Receipt Number:', self.receipt_number],
            ['Date:', self.payment_date.strftime('%B %d, %Y')],
            ['Time:', self.payment_date.strftime('%I:%M %p')],
        ]
        
        receipt_table = Table(receipt_data, colWidths=[2*inch, 3*inch])
        receipt_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(receipt_table)
        elements.append(Spacer(1, 20))
        
        # Student information
        student_header = Paragraph("Student Information", header_style)
        elements.append(student_header)
        
        student_data = [
            ['Student Name:', self.student.student_name],
            ['Date of Birth:', self.student.dob.strftime('%B %d, %Y')],
            ['Program:', self.student.get_program_display()],
            ['Email:', self.student.email],
            ['Parent/Guardian:', self.student.parents_name],
            ['Parent Contact:', self.student.parents_contact],
        ]
        
        student_table = Table(student_data, colWidths=[2*inch, 3*inch])
        student_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(student_table)
        elements.append(Spacer(1, 20))
        
        # Payment information
        payment_header = Paragraph("Payment Details", header_style)
        elements.append(payment_header)
        
        payment_data = [
            ['Amount Paid:', f"${self.amount:.2f}"],
            ['Payment Method:', self.get_payment_method_display()],
            ['Status:', self.get_status_display()],
            ['Description:', self.description or 'N/A'],
        ]
        
        payment_table = Table(payment_data, colWidths=[2*inch, 3*inch])
        payment_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F8F9FA')),
        ]))
        
        elements.append(payment_table)
        elements.append(Spacer(1, 30))
        
        # Footer
        footer_text = """
        <para align=center>
        <font size=8>
        Thank you for your payment!<br/>
        For any inquiries, please contact us at receiptsiclife@example.com<br/>
        This is an automatically generated receipt.
        </font>
        </para>
        """
        footer = Paragraph(footer_text, styles['Normal'])
        elements.append(footer)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    def generate_and_send_receipt(self):
        """Generate PDF and send via email"""
        try:
            # Generate PDF
            pdf_buffer = self.generate_pdf_receipt()
            
            # Prepare email
            subject = f"Payment Receipt - {self.receipt_number}"
            message = f"""
            Dear {self.student.student_name},
            
            Thank you for your payment of ${self.amount:.2f} for the {self.student.get_program_display()} program.
            
            Please find your receipt attached to this email.
            
            Payment Details:
            - Receipt Number: {self.receipt_number}
            - Amount: ${self.amount:.2f}
            - Payment Date: {self.payment_date.strftime('%B %d, %Y')}
            - Payment Method: {self.get_payment_method_display()}
            
            If you have any questions, please don't hesitate to contact us.
            
            Best regards,
            ReceiptSicLife Team
            """
            
            # Create email
            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[self.student.email],
            )
            
            # Attach PDF
            email.attach(
                f"receipt_{self.receipt_number}.pdf",
                pdf_buffer.getvalue(),
                'application/pdf'
            )
            
            # Send email
            email.send()
            
            print(f"Receipt sent successfully to {self.student.email}")
            
        except Exception as e:
            print(f"Error sending receipt: {str(e)}")
    
    def __str__(self):
        return f"{self.student.student_name} - ${self.amount} ({self.status})"
    
    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        ordering = ['-payment_date']