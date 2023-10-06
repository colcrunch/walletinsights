# Define views here!
from django.contrib.auth.decorators import login_required, permission_required


@login_required()
@permission_required("walletinsights.access_walletinsights")
def dashboard(request):
    pass
