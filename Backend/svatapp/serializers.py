from rest_framework import serializers
from django.core.files.uploadedfile import UploadedFile
from .models import Vulnerability
import logging

logger = logging.getLogger(__name__)

class VulnerabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Vulnerability
        fields = [
            'vulnerability_name', 'cve_id', 'cwe_id', 'description',
            'type', 'severity', 'risk', 'recommended_fix', 'cve_url', 'cwe_url'
        ]

class ProcessSerializer(serializers.Serializer):
    files = serializers.ListField(child=serializers.FileField(), required=False)
    message = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    chunk_size = serializers.IntegerField(default=600, required=False)
    chunk_overlap = serializers.IntegerField(default=40, required=False)
    llm_temperature = serializers.FloatField(default=0.7, required=False)
    max_tokens = serializers.IntegerField(default=1024, required=False)
    top_k = serializers.IntegerField(default=3, required=False)
    model_name = serializers.CharField(max_length=50, default='llama3.1:8b', required=False)

    def validate(self, data):
        try:
            if data.get('message'):
                data['message'].encode('utf-8').decode('utf-8')
                logger.debug(f"Validated UTF-8 for message: {data['message'][:50]}...")
        except UnicodeDecodeError as e:
            logger.error(f"Invalid UTF-8 in message field: {str(e)}")
            raise serializers.ValidationError({"message": f"Invalid UTF-8 encoding in message: {str(e)}"})
        if data.get('files'):
            for file in data['files']:
                if file.name.lower().endswith(('.txt', '.py', '.js', '.java', '.c', '.cpp')):
                    try:
                        file.seek(0)
                        sample = file.read(1024).decode('utf-8')
                        file.seek(0)
                        logger.debug(f"Validated UTF-8 for file: {file.name}")
                    except UnicodeDecodeError as e:
                        logger.error(f"Invalid UTF-8 in file {file.name}: {str(e)}")
                        raise serializers.ValidationError({"files": f"Invalid UTF-8 encoding in file {file.name}: {str(e)}"})
        return data

class CodeAnalysisSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=100000, required=False, allow_blank=True)
    code_file = serializers.FileField(required=False)
    model_name = serializers.CharField(max_length=50, default='llama3.1:8b', required=False)
    temperature = serializers.FloatField(default=0.7, required=False)

    def validate(self, data):
        code = data.get('code')
        code_file = data.get('code_file')

        if not code and not code_file:
            raise serializers.ValidationError({"non_field_errors": "Either code or code_file must be provided."})

        if code:
            try:
                code.encode('utf-8').decode('utf-8')
                logger.debug(f"Validated UTF-8 for code: {code[:50]}...")
            except UnicodeDecodeError as e:
                logger.error(f"Invalid UTF-8 in code field: {str(e)}")
                raise serializers.ValidationError({"code": f"Invalid UTF-8 encoding in code: {str(e)}"})

        if code_file:
            try:
                code_file.seek(0)
                sample = code_file.read(1024).decode('utf-8')
                code_file.seek(0)
                logger.debug(f"Validated UTF-8 for code_file: {code_file.name}")
            except UnicodeDecodeError as e:
                logger.error(f"Invalid UTF-8 in code_file {code_file.name}: {str(e)}")
                raise serializers.ValidationError({"code_file": f"Invalid UTF-8 encoding in file {code_file.name}: {str(e)}"})

        return data

class NewsSerializer(serializers.Serializer):
    title = serializers.CharField()
    link = serializers.URLField()
    published = serializers.CharField()