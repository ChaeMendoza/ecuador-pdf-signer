from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
from .models import Document
from .forms import DocumentForm, SignDocumentForm, BatchSignForm
from apps.signing.services import sign_pdf_service, get_pdf_page_size
from django.core.files.base import ContentFile
import os
import zipfile
import tempfile
from io import BytesIO

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

@login_required
def batch_sign(request):
    if request.method == 'POST':
        form = BatchSignForm(request.POST, request.FILES)
        if form.is_valid():
            documents = request.FILES.getlist('documents')
            p12_file = request.FILES['p12_file']
            password = form.cleaned_data['password']
            page = form.cleaned_data['page']
            x = form.cleaned_data['x']
            y = form.cleaned_data['y']
            width = form.cleaned_data['width']
            height = form.cleaned_data['height']
            
            if len(documents) > 100:
                messages.error(request, 'No se pueden procesar más de 100 documentos a la vez.')
                return redirect('batch_sign')
            
            p12_content = p12_file.read()
            
            # Validar dimensiones de los documentos
            reference_size = None
            for doc_file in documents:
                if not doc_file.name.lower().endswith('.pdf'):
                    continue
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf:
                    for chunk in doc_file.chunks():
                        tmp_pdf.write(chunk)
                    tmp_pdf_path = tmp_pdf.name
                
                try:
                    size = get_pdf_page_size(tmp_pdf_path, page)
                    if reference_size is None:
                        reference_size = size
                    else:
                        # Permitir variación de 10 puntos
                        if abs(size[0] - reference_size[0]) > 10 or abs(size[1] - reference_size[1]) > 10:
                            messages.error(request, f'Los documentos tienen dimensiones diferentes. {doc_file.name} tiene {size}, referencia {reference_size}.')
                            return redirect('batch_sign')
                finally:
                    if os.path.exists(tmp_pdf_path):
                        os.remove(tmp_pdf_path)
            
            # Crear ZIP en memoria
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for doc_file in documents:
                    if not doc_file.name.lower().endswith('.pdf'):
                        continue  # Solo PDFs
                    
                    # Guardar temporalmente el PDF
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf:
                        for chunk in doc_file.chunks():
                            tmp_pdf.write(chunk)
                        tmp_pdf_path = tmp_pdf.name
                    
                    try:
                        # Firmar
                        signed_pdf_path = sign_pdf_service(tmp_pdf_path, p12_content, password, page, x, y, width, height)
                        
                        # Agregar al ZIP
                        signed_name = f"signed_{doc_file.name}"
                        with open(signed_pdf_path, 'rb') as f:
                            zip_file.writestr(signed_name, f.read())
                        
                        # Limpiar
                        os.remove(signed_pdf_path)
                    except Exception as e:
                        messages.error(request, f'Error al firmar {doc_file.name}: {str(e)}')
                        return redirect('batch_sign')
                    finally:
                        if os.path.exists(tmp_pdf_path):
                            os.remove(tmp_pdf_path)
            
            zip_buffer.seek(0)
            response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename="documentos_firmados.zip"'
            messages.success(request, f'{len(documents)} documentos firmados exitosamente.')
            return response
    else:
        form = BatchSignForm()
    
    return render(request, 'documents/batch_sign.html', {'form': form})
