from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Document
from .forms import DocumentForm, SignDocumentForm
from apps.signing.services import sign_pdf_service
from django.core.files.base import ContentFile
import os

@login_required
def document_list(request):
    documents = Document.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'documents/document_list.html', {'documents': documents})

@login_required
def document_upload(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.user = request.user
            document.save()
            messages.success(request, 'Documento subido correctamente.')
            return redirect('document_list')
    else:
        form = DocumentForm()
    return render(request, 'documents/document_form.html', {'form': form})

@login_required
def document_sign(request, pk):
    document = get_object_or_404(Document, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = SignDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            p12_file = request.FILES['p12_file']
            password = form.cleaned_data['password']
            
            p12_content = p12_file.read()
            input_pdf_path = document.original_file.path
            
            try:
                page = form.cleaned_data['page']
                x = form.cleaned_data['x']
                y = form.cleaned_data['y']
                width = form.cleaned_data['width']
                height = form.cleaned_data['height']
                
                signed_pdf_path = sign_pdf_service(input_pdf_path, p12_content, password, page, x, y, width, height)
                
                with open(signed_pdf_path, 'rb') as f:
                    file_name = os.path.basename(document.original_file.name)
                    signed_name = f"signed_{file_name}"
                    document.signed_file.save(signed_name, ContentFile(f.read()), save=False)
                
                document.status = 'signed'
                document.signed_at = timezone.now()
                document.signature_page = page
                document.signature_x = x
                document.signature_y = y
                document.signature_width = width
                document.signature_height = height
                document.save()
                
                # Cleanup temp file
                if os.path.exists(signed_pdf_path):
                    os.remove(signed_pdf_path)
                    
                messages.success(request, 'Documento firmado exitosamente.')
                return redirect('document_list')
            except Exception as e:
                messages.error(request, f'Error al firmar: {str(e)}')
    else:
        form = SignDocumentForm()
        
    return render(request, 'documents/document_sign.html', {'form': form, 'document': document})
