# Archived tutor prompts

Old tutor prompts, kept so we can go back to them. They are **not** loaded by the app.

## physics_emmy_v1_scientific_method.md

The first version of Emmy (used until November 2026): a Socratic physics tutor
that guided students through a fixed five-stage scientific method (research
question, hypothesis, plan, data, analysis) with locked stage gates. It was
replaced by the two Nature of Science versions of Emmy
(`Emmy_prompt_exoplanet_lesson.txt` and `Emmy_prompt_any_experiment.txt`).

To bring it back, move the file back to `tutor_prompts/` and add this entry to
`TUTORS` in `modules/tutors.py`:

```python
"physics_emmy": {
    "kind": "socratic",
    "title": "Emmy (v1): Physics Research Tutor",
    "icon": "🔭",
    "description": (
        "A Socratic tutor for physics experiments. Emmy guides you through the "
        "scientific method for an experiment of your choice, one question at a "
        "time. She won't hand you answers, but you can always ask her for a hint."
    ),
    "prompt_file": "physics_emmy_v1_scientific_method.md",
    "greeting": (
        "**Stage 1/5: Research Question. Status: draft. Next: Hypothesis.**\n\n"
        "Hi, I'm Emmy, your scientific mentor. Whenever you're stuck, just ask "
        "me for help or a small hint; otherwise I'll keep nudging you with "
        "questions so you do the thinking. What physics experiment are you "
        "investigating?"
    ),
    "max_tokens": 800,
    "history_turns": 10,
},
```

Its full history is also in git (`git log --follow tutor_prompts/archive/physics_emmy_v1_scientific_method.md`).
