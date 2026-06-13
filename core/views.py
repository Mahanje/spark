from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.contenttypes.models import ContentType
from .models import Report

@require_POST
def submit_report(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Please Login First.'}, status=403)

    model_name = request.POST.get('model')
    object_id = request.POST.get('id')
    reason = request.POST.get('reason')
    description = request.POST.get('description', '')

    try:
        content_type = ContentType.objects.get(model=model_name)

        # جلوگیری از گزارش تکراری
        if Report.objects.filter(
                user=request.user,
                content_type=content_type,
                object_id=object_id
        ).exists():
            return JsonResponse({'status': 'error', 'message': 'You Already Reported.'}, status=400)

        Report.objects.create(
            user=request.user,
            content_type=content_type,
            object_id=object_id,
            reason=reason,
            description=description
        )

        return JsonResponse({
            'status': 'success',
            'message': 'Your Report Has Been Uploaded And Soon Will Be Reviewed.'
        })

    except Exception:
        return JsonResponse({'status': 'error', 'message': 'There Seems To Be A problem While Reporting.'}, status=400)




