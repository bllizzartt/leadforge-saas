from typing import Dict, Any, Optional
from app.core.config import settings


class EnrichmentService:
    """
    Service for enriching leads with external data
    """
    
    async def enrich_lead(self, lead) -> Dict[str, Any]:
        """
        Enrich a lead with additional data
        """
        result = {}
        
        # Enrich with company data if company name exists
        if lead.company:
            company_data = await self.enrich_company(lead.company)
            if company_data:
                result.update(company_data)
        
        # Enrich with social data if LinkedIn URL exists
        if lead.linkedin_url:
            social_data = await self.enrich_social(lead.linkedin_url)
            if social_data:
                result.update(social_data)
        
        return result
    
    async def enrich_company(self, company_name: str) -> Optional[Dict[str, Any]]:
        """
        Enrich company data using Clearbit or mock
        """
        if not settings.CLEARBIT_KEY:
            return mock_company_enrichment(company_name)
        
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://company.clearbit.com/v2/companies/find",
                    params={"name": company_name},
                    headers={"Authorization": f"Bearer {settings.CLEARBIT_KEY}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "company_size": data.get("employees", ""),
                        "company_industry": data.get("industry", ""),
                        "company_revenue": data.get("estimatedRevenue", ""),
                        "company_url": data.get("domain", ""),
                        "enrichment_source": "clearbit"
                    }
                    
        except Exception as e:
            pass
        
        return mock_company_enrichment(company_name)
    
    async def enrich_social(self, linkedin_url: str) -> Optional[Dict[str, Any]]:
        """
        Enrich social profile data
        """
        # Mock implementation
        return {
            "linkedin_profile": linkedin_url,
            "social_enriched": True
        }


async def enrichment_service_enrich_lead(lead) -> Dict[str, Any]:
    """
    Standalone function to enrich a lead
    """
    service = EnrichmentService()
    return await service.enrich_lead(lead)


def mock_company_enrichment(company_name: str) -> Dict[str, Any]:
    """
    Mock company enrichment for development/testing
    """
    import random
    
    company_sizes = [
        "1-10 employees",
        "11-50 employees", 
        "51-200 employees",
        "201-500 employees",
        "501-1000 employees",
        "1001-5000 employees",
        "5001+ employees"
    ]
    
    industries = [
        "Technology",
        "Healthcare",
        "Finance",
        "Education",
        "Retail",
        "Manufacturing",
        "Services",
        "Media",
        "Real Estate",
        "Other"
    ]
    
    return {
        "company_size": random.choice(company_sizes),
        "company_industry": random.choice(industries),
        "company_revenue": f"${random.randint(1, 100)}M",
        "enrichment_source": "mock",
        "enriched_at": "2024-01-15T10:30:00Z"
    }


async def detect_tech_stack(company_domain: str) -> list:
    """
    Detect technology stack used by a company (mock)
    """
    if not settings.BUILTWITH_KEY:
        return mock_tech_stack()
    
    try:
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.builtwith.com/v2/api.json",
                params={"KEY": settings.BUILTWITH_KEY, "LOOKUP": company_domain}
            )
            
            if response.status_code == 200:
                data = response.json()
                # Parse technologies from response
                return extract_technologies(data)
                
    except Exception as e:
        pass
    
    return mock_tech_stack()


def mock_tech_stack() -> list:
    """
    Mock tech stack for development/testing
    """
    common_tech = [
        "React", "Vue.js", "Angular", "Node.js", "Python", "Django", 
        "Ruby on Rails", "PHP", "Laravel", "AWS", "Google Cloud", "Azure",
        "PostgreSQL", "MongoDB", "Redis", "Docker", "Kubernetes"
    ]
    
    import random
    return random.sample(common_tech, k=random.randint(2, 5))


def extract_technologies(data: dict) -> list:
    """
    Extract technologies from BuiltWith API response
    """
    technologies = []
    
    try:
        if "Results" in data:
            for result in data["Results"]:
                if "Paths" in result:
                    for path in result["Paths"]:
                        if "Technologies" in path:
                            for tech in path["Technologies"]:
                                technologies.append(tech.get("Name", ""))
    except Exception:
        pass
    
    return list(set(technologies))
