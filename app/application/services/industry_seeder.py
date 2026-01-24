"""
Industry Seeder Service

Service to seed default industries for a new tenant.
"""

from app.application.services.industry_seed_data import INDUSTRIES, IndustrySeedData
from app.application.use_cases.industry_use_cases import CreateIndustryUseCase
from app.domain.repositories.industry_repository import IndustryRepository
from app.domain.value_objects.core import IndustryId, TenantId
from app.shared.utils.generators import generate_cuid


async def seed_industries_for_tenant(
    tenant_id: TenantId,
    industry_repository: IndustryRepository,
) -> None:
    """
    Seed default industries for a new tenant.
    
    Creates all parent industries and their children in a hierarchical structure.
    If an industry already exists (by code), it will be skipped.
    
    Args:
        tenant_id: The tenant ID to create industries for
        industry_repository: The industry repository to use
    """
    create_use_case = CreateIndustryUseCase(industry_repository)
    
    # Track created parent industries by code for child creation
    parent_industry_map: dict[str, IndustryId] = {}
    
    for industry_data in INDUSTRIES:
        # Extract children before creating parent
        children = industry_data.get("children", [])
        parent_data: IndustrySeedData = {
            "name": industry_data["name"],
            "code": industry_data["code"],
            "description": industry_data["description"],
        }
        
        # Check if parent already exists by code
        existing_parent = await industry_repository.get_by_code(
            parent_data["code"], tenant_id
        )
        
        if existing_parent:
            # Use existing parent ID
            parent_id = existing_parent.id
        else:
            # Create parent industry
            parent_id = IndustryId(generate_cuid())
            await create_use_case.execute(
                industry_id=parent_id,
                tenant_id=tenant_id,
                name=parent_data["name"],
                description=parent_data.get("description"),
                code=parent_data.get("code"),
                parent_industry_id=None,
            )
        
        # Store parent ID for children
        parent_industry_map[parent_data["code"]] = parent_id
        
        # Create child industries
        if children:
            for child_data in children:
                # Check if child already exists by code
                existing_child = await industry_repository.get_by_code(
                    child_data["code"], tenant_id
                )
                
                if not existing_child:
                    child_id = IndustryId(generate_cuid())
                    await create_use_case.execute(
                        industry_id=child_id,
                        tenant_id=tenant_id,
                        name=child_data["name"],
                        description=child_data.get("description"),
                        code=child_data.get("code"),
                        parent_industry_id=parent_id,
                    )
