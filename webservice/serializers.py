from rest_framework import serializers
from webservice.models import Job, Execution
from core.mister_hadoop import MisterHadoop
import uuid


def generate_uuid():
    return "%s" % (uuid.uuid4())

mister_hadoop = MisterHadoop()


class JobSerializer(serializers.Serializer):
    id = serializers.IntegerField(label='ID', read_only=True)
    name = serializers.CharField(max_length=100, allow_blank=False, default='')
    status = serializers.CharField(max_length=100, allow_blank=False, default='')
    command = serializers.CharField(allow_blank=True, default='')
    callback_url = serializers.CharField(allow_blank=True, default='')
    user = serializers.CharField(max_length=100, allow_blank=False, default='')
    history = serializers.SerializerMethodField('get_execution_history')

    def get_execution_history(self, job):
        related_executions = Execution.objects.filter(job_id=job.id)
        job_history = mister_hadoop.get_running_jobs()
        result = []
        for execution in related_executions:
            print("job_history = %s" % (job_history))
            print("execution = %s" % (execution))
            hadoop_job_details = filter(lambda x: str(x[u"id"]) == str(execution.application_hadoop_id), job_history)
            print("hadoop_job_details = %s" % (hadoop_job_details))
            if hadoop_job_details:
                hadoop_job_detail = hadoop_job_details[0]
                result += [{
                    "id": execution.id,
                    "application_hadoop_id": execution.application_hadoop_id,
                    "progress": hadoop_job_detail["progress"],
                    "state": hadoop_job_detail["state"],
                    "finalStatus": hadoop_job_detail["finalStatus"]
                }]
        return result

    def create(self, validated_data):
        """
        Create and return a new `Job` instance, given the validated data.
        """
        return Job.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Update and return an existing `Job` instance, given the validated data.
        """
        instance.name = validated_data.get('name', instance.name)
        instance.status = validated_data.get('status', instance.status)
        instance.parameters = validated_data.get('parameters', instance.status)
        instance.callback_url = validated_data.get('callback_url', instance.callback_url)
        instance.user = validated_data.get('user', instance.user)

        if instance.file_id:
            instance.save()
        return instance
