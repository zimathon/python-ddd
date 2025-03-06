from rest_framework_nested import routers
from django.urls import path, include
from .views import AccountViewSet, ActivityViewSet

router = routers.DefaultRouter()
router.register(r'accounts', AccountViewSet)

accounts_router = routers.NestedDefaultRouter(router, r'accounts', lookup='account')
accounts_router.register(r'activities', ActivityViewSet, basename='account-activities')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(accounts_router.urls)),
] 