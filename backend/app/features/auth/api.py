from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm

from app.core.security.supabase import supabase_auth
from app.features.users.schemas import Token, Login, UserRegistration, User, RefreshToken
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
    return await login(login_data=login_data, user_service=user_service)


@router.post("/login", response_model=Token)
async def login(
        login_data: Login,
        user_service: UserService = Depends(get_user_service),
):
    """
    Login user and get access token
    """
    # Authenticate with Supabase
    try:
        auth_result = await supabase_auth.sign_in(
            email=login_data.email, 
            password=login_data.password
        )
        
        # Find or create user in our database
        db_user = user_service.get_by_email(email=login_data.email)
        
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found in application database",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Return token information from Supabase
        return Token(
            access_token=auth_result["access_token"],
            refresh_token=auth_result.get("refresh_token"),
            expires_in=auth_result.get("expires_in"),
            token_type="bearer"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_data: RefreshToken):
    """
    Refresh an access token using a refresh token
    """
    try:
        # Call Supabase to refresh the token
        refresh_result = await supabase_auth.refresh_token(refresh_data.refresh_token)
        
        # Return new token information
        return Token(
            access_token=refresh_result["access_token"],
            refresh_token=refresh_result.get("refresh_token"),
            expires_in=refresh_result.get("expires_in"),
            token_type="bearer"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Failed to refresh token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )


@router.post("/register", response_model=User)
async def register(
        registration_data: UserRegistration,
        background_tasks: BackgroundTasks,
        user_service: UserService = Depends(get_user_service),
        organization_service: OrganizationService = Depends(get_organization_service),
):
    """
    Register a new user with optional organization
    """
    # First register with Supabase
    try:
        # Add user metadata
        user_metadata = {
            "name": registration_data.name,
            "is_superuser": registration_data.is_superuser
        }
        
        if registration_data.organization_name:
            user_metadata["organization_name"] = registration_data.organization_name
            
        # Register with Supabase
        supabase_user = await supabase_auth.sign_up(
            email=registration_data.email,
            password=registration_data.password,
            user_metadata=user_metadata
        )
        
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
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {str(e)}"
        )