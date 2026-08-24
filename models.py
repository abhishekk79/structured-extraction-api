from typing import Literal, Optional
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
        default=None,
        description="Minimum base salary figure, in the pay period given by salary_period, if a salary is stated. Base salary only — exclude bonuses, commission, signing bonuses, or OTE (on-target earnings) figures.",
    )
    salary_max: Optional[int] = Field(
        default=None,
        description="Maximum base salary figure, in the pay period given by salary_period, if a salary is stated. Base salary only — exclude bonuses, commission, signing bonuses, or OTE (on-target earnings) figures.",
    )
    salary_period: Optional[Literal["hourly", "weekly", "project", "annual"]] = Field(
        default=None,
        description="The pay period the salary figures are stated in, if a salary is given. 'hourly' for rates like '$45/hour', 'weekly' for rates like '$2,000/week', 'project' for a flat one-time project fee, 'annual' for yearly salaries.",
    )
    currency: Optional[str] = Field(
        default=None,
        description="ISO 4217 currency code for the salary figures, if a salary is given, e.g. 'USD', 'EUR', 'INR'. Infer from currency symbols, country, or an explicit currency name if not labeled directly.",
    )
