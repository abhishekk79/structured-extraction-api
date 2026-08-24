from typing import Optional
from pydantic import BaseModel, Field


class JobPosting(BaseModel):
    title: str = Field(description="The job title, e.g. 'Senior Backend Engineer'")
    seniority: str = Field(
        description="Seniority level, e.g. 'Junior', 'Mid', 'Senior', 'Staff', 'Lead'"
    )
    skills: list[str] = Field(
        description="List of required or nice-to-have technical skills, as short strings"
    )
    location: str = Field(description="The stated location or region for the role")
    remote: bool = Field(description="True if the role is remote, false otherwise")
    salary_min: Optional[int] = Field(
        default=None, description="Minimum salary in the stated currency, if given"
    )
    salary_max: Optional[int] = Field(
        default=None, description="Maximum salary in the stated currency, if given"
    )
