import os
import zipfile
import tempfile
from io import BytesIO
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile

from apps.users.decorators import api_token_required
from apps.signing.services import sign_pdf_service, get_pdf_page_size
from .models import Document, SignatureProfile, SignatureBatch

@csrf_exempt
@api_token_required
def api_sign_individual(request):
    """
    Endpoint para firma individual de un documento PDF.
    Acepta: pdf_file (archivo), p12_file (archivo), password (texto),
           y ya sea profile_id (int) o las coordenadas individuales:
           page (int), x (float), y (float), width (float), height (float).
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido. Use POST.'}, status=405)
    
    # 1. Validar archivos requeridos
    if 'pdf_file' not in request.FILES:
        return JsonResponse({'error': 'Falta el archivo "pdf_file"'}, status=400)
    if 'p12_file' not in request.FILES:
        return JsonResponse({'error': 'Falta el archivo de firma "p12_file"'}, status=400)
    
    password = request.POST.get('password')
    if not password:
        return JsonResponse({'error': 'Falta la contraseña del certificado ("password")'}, status=400)
    
    tsa_url = request.POST.get('tsa_url')
    if not tsa_url:
        tsa_url = None
        
    tsa_username = request.POST.get('tsa_username')
    tsa_password = request.POST.get('tsa_password')
    if tsa_username:
        tsa_username = tsa_username.strip()
    if tsa_password:
        tsa_password = tsa_password.strip()
    if not tsa_username or not tsa_password:
        tsa_username = None
        tsa_password = None
        
    # 2. Obtener parámetros de posición (Perfil o Coordenadas)
    profile_id = request.POST.get('profile_id')
    if profile_id:
        try:
            profile = SignatureProfile.objects.get(id=profile_id, user=request.user)
            page = profile.page
            x = profile.x
            y = profile.y
            width = profile.width
            height = profile.height
        except SignatureProfile.DoesNotExist:
            return JsonResponse({'error': f'El perfil de firma con ID {profile_id} no existe para este usuario.'}, status=400)
    else:
        # Coordenadas manuales
        try:
            page = int(request.POST.get('page', 1))
            x_val = request.POST.get('x')
            y_val = request.POST.get('y')
            
            if x_val is None or y_val is None:
                return JsonResponse({'error': 'Debe proporcionar las coordenadas ("x" e "y") o un "profile_id".'}, status=400)
                
            x = float(x_val)
            y = float(y_val)
            width = float(request.POST.get('width', 200))
            height = float(request.POST.get('height', 50))
        except ValueError:
            return JsonResponse({'error': 'Los parámetros x, y, width, height, page deben ser numéricos.'}, status=400)

    # 3. Guardar documento original para trazabilidad
    pdf_file = request.FILES['pdf_file']
    p12_file = request.FILES['p12_file']
    p12_content = p12_file.read()
    
    document = Document(
        user=request.user,
        original_file=pdf_file,
        status='uploaded',
        source='api'
    )
    document.save()
    
    # 4. Procesar Firma
    try:
        input_pdf_path = document.original_file.path
        signed_pdf_path = sign_pdf_service(
            input_pdf_path, p12_content, password, page, x, y, width, height,
            tsa_url=tsa_url, tsa_username=tsa_username, tsa_password=tsa_password
        )
        
        # Guardar archivo firmado en el modelo
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
        
        # Limpiar temporal
        if os.path.exists(signed_pdf_path):
            os.remove(signed_pdf_path)
            
    except Exception as e:
        # Eliminar registro e informar error
        document.delete()
        return JsonResponse({'error': f'Error en el proceso de firma: {str(e)}'}, status=500)
        
    # 5. Retornar Respuesta (Binario por defecto, o JSON si se solicita)
    return_binary = request.POST.get('return_binary', 'true').lower() == 'true'
    
    if return_binary:
        with open(document.signed_file.path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/pdf')
            file_name = os.path.basename(document.original_file.name)
            response['Content-Disposition'] = f'attachment; filename="signed_{file_name}"'
            return response
    else:
        return JsonResponse({
            'status': 'success',
            'document': {
                'id': document.id,
                'original_name': os.path.basename(document.original_file.name),
                'signed_name': os.path.basename(document.signed_file.name),
                'status': document.status,
                'source': document.source,
                'created_at': document.created_at.isoformat(),
                'signed_at': document.signed_at.isoformat(),
                'download_url': request.build_absolute_uri(
                    reverse('api_document_download', args=[document.id])
                )
            }
        })

@csrf_exempt
@api_token_required
def api_sign_batch(request):
    """
    Endpoint para firma masiva de múltiples PDFs.
    Acepta: documents (múltiples archivos), p12_file (archivo), password (texto),
           y ya sea profile_id (int) o las coordenadas individuales.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido. Use POST.'}, status=405)
        
    documents = request.FILES.getlist('documents')
    if not documents:
        return JsonResponse({'error': 'Debe subir uno o más archivos en el parámetro "documents".'}, status=400)
    
    if len(documents) > 100:
        return JsonResponse({'error': 'El número máximo de documentos permitido por lote es 100.'}, status=400)
        
    if 'p12_file' not in request.FILES:
        return JsonResponse({'error': 'Falta el archivo de firma "p12_file"'}, status=400)
        
    password = request.POST.get('password')
    if not password:
        return JsonResponse({'error': 'Falta la contraseña del certificado ("password")'}, status=400)
        
    tsa_url = request.POST.get('tsa_url')
    if not tsa_url:
        tsa_url = None
        
    tsa_username = request.POST.get('tsa_username')
    tsa_password = request.POST.get('tsa_password')
    if tsa_username:
        tsa_username = tsa_username.strip()
    if tsa_password:
        tsa_password = tsa_password.strip()
    if not tsa_username or not tsa_password:
        tsa_username = None
        tsa_password = None
        
    # Obtener parámetros de posición (Perfil o Coordenadas)
    profile = None
    profile_id = request.POST.get('profile_id')
    if profile_id:
        try:
            profile = SignatureProfile.objects.get(id=profile_id, user=request.user)
            page = profile.page
            x = profile.x
            y = profile.y
            width = profile.width
            height = profile.height
        except SignatureProfile.DoesNotExist:
            return JsonResponse({'error': f'El perfil de firma con ID {profile_id} no existe para este usuario.'}, status=400)
    else:
        try:
            page = int(request.POST.get('page', 1))
            x_val = request.POST.get('x')
            y_val = request.POST.get('y')
            
            if x_val is None or y_val is None:
                return JsonResponse({'error': 'Debe proporcionar las coordenadas ("x" e "y") o un "profile_id".'}, status=400)
                
            x = float(x_val)
            y = float(y_val)
            width = float(request.POST.get('width', 200))
            height = float(request.POST.get('height', 50))
        except ValueError:
            return JsonResponse({'error': 'Los parámetros x, y, width, height, page deben ser numéricos.'}, status=400)
            
    p12_file = request.FILES['p12_file']
    p12_content = p12_file.read()
    
    # Validar dimensiones de los documentos (compatibilidad)
    reference_size = None
    for doc_file in documents:
        if not doc_file.name.lower().endswith('.pdf'):
            return JsonResponse({'error': f'El archivo {doc_file.name} no es un PDF válido.'}, status=400)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf:
            for chunk in doc_file.chunks():
                tmp_pdf.write(chunk)
            tmp_pdf_path = tmp_pdf.name
        
        try:
            size = get_pdf_page_size(tmp_pdf_path, page)
            if reference_size is None:
                reference_size = size
            else:
                if abs(size[0] - reference_size[0]) > 10 or abs(size[1] - reference_size[1]) > 10:
                    return JsonResponse({
                        'error': f'Las dimensiones de los documentos no coinciden. {doc_file.name} ({size}) vs Referencia ({reference_size})'
                    }, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Error al leer dimensiones de {doc_file.name}: {str(e)}'}, status=400)
        finally:
            if os.path.exists(tmp_pdf_path):
                os.remove(tmp_pdf_path)

    # Registrar el lote en SignatureBatch
    batch_log = SignatureBatch.objects.create(
        user=request.user,
        source='api',
        document_count=len(documents),
        signature_profile=profile
    )

    return_binary = request.POST.get('return_binary', 'true').lower() == 'true'
    
    if return_binary:
        # Generar archivo ZIP en memoria y retornar
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for doc_file in documents:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf:
                    for chunk in doc_file.chunks():
                        tmp_pdf.write(chunk)
                    tmp_pdf_path = tmp_pdf.name
                
                try:
                    signed_pdf_path = sign_pdf_service(
                        tmp_pdf_path, p12_content, password, page, x, y, width, height,
                        tsa_url=tsa_url, tsa_username=tsa_username, tsa_password=tsa_password
                    )
                    
                    signed_name = f"signed_{doc_file.name}"
                    with open(signed_pdf_path, 'rb') as f:
                        zip_file.writestr(signed_name, f.read())
                    
                    os.remove(signed_pdf_path)
                except Exception as e:
                    return JsonResponse({'error': f'Error al firmar {doc_file.name}: {str(e)}'}, status=500)
                finally:
                    if os.path.exists(tmp_pdf_path):
                        os.remove(tmp_pdf_path)
                        
        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="documentos_firmados.zip"'
        return response
    else:
        # Guardar cada documento individual en la base de datos y retornar JSON
        signed_docs_json = []
        for doc_file in documents:
            # Creamos el registro del documento original
            document = Document(
                user=request.user,
                original_file=doc_file,
                status='uploaded',
                source='api'
            )
            document.save()
            
            try:
                input_pdf_path = document.original_file.path
                signed_pdf_path = sign_pdf_service(
                    input_pdf_path, p12_content, password, page, x, y, width, height,
                    tsa_url=tsa_url, tsa_username=tsa_username, tsa_password=tsa_password
                )
                
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
                
                if os.path.exists(signed_pdf_path):
                    os.remove(signed_pdf_path)
                
                signed_docs_json.append({
                    'id': document.id,
                    'original_name': os.path.basename(document.original_file.name),
                    'signed_name': os.path.basename(document.signed_file.name),
                    'download_url': request.build_absolute_uri(
                        reverse('api_document_download', args=[document.id])
                    )
                })
            except Exception as e:
                document.delete()
                return JsonResponse({
                    'error': f'Error al firmar {doc_file.name} en guardado por DB: {str(e)}'
                }, status=500)
                
        return JsonResponse({
            'status': 'success',
            'batch_id': batch_log.id,
            'total_signed': len(documents),
            'signed_documents': signed_docs_json
        })

@csrf_exempt
@api_token_required
def api_document_download(request, pk):
    """
    Endpoint seguro para descargar archivos firmados mediante API.
    """
    try:
        document = Document.objects.get(pk=pk, user=request.user)
        if not document.signed_file:
            return JsonResponse({'error': 'El documento no ha sido firmado todavía.'}, status=400)
            
        with open(document.signed_file.path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/pdf')
            file_name = os.path.basename(document.signed_file.name)
            response['Content-Disposition'] = f'attachment; filename="{file_name}"'
            return response
            
    except Document.DoesNotExist:
        return JsonResponse({'error': 'Documento no encontrado o no pertenece a su usuario.'}, status=404)

@csrf_exempt
@api_token_required
def api_profiles_list(request):
    """
    Lista los perfiles de firma del usuario en formato JSON.
    """
    profiles = SignatureProfile.objects.filter(user=request.user).order_by('-created_at')
    data = []
    for p in profiles:
        data.append({
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'page': p.page,
            'x': p.x,
            'y': p.y,
            'width': p.width,
            'height': p.height,
            'created_at': p.created_at.isoformat()
        })
    return JsonResponse({'status': 'success', 'profiles': data})
