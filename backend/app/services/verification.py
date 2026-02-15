from typing import Dict, Any, Optional
from app.core.config import settings


async def verify_email_service(email: str) -> Dict[str, Any]:
    """
    Verify email using Hunter.io API (or mock if no API key)
    """
    if not settings.HUNTER_KEY:
        # Mock verification for development
        return mock_email_verification(email)
    
    try:
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.hunter.io/v2/email-verifier",
                params={"email": email, "api_key": settings.HUNTER_KEY}
            )
            
            if response.status_code == 200:
                data = response.json().get("data", {})
                return {
                    "status": data.get("result", "unknown"),
                    "score": data.get("score", 0),
                    "regexp": data.get("regexp", False),
                    "gibberish": data.get("gibberish", False),
                    "disposable": data.get("disposable", False),
                    "webmail": data.get("webmail", False),
                    "mx_records": data.get("mx_records", False),
                    "smtp_server": data.get("smtp_server", False),
                    "smtp_check": data.get("smtp_check", False),
                    "accept_all": data.get("accept_all", False),
                    "source": "hunter.io"
                }
            else:
                return mock_email_verification(email)
                
    except Exception as e:
        return mock_email_verification(email)


def mock_email_verification(email: str) -> Dict[str, Any]:
    """
    Mock email verification for development/testing
    """
    # Basic email format check
    import re
    
    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
        return {
            "status": "invalid",
            "reason": "Invalid email format",
            "source": "mock"
        }
    
    # Mock results based on email domain
    common_providers = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]
    disposable_emails = ["tempmail.com", "throwaway.com", "fakeinbox.com"]
    
    domain = email.split("@")[-1].lower()
    
    if domain in common_providers:
        return {
            "status": "valid",
            "score": 85,
            "regexp": True,
            "gibberish": False,
            "disposable": False,
            "webmail": True,
            "mx_records": True,
            "smtp_server": True,
            "smtp_check": True,
            "accept_all": False,
            "source": "mock"
        }
    
    if domain in disposable_emails:
        return {
            "status": "invalid",
            "score": 0,
            "reason": "Disposable email domain",
            "source": "mock"
        }
    
    # Default: assume valid for unknown domains
    return {
        "status": "valid",
        "score": 70,
        "regexp": True,
        "gibberish": False,
        "disposable": False,
        "webmail": False,
        "mx_records": True,
        "smtp_server": True,
        "smtp_check": True,
        "accept_all": False,
        "source": "mock"
    }


async def find_email(first_name: str, last_name: str, company: str, domain: str = None) -> Optional[str]:
    """
    Find email using Hunter.io API (or mock)
    """
    if not settings.HUNTER_KEY:
        # Mock email finder
        domain = domain or f"{company.lower().replace(' ', '')}.com"
        return f"{first_name.lower()}.{last_name.lower()}@{domain}"
    
    try:
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.hunter.io/v2/email-finder",
                params={
                    "first_name": first_name,
                    "last_name": last_name,
                    "company": company,
                    "api_key": settings.HUNTER_KEY
                }
            )
            
            if response.status_code == 200:
                data = response.json().get("data", {})
                return data.get("email")
            return None
                
    except Exception as e:
        return None
