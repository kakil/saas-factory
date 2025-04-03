from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.features.users.schemas import Token, Login, UserRegistration, User
from app.features.users.service import UserService, get_user_service
from app.features.teams.service import OrganizationService, get_organization_service
from app.features.teams.schemas import OrganizationCreate

router = APIRouter()


@router.post("/token", response_model=Token)
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(),
        user_service: UserService = Depends(get_user_service),
):
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    login_data = Login(email=form_data.username, password=form_data.password)
    return user_service.login(login_data=login_data)


@router.post("/login", response_model=Token)
async def login(
        login_data: Login,
        user_service: UserService = Depends(get_user_service),
):
    """
    Login user and get access token
    """
    return user_service.login(login_data=login_data)


@router.post("/register", response_model=User)
async def register(
        registration_data: UserRegistration,
        user_service: UserService = Depends(get_user_service),
        organization_service: OrganizationService = Depends(get_organization_service),
):
    """
    Register a new user with optional organization
    """
    # Handle organization creation if name is provided
    if registration_data.organization_name:
        # Create organization
        org_data = OrganizationCreate(
            name=registration_data.organization_name,
            plan_id="free"  # Default plan
        )
        organization = organization_service.create_organization(organization_in=org_data)

        # Create user with organization
        user_create_data = registration_data.model_copy(exclude={"organization_name"})
        user = user_service.create_user_with_organization(
            user_in=user_create_data, organization_id=organization.id
        )
    else:
        # Create user without organization
        user_create_data = registration_data.model_copy(exclude={"organization_name"})
        user = user_service.create_user(user_in=user_create_data)

    return user