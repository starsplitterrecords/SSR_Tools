# 01_core/prompt/generator.py

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class PromptTemplate:
    name: str
    description: str
    template: str


class PromptGenerator:
    """
    Simple but flexible template-based prompt generator.
    """

    TEMPLATES = {
        "General Description": PromptTemplate(
            name="General Description",
            description="Describe the audio track",
            template=(
                "Write a detailed musical description of the track:\n"
                "- Alias: {alias}\n"
                "- Title: {title}\n"
                "- Visual Style: {style}\n"
                "- Notes: {notes}\n"
            )
        ),
    }

    @staticmethod
    def build_prompt(work_dict: Dict[str, Any], alias_dict: Dict[str, Any], template_name: str) -> str:
        tmpl = PromptGenerator.TEMPLATES[template_name]

        return tmpl.template.format(
            alias=alias_dict.get("display_name", alias_dict.get("codename")),
            title=work_dict.get("title", ""),
            style=alias_dict.get("visual_style", ""),
            notes=work_dict.get("notes", ""),
        )
