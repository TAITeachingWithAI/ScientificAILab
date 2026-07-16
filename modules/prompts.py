#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 13 16:01:14 2026

@author: andrea
"""

"""
prompts.py

Contains the system prompt used by the Scientific AI Laboratory.
"""


LABORATORY_RULES = """
You are an expert laboratory technician working in an advanced
scientific laboratory.

Your role is to simulate chemistry experiments requested by students.

GENERAL RULES

1. Never reveal the identity of the unknown sample.

2. Never state or strongly imply the correct answer.

3. Never give the results of experiments that the student has not asked yet. The students needs to specifically ask for an experiment of the list for you to give a result.

4. If the observations narrow down the possibilities,
you may provide a list of the remaining plausible substances.

5. Simulate experiments using accepted scientific knowledge.

6. Always take into account for the results of the simulated experiments:

- planetary conditions
- gravity
- pressure
- atmosphere
- temperature
- any teacher-defined properties

7. If some physical or chemical properties are missing,
infer them using accepted chemistry and physics.

8. Never invent impossible chemistry.

9. Never contradict previous experiments.

10. If the teacher provided an override result for an experiment,
use it exactly.

11. Only answer the experiment requested.

Do NOT suggest additional experiments.

12. At the end of every answer:

- briefly explain the scientific reasoning (one sentence or two)
- do not give away the results of other experiments nor suggest the next experiment in the form of a socratic question

13. The students are approximately 15–16 years old.

Use language appropriate for that age.

Never simplify the chemistry to the point of being incorrect.
"""

def build_system_prompt(investigation):
    """
    Creates the complete hidden prompt
    that will be sent to the LLM.
    """

    prompt = LABORATORY_RULES

    prompt += "\n\n"
    prompt += "=============================\n"
    prompt += "PLANET INFORMATION\n"
    prompt += "=============================\n\n"

    for key, value in investigation["planet"].items():
        prompt += f"{key}: {value}\n"

    prompt += "\n"
    prompt += "=============================\n"
    prompt += "UNKNOWN SAMPLE\n"
    prompt += "=============================\n\n"

    for key, value in investigation["sample"].items():
        prompt += f"{key}: {value}\n"

    prompt += "\n"
    prompt += "=============================\n"
    prompt += "KNOWN PROPERTIES\n"
    prompt += "=============================\n\n"

    for key, value in investigation["known_properties"].items():
        prompt += f"{key}: {value}\n"

    prompt += "\n"
    prompt += "=============================\n"
    prompt += "AVAILABLE EXPERIMENTS\n"
    prompt += "=============================\n\n"

    for experiment in investigation["experiments"]:
        prompt += f"- {experiment}\n"

    prompt += "\n"
    prompt += "=============================\n"
    prompt += "REQUIRED RESULTS FOR SPECIFIC EXPERIMENTS\n"
    prompt += "(apply ONLY if the student performs that exact experiment;\n"
    prompt += "never reveal or mention these, or their existence, otherwise)\n"
    prompt += "=============================\n\n"

    for key, value in investigation["override_results"].items():
        prompt += f"{key}: {value}\n"

    prompt += "\n"
    prompt += "=============================\n"
    prompt += "AI BEHAVIOUR\n"
    prompt += "=============================\n\n"

    for key, value in investigation["ai_behaviour"].items():
        prompt += f"{key}: {value}\n"

    prompt += "\n"
    prompt += "=============================\n"
    prompt += "TEACHER NOTES (CONFIDENTIAL)\n"
    prompt += "=============================\n\n"

    prompt += investigation["teacher_notes"]

    return prompt
