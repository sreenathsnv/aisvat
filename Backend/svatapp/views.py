from django.shortcuts import render
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_404_NOT_FOUND,
    HTTP_400_BAD_REQUEST,
    HTTP_201_CREATED,
    HTTP_403_FORBIDDEN,
    HTTP_205_RESET_CONTENT
)
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .serializers import ProcessSerializer, CodeAnalysisSerializer, NewsSerializer, VulnerabilitySerializer
from .models import Vulnerability, ProcessingResult, CustomUser
from .utils.file_processing import check_chromadb_connection, process_files, create_collection_name
from .utils.vulnerability_extraction import convert_vulnerabilities_to_documents, extract_structured_vulnerabilities, get_qa_chain, parse_vulnerability_from_pdf, extract_text_from_image
from .utils.code_analysis import analyze_code_with_llm, extract_ids_from_response, fetch_cve_details, fetch_cwe_details
from .utils.news_feed import fetch_all_news
from langchain_community.llms import Ollama
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from rest_framework.parsers import MultiPartParser, FormParser
from pathlib import Path
from django.conf import settings
import logging
import uuid
import time

logger = logging.getLogger(__name__)

@api_view(['GET'])
def test(request):
    return Response({'message': 'Successful'}, status=HTTP_200_OK)

def test_email(request):
    subject = 'Test MailHog HTML Email'
    from_email = None  # will use DEFAULT_FROM_EMAIL
    to = ['test@receiver.com']

    html_content = render_to_string('email/activation_email.html', {
        'user': request.user,
        'url': 'http://localhost:8000/auth/activate/sample-uid/sample-token/',
    })

    email = EmailMultiAlternatives(subject, '', from_email, to)
    email.attach_alternative(html_content, "text/html")
    email.send()

    return Response("Test email sent using MailHog.")

class ReportViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def create(self, request):
        if not check_chromadb_connection():
            return Response(
                {"error": "Could not connect to ChromaDB server. Please ensure it is running."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        serializer = ProcessSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        files = data.get('files', [])
        message = data.get('message', '')
        chunk_size = data.get('chunk_size', 600)
        chunk_overlap = data.get('chunk_overlap', 40)
        llm_temperature = data.get('llm_temperature', 0.7)
        max_tokens = data.get('max_tokens', 1024)
        top_k = data.get('top_k', 3)
        model_name = data.get('model_name', 'llama3.1:8b')

        if not files and not message:
            return Response({"error": "No files or message provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            llm = Ollama(model=model_name, temperature=llm_temperature, num_ctx=2048, num_predict=max_tokens)
        except Exception as e:
            return Response({"error": f"Failed to initialize LLM: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        collection_names = []
        qa_chains = {}
        vulnerabilities = []

        if files:
            try:
                collection_names, qa_chains, vulnerabilities = process_files(
                    files, llm, model_name, chunk_size, chunk_overlap, llm_temperature, max_tokens, top_k
                )
                vuln_serializer = VulnerabilitySerializer(vulnerabilities, many=True)
                response_data = {
                    "status": "Collections created",
                    "collections": collection_names,
                    "vulnerabilities": vuln_serializer.data,
                    "message": "Files processed. You can now ask questions via WebSocket."
                }

                for file in files:
                    # Generate unique collection name using timestamp and UUID
                    unique_id = f"{int(time.time())}-{str(uuid.uuid4())[:8]}"
                    collection_name = create_collection_name(file.name, unique_id)
                    result_url = f"http://localhost:4200/results/{collection_name}"
                    # Store the result in the database
                    ProcessingResult.objects.create(
                        user=request.user,
                        file_name=file.name,
                        collection_name=collection_name,
                        response_data=response_data,
                        result_url=result_url
                    )

                    user = CustomUser.objects.get(email=request.user.email)
                    print(f"/n/nThe user details {user.full_name,user.email}")
                    # Send email notification
                    try:
                        subject = f'File Processing Complete: {file.name}'
                        html_content = render_to_string('email/processing_complete.html', {
                            'user': user.full_name.capitalize(),
                            'file_name': file.name,
                            'result_url': result_url,
                        })
                        email = EmailMultiAlternatives(subject, '', settings.DEFAULT_FROM_EMAIL, [request.user.email])
                        email.attach_alternative(html_content, "text/html")
                        email.send()
                        logger.info(f"Sent email notification for file {file.name} to {request.user.email}")
                        
                    except Exception as e:
                        logger.error(f"Failed to send email for file {file.name}: {str(e)}")

                for vuln in vulnerabilities:
                    vuln['collection_name'] = create_collection_name(vuln.get('file_name', 'default'), unique_id)
                    Vulnerability.objects.get_or_create(**vuln)

                return Response(response_data, status=HTTP_201_CREATED)
            except ValueError as e:
                return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

class ResultView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, collection_name):
        try:
            result = ProcessingResult.objects.get(
                user=request.user,
                collection_name=collection_name
            )
            return Response(result.response_data, status=HTTP_200_OK)
        except ProcessingResult.DoesNotExist:
            return Response({"error": "Result not found"}, status=HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Error retrieving result: {str(e)}"}, status=HTTP_500_INTERNAL_SERVER_ERROR)

class CodeAnalysisViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def create(self, request):
        serializer = CodeAnalysisSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        code = data.get('code', '')
        code_file = data.get('code_file')
        model_name = data.get('model_name', 'llama3.1:8b')
        temperature = data.get('temperature', 0.7)

        valid_models = ["llama3:7b", "tinyllama", "llama3.1:8b", "phi", "mistral:latest", "qwen:7b", "gemma:2b", "neural-chat"]
        
        if model_name not in valid_models:
            return Response({"error": f"Invalid model name. Choose from {valid_models}"}, status=status.HTTP_400_BAD_REQUEST)

        if not code and not code_file:
            return Response({"error": "No code or code file provided"}, status=status.HTTP_400_BAD_REQUEST)

        if code_file:
            if Path(code_file.name).suffix.lower() not in settings.ALLOWED_EXTENSIONS:
                return Response({"error": f"Unsupported file type: {code_file.name}"}, status=status.HTTP_400_BAD_REQUEST)
            code = code_file.read().decode('utf-8')

        if not code.strip():
            return Response({"error": "Provided code or file is empty"}, status=status.HTTP_400_BAD_REQUEST)

        analysis = analyze_code_with_llm(code, model_name, temperature=temperature)
        cve_ids, cwe_ids = extract_ids_from_response(analysis)
        table_data = []

        for cve_id in cve_ids:
            details = fetch_cve_details(cve_id)
            cvss_score = details.get("cvss_score", "N/A")
            severity = "N/A" if cvss_score == "N/A" else ("High" if float(cvss_score) >= 7 else "Medium")
            table_data.append({
                "vulnerability_name": cve_id,
                "cve_id": cve_id,
                "cwe_id": "N/A",
                "description": details.get("description", "No description available"),
                "type": "Unknown",
                "severity": severity,
                "risk": "Unknown",
                "recommended_fix": "N/A",
                "cve_url": f"https://cve.mitre.org/cgi-bin/cvename.cgi?name={cve_id}",
                "cwe_url": "N/A"
            })

        for cwe_id in cwe_ids:
            details = fetch_cwe_details(cwe_id)
            cwe_number = cwe_id.replace("CWE-", "")
            table_data.append({
                "vulnerability_name": details.get("title", cwe_id),
                "cve_id": "N/A",
                "cwe_id": cwe_id,
                "description": details.get("description", "No description available"),
                "type": "Unknown",
                "severity": "Medium",
                "risk": "Unknown",
                "recommended_fix": "N/A",
                "cve_url": "N/A",
                "cwe_url": f"https://cwe.mitre.org/data/definitions/{cwe_number}.html"
            })

        # Generate unique collection name using timestamp and UUID
        file_name = code_file.name if code_file else "inline_code_analysis"
        unique_id = f"{int(time.time())}-{str(uuid.uuid4())[:8]}"
        collection_name = create_collection_name(file_name, unique_id)
        result_url = f"http://localhost:4200/results/{collection_name}"
        response_data = {
            "status": f"Analyzed code and found {len(cve_ids)} CVEs and {len(cwe_ids)} CWEs.",
            "vulnerabilities": table_data,
            "message": "Code analysis complete. You can view the results."
        }

        ProcessingResult.objects.create(
            user=request.user,
            file_name=file_name,
            collection_name=collection_name,
            response_data=response_data,
            result_url=result_url
        )

        # Send email notification
        try:
            subject = f'Code Analysis Complete: {file_name}'
            html_content = render_to_string('email/processing_complete.html', {
                'user': request.user,
                'file_name': file_name,
                'result_url': result_url,
            })
            email = EmailMultiAlternatives(subject, '', settings.DEFAULT_FROM_EMAIL, [request.user.email])
            email.attach_alternative(html_content, "text/html")
            email.send()
            logger.info(f"Sent email notification for code analysis {file_name} to {request.user.email}")
        except Exception as e:
            logger.error(f"Failed to send email for code analysis {file_name}: {str(e)}")

        return Response(response_data, status=HTTP_201_CREATED)

class NewsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            news_data = fetch_all_news()
            if not news_data or not isinstance(news_data, dict):
                return Response({"error": "No news available"}, status=status.HTTP_404_NOT_FOUND)

            formatted_news = {}
            for source, items in news_data.items():
                if not items or not isinstance(items, list):
                    continue
                formatted_news[source] = NewsSerializer(items, many=True).data

            return Response({"news": formatted_news})
        except Exception as e:
            return Response({"error": f"Error fetching news: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)